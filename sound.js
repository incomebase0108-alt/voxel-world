// ===================================================================
// サウンドシステム（WebAudio・本体コードと疎結合）  ── 2号機 / 音響担当
//   ・index.html 側は window.playSFX('name', opts?) を呼ぶだけ（未読込でも壊れない）
//   ・既存トリガー window.onThunderSound / window.onPlayerHurt もここで実装
//   ・素材は仮の合成音。後で音声ファイル再生に差し替え可能
//   ・音量は master / sfx / bgm の3バス構成（④設定の受け渡し口 window.SoundSettings）
// ===================================================================
(function () {
  let ctx = null, master = null, sfxBus = null, bgmBus = null, ambBus = null;

  // ④ 音量状態（0..1）。UI見た目は3号機、ここは値の受け渡し口のみ。
  const vol = { master: 1.0, sfx: 1.0, bgm: 0.75, amb: 0.5, muted: false };

  // 個別SE音量の微調整（0..4 の倍率、既定1.0）。例:「足音うるさい」→ gains.footstep=0.5
  //   window.SoundSettings.setGain('footstep', 0.5) で即変更可。playSFX 経由の音に乗る。
  const gains = {
    footstep: 1, jump: 1, land: 1, break: 1, place: 1, eat: 1, pickup: 1, craft: 1,
    splash: 1, swim: 1, attack: 1, hit: 1, hurt: 1, thunder: 1, mob: 1,
    whiff: 1, charge_start: 1, charge_full: 1, levelup: 1,
  };
  let curMul = 1; // 再生中SEの倍率（tone/noise が参照。playSFX が設定）

  function ac() {
    if (!ctx) {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return null;
      ctx = new AC();
      // バス構成： source → (sfxBus|bgmBus) → master → destination
      master = ctx.createGain();
      sfxBus = ctx.createGain();
      bgmBus = ctx.createGain();
      ambBus = ctx.createGain(); // ① 環境音アンビエンス（BGMの下）
      sfxBus.connect(master); bgmBus.connect(master); ambBus.connect(master); master.connect(ctx.destination);
      applyVolumes();
    }
    if (ctx.state === 'suspended') ctx.resume(); // ユーザー操作起点で再開
    return ctx;
  }
  function applyVolumes() {
    if (!master) return;
    const m = vol.muted ? 0 : vol.master;
    master.gain.value = m;
    sfxBus.gain.value = vol.sfx;
    bgmBus.gain.value = vol.bgm;
    if (ambBus) ambBus.gain.value = vol.amb;
  }

  // 単音（周波数スライド可）
  function tone(freq, dur, type, gain, slideTo, dest, at) {
    const c = ac(); if (!c) return;
    const t = c.currentTime + (at || 0), o = c.createOscillator(), g = c.createGain(); // at=発音オフセット秒（アルペジオ用）
    o.type = type || 'sine';
    o.frequency.setValueAtTime(freq, t);
    if (slideTo) o.frequency.exponentialRampToValueAtTime(Math.max(1, slideTo), t + dur);
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime((gain || 0.2) * curMul, t + 0.01);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g).connect(dest || sfxBus);
    o.start(t); o.stop(t + dur + 0.02);
  }
  // ノイズ（破裂音・雷・打撃・足音用）
  function noise(dur, gain, filterFreq, type, dest) {
    const c = ac(); if (!c) return;
    const t = c.currentTime, n = Math.floor(c.sampleRate * dur);
    const buf = c.createBuffer(1, n, c.sampleRate), d = buf.getChannelData(0);
    for (let i = 0; i < n; i++) d[i] = Math.random() * 2 - 1;
    const src = c.createBufferSource(); src.buffer = buf;
    const g = c.createGain(); g.gain.setValueAtTime((gain || 0.2) * curMul, t); g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    const f = c.createBiquadFilter(); f.type = type || 'lowpass'; f.frequency.value = filterFreq || 1000;
    src.connect(f).connect(g).connect(dest || sfxBus);
    src.start(t); src.stop(t + dur);
  }
  const clamp01 = (v) => Math.max(0, Math.min(1, v));

  // ── 素材別パラメータ（足音・破壊・設置で材質感を出す）─────────────
  // block 名は1号機コア側の地表/ブロック種に合わせる。未知名は default。
  const MAT = {
    grass:     { ff: 450,  g: 0.07, type: 'lowpass' },
    dirt:      { ff: 380,  g: 0.08, type: 'lowpass' },
    sand:      { ff: 700,  g: 0.06, type: 'bandpass' },
    stone:     { ff: 1500, g: 0.09, type: 'highpass' },
    stonebrick:{ ff: 1400, g: 0.09, type: 'highpass' },
    planks:    { ff: 900,  g: 0.08, type: 'bandpass' },
    glass:     { ff: 2600, g: 0.07, type: 'highpass' },
    water:     { ff: 600,  g: 0.06, type: 'lowpass' },
    default:   { ff: 800,  g: 0.08, type: 'lowpass' },
  };
  const mat = (b) => MAT[b] || MAT.default;

  // ── モブ鳴き声（type 別）。短い合成音で個性を付ける ────────────────
  function mobCry(type, vmul, dest) {
    const v = vmul || 1, d = dest || null; // dest 指定で 3D パンナー経由（③）。null は sfxBus
    switch (type) {
      case 'cow':      tone(140, 0.45, 'sawtooth', 0.10 * v, 110, d); break;
      case 'sheep':    tone(330, 0.30, 'sawtooth', 0.09 * v, 300, d); tone(360, 0.18, 'sawtooth', 0.06 * v, 320, d); break;
      case 'chicken':  tone(900, 0.06, 'square', 0.07 * v, 1200, d); tone(1100, 0.05, 'square', 0.06 * v, 800, d); break;
      case 'pig':      tone(220, 0.18, 'sawtooth', 0.10 * v, 160, d); noise(0.10, 0.05 * v, 700, 'lowpass', d); break;
      case 'horse':    tone(420, 0.35, 'sawtooth', 0.10 * v, 180, d); noise(0.15, 0.05 * v, 900, 'lowpass', d); break;
      case 'villager': tone(260, 0.22, 'sine', 0.09 * v, 230, d); break;
      case 'slime':    noise(0.18, 0.10 * v, 500, 'lowpass', d); break;
      case 'zombie':   tone(120, 0.5, 'sawtooth', 0.10 * v, 90, d); noise(0.3, 0.05 * v, 400, 'lowpass', d); break;
      case 'skeleton': for (let i = 0; i < 4; i++) noise(0.04, 0.07 * v, 2500, 'bandpass', d); break; // カタカタ
      case 'golem':    tone(70, 0.6, 'sine', 0.14 * v, 50, d); noise(0.4, 0.08 * v, 200, 'lowpass', d); break;
      default:         tone(300, 0.2, 'sine', 0.08 * v, 280, d);
    }
  }

  // ── 効果音テーブル（仮の合成音。opts で材質/落下量/モブ種/音量を受ける）──
  const SFX = {
    // 既存9音（品質を少し調整）
    thunder() { noise(0.6, 0.5, 500); tone(64, 0.5, 'sine', 0.4, 40); },
    hurt()    { tone(200, 0.18, 'square', 0.22, 120); noise(0.06, 0.10, 1200); },
    attack()  { tone(180, 0.07, 'square', 0.18, 90); noise(0.05, 0.08, 2200); },
    hit()     { noise(0.08, 0.16, 1600); tone(160, 0.05, 'square', 0.10, 100); },
    pickup()  { tone(660, 0.08, 'sine', 0.16, 990); tone(990, 0.06, 'sine', 0.10, 1320); },
    eat()     { tone(300, 0.12, 'sine', 0.14, 360); noise(0.05, 0.04, 600); },
    jump()    { tone(330, 0.09, 'sine', 0.10, 520); },
    // 種類別対応：break/place は opts.block で材質感を変える（未指定は default）
    break(o)  { const m = mat(o && o.block); noise(0.14, m.g * 1.8, m.ff, m.type); tone(m.ff / 6, 0.08, 'square', 0.06, m.ff / 10); },
    place(o)  { const m = mat(o && o.block); tone(m.ff / 4, 0.06, 'sine', 0.12, m.ff / 6); noise(0.05, m.g, m.ff, m.type); },

    // 新規（フックを1号機へ依頼）
    footstep(o) { const m = mat(o && o.block); noise(0.06, m.g, m.ff, m.type); },     // 地表ブロック別
    land(o)     { const f = clamp01((o && o.fall ? o.fall : 2) / 12);                  // 落下量で強さ
                  noise(0.12, 0.10 + 0.22 * f, 300 + 200 * f, 'lowpass'); tone(110, 0.10, 'sine', 0.08 + 0.1 * f, 70); },
    craft()     { tone(523, 0.07, 'square', 0.10, 523); tone(659, 0.07, 'square', 0.10, 659); noise(0.05, 0.06, 1800); }, // 工作音
    splash()    { noise(0.25, 0.18, 900, 'lowpass'); tone(500, 0.2, 'sine', 0.08, 200); },  // 入水
    swim()      { noise(0.22, 0.035, 420, 'lowpass'); },                                    // 水中移動（やわらかく）
    mob(o)      { if (o && o.x != null) playMobSpatial(o); else mobCry(o && o.type, o && o.vol); }, // モブ鳴き(座標あれば3D)
    // 攻撃アクション（空振り・溜め）
    whiff()       { noise(0.18, 0.06, 1200, 'bandpass'); },                                          // 空振り（風切り）
    charge_start(){ tone(160, 0.25, 'sawtooth', 0.07, 320); },                                       // 溜め開始（上昇）
    charge_full() { tone(880, 0.10, 'sine', 0.10, 1320); tone(1320, 0.08, 'sine', 0.07, 1760); },    // 溜め完了（チャイム）
    // レベルアップ（1号機の playSFX('levelup') 連携）：上昇アルペジオ＋締めのきらめき
    levelup() {
      const seq = [523.25, 659.25, 783.99, 1046.50]; // C5-E5-G5-C6
      seq.forEach((f, i) => tone(f, 0.20, 'square', 0.12, f, null, i * 0.09));
      tone(1318.51, 0.30, 'sine', 0.10, 1568.00, null, 0.40); // 締め(E6→G6きらめき)
    },
  };

  // 公開API：playSFX(name, opts) ── opts は省略可（後方互換）
  window.playSFX = (name, opts) => {
    const prev = curMul;
    try { curMul = prev * (gains[name] != null ? gains[name] : 1); (SFX[name] || (() => {}))(opts); }
    catch (e) {} finally { curMul = prev; }
    maybeAutoStartMusic(); // SFXが鳴る＝ユーザー操作＆ctx稼働。BGM未起動なら確実に起動（window listener非依存）
    ensureScheduler();     // 万一ノート生成ループが死んでいたら自己回復（SFXのたびに健全性を担保）
    if (bgmOn) startAmbience(); // 環境音も起動を担保
  };

  // 既存トリガーをサウンドに接続
  window.onThunderSound = () => window.playSFX('thunder');
  window.onPlayerHurt   = () => window.playSFX('hurt');

  // === 攻撃アクション連携（防御的: 1号機が口を呼ぶだけ・未呼出なら無音待機）=====
  //   window.onAttackHit(weapon, isCrit) … weapon: 'sword'|'axe'|'bow'|'fist'
  //   window.onAttackWhiff() … 空振り / window.onAttackCharge('start'|'full') … 溜め
  function weaponHit(weapon, isCrit) {
    const v = isCrit ? 1.5 : 1;
    switch (weapon) {
      case 'sword': noise(0.06, 0.10 * v, 4000, 'highpass'); tone(700, 0.10, 'square', 0.10 * v, 1100); break; // 斬撃＋金属音
      case 'axe':   noise(0.12, 0.16 * v, 700, 'lowpass'); tone(120, 0.10, 'square', 0.14 * v, 70); break;     // 重い打撃
      case 'bow':   window.playSFX('hit'); break;                                                              // 命中（既存音）
      case 'fist':  noise(0.07, 0.12 * v, 900, 'lowpass'); tone(160, 0.06, 'sine', 0.10 * v, 110); break;      // パンチ
      default:      window.playSFX('hit');
    }
    if (isCrit) { tone(1400, 0.12, 'square', 0.12, 2000); tone(1900, 0.10, 'sine', 0.08, 2400); }              // クリティカル強調
  }
  window.onAttackHit    = (weapon, isCrit) => {
    const prev = curMul;
    try { curMul = prev * (gains.attack != null ? gains.attack : 1); weaponHit(weapon, !!isCrit); }
    catch (e) {} finally { curMul = prev; }
  };
  window.onAttackWhiff  = () => window.playSFX('whiff');
  window.onAttackCharge = (phase) => window.playSFX(phase === 'full' ? 'charge_full' : 'charge_start');

  // === ② BGMシステム（合成音・bgmBus経由・状況でレイヤー切替＋クロスフェード）===
  //   ・コアは window.setMusicScene('day'|'night'|'combat'|'water') を呼ぶだけ
  //   ・最初のユーザー操作で 'day' を自動開始（startMusic/stopMusic で明示制御も可）
  //   ・素材は合成音。後で音楽ファイル(loop)再生に差し替え可能
  const XFADE = 1.8; // シーン間クロスフェード秒
  const BGM_RICH = 'v2-layer+xfade(2026-06-03)'; // ②BGMリッチ化の版。実機H診断(getSoundDiag)で「どのビルドにBGMが入ったか」を追える
  // level = シーン間の音量バランス（0..1.2程度）。water は静かだが「水中だと分かる」程度に。
  // 多層化パラメータ（②BGMリッチ化・2026-06-03）：bassG=サブベース土台量 / shimmer=高域の艶 /
  //   bassline=低音の鼓動(scheduler) / tremHz・tremDepth=パッドの呼吸(揺らぎ)。既存フィールドは不変＝後方互換。
  const SCENES = {
    day:    { tempo: 104, scale: [220.00, 246.94, 277.18, 329.63, 369.99], pad: [110.00, 164.81, 220.00], wave: 'triangle', density: 0.55, drums: false, level: 1.0, bassG: 0.05,  shimmer: true,  bassline: true,  tremHz: 0.13, tremDepth: 0.12 },
    night:  { tempo: 76,  scale: [164.81, 196.00, 220.00, 261.63, 293.66], pad: [123.47, 164.81, 220.00], wave: 'sine',     density: 0.42, drums: false, level: 0.9, bassG: 0.045, shimmer: true,  bassline: false, tremHz: 0.09, tremDepth: 0.14 },
    combat: { tempo: 148, scale: [146.83, 174.61, 196.00, 220.00, 261.63], pad: [110.00, 146.83, 220.00], wave: 'sawtooth', density: 0.85, drums: true,  level: 1.0, bassG: 0.07,  shimmer: false, bassline: true,  tremHz: 0.6,  tremDepth: 0.10 },
    water:  { tempo: 58,  scale: [261.63, 311.13, 349.23, 392.00, 466.16], pad: [130.81, 196.00, 261.63], wave: 'sine',     density: 0.26, drums: false, level: 0.6, bassG: 0.035, shimmer: true,  bassline: false, tremHz: 0.07, tremDepth: 0.16 },
  };
  let bgmOn = false, bgmScene = null, bgmTimer = null, nextNoteT = 0, beat = 0, userMusicCtl = false, lastNoteTime = 0;
  let xfadeUntil = 0; // クロスフェード進行中の終了時刻（この間はscheduler の stuck回復ガードを抑止＝自動化の衝突回避）
  const sceneNodes = {}; // name -> { gain, layer, pad:[{o}] }

  function sceneGain(name) {
    if (!sceneNodes[name]) {
      const g = ac().createGain(); g.gain.value = 0.0001; g.connect(bgmBus);
      sceneNodes[name] = { gain: g, pad: [] };
    }
    return sceneNodes[name];
  }
  // pad は各シーン常駐（停止/再生成しない＝停止タイマー競合を原理的に排除）。
  // 非アクティブ時は scene gain を 0 にして黙らせるだけ。
  function startPad(name) {
    const c = ac(); if (!c) return;
    const node = sceneGain(name);
    if (node.pad.length) return; // 既に常駐済みなら二重生成しない（クロスフェードでは再生成せず＝ノードリーク無し）
    const sc = SCENES[name];
    // 多層化①: 呼吸（tremolo）レイヤー。pad/sub/shimmer をまとめて通し、ゆっくり揺らして生命感を出す。
    //   layerGain.gain は crossfade が触る scene gain (node.gain.gain) とは別 AudioParam なので LFO と干渉しない。
    const layerGain = c.createGain(); layerGain.gain.value = 1.0; layerGain.connect(node.gain);
    const lfo = c.createOscillator(); lfo.type = 'sine'; lfo.frequency.value = sc.tremHz || 0.12;
    const lfoDepth = c.createGain(); lfoDepth.gain.value = sc.tremDepth || 0.12;
    lfo.connect(lfoDepth).connect(layerGain.gain); lfo.start(); // LFO→深さ→layerGainのAudioParamへ加算（1.0を中心に揺れる）
    node.layer = layerGain; node.pad.push({ o: lfo });
    // 多層化②: 和音パッド（既存・微デチューンで厚み）。呼吸レイヤー経由で接続。
    sc.pad.forEach((f, i) => {
      const o = c.createOscillator(), g = c.createGain();
      o.type = name === 'combat' ? 'sawtooth' : 'sine';
      o.frequency.value = f * (1 + (i - 1) * 0.003);
      g.gain.value = 0.09;
      o.connect(g).connect(layerGain); o.start();
      node.pad.push({ o });
    });
    // 多層化③: サブベース・ドローン（根音の1オクターブ下）で土台の厚みを足す。
    {
      const o = c.createOscillator(), g = c.createGain();
      o.type = 'sine'; o.frequency.value = sc.pad[0] / 2;
      g.gain.value = sc.bassG || 0.05;
      o.connect(g).connect(layerGain); o.start();
      node.pad.push({ o });
    }
    // 多層化④: シマー（根音の1オクターブ上をごく弱く）で上の艶。combat は密度過多なので省略。
    if (sc.shimmer) {
      const o = c.createOscillator(), g = c.createGain();
      o.type = 'triangle'; o.frequency.value = sc.pad[0] * 2 * (1 + 0.004);
      g.gain.value = 0.022;
      o.connect(g).connect(layerGain); o.start();
      node.pad.push({ o });
    }
  }
  function stopPad(name) {
    const node = sceneNodes[name]; if (!node) return;
    node.pad.forEach(({ o }) => { try { o.stop(); } catch (e) {} }); // LFO含む全オシレータを停止
    node.pad = [];
    if (node.layer) { try { node.layer.disconnect(); } catch (e) {} node.layer = null; } // 呼吸レイヤーも撤去（次回startPadで再生成＝二重接続/リーク防止）
  }
  function bgmNote(freq, dur, dest, gain, wave) {
    const c = ac(); if (!c) return;
    const t = c.currentTime, o = c.createOscillator(), g = c.createGain();
    lastNoteTime = t; // 診断：直近のノート発音時刻
    o.type = wave || 'sine'; o.frequency.value = freq;
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(gain || 0.07, t + 0.02);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g).connect(dest); o.start(t); o.stop(t + dur + 0.02);
  }
  function kick(dest) {
    const c = ac(); if (!c) return;
    const t = c.currentTime, o = c.createOscillator(), g = c.createGain();
    o.type = 'sine'; o.frequency.setValueAtTime(140, t); o.frequency.exponentialRampToValueAtTime(50, t + 0.12);
    g.gain.setValueAtTime(0.16, t); g.gain.exponentialRampToValueAtTime(0.0001, t + 0.16);
    o.connect(g).connect(dest); o.start(t); o.stop(t + 0.18);
  }
  // 多層化: 低音の鼓動（bassline）。サブベース・ドローンの上に乗る短い拍動で前進感を出す。
  function bgmBass(freq, dur, dest, gain) {
    const c = ac(); if (!c) return;
    const t = c.currentTime, o = c.createOscillator(), g = c.createGain();
    o.type = 'triangle'; o.frequency.value = freq;
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(gain || 0.06, t + 0.03);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g).connect(dest); o.start(t); o.stop(t + dur + 0.02);
  }
  // ノート生成ループ。例外が出ても・遅れても「絶対に止まらない」設計。
  function scheduler() {
    bgmTimer = null;
    if (!bgmOn) return; // 明示停止時のみ終了（再武装しない）
    try {
      const c = ac();
      if (c && bgmScene && SCENES[bgmScene]) {
        const sc = SCENES[bgmScene], node = sceneGain(bgmScene), spb = 60 / sc.tempo / 2; // 8分音符
        const lvl = sc.level || 1, gp = node.gain.gain; // node.gain=GainNode本体 / .gain.gain=AudioParam
        // アクティブscene gainを必ずlevelへ駆動（stuck/0張り付き防止）。ただしクロスフェード中は抑止
        //   ＝意図的な equal-power カーブと setTargetAtTime の自動化衝突を避ける。
        if (c.currentTime > xfadeUntil && gp.value < lvl - 0.02) gp.setTargetAtTime(lvl, c.currentTime, 0.25);
        if (nextNoteT < c.currentTime) nextNoteT = c.currentTime; // 背景化等で遅れたら追従（大量生成・例外を防止）
        let guard = 0; // 暴走ガード
        while (nextNoteT < c.currentTime + 0.2 && guard++ < 64) {
          if (Math.random() < sc.density) {
            const f = sc.scale[(Math.random() * sc.scale.length) | 0] * (Math.random() < 0.3 ? 2 : 1);
            bgmNote(f, spb * (Math.random() < 0.5 ? 1.6 : 0.9), node.gain, 0.12, sc.wave);
          }
          if (sc.drums && beat % 2 === 0) kick(node.gain);
          if (sc.bassline && beat % 4 === 0) bgmBass(sc.scale[0] / 2, spb * 1.8, node.gain, (sc.bassG || 0.05) * 1.2); // 低音の鼓動（2拍ごと）
          nextNoteT += spb; beat++;
        }
      }
    } catch (e) { /* 例外でループを殺さない */ }
    if (bgmOn) bgmTimer = setTimeout(scheduler, 60); // 生きている限り必ず再武装
  }
  // 死んでいたら復活させる自己回復（scene切替・playSFX・タブ復帰から呼ぶ）
  function ensureScheduler() {
    if (bgmOn && !bgmTimer) {
      const c = ac(); if (c && nextNoteT < c.currentTime) nextNoteT = c.currentTime;
      scheduler();
    }
  }
  // シーン gain のフェード。shape='in'|'out' を渡すと equal-power カーブ（sin/cos）でクロスの中央ディップを解消。
  //   省略時は従来の線形ramp（後方互換）。sceneNodes[name].gain は GainNode本体、AudioParam は .gain.gain。
  function fadeSceneGain(name, to, shape) {
    const c = ac(), g = sceneGain(name).gain.gain;
    g.cancelScheduledValues(c.currentTime);
    const from = Math.max(0.0001, g.value), target = Math.max(0.0001, to);
    xfadeUntil = c.currentTime + XFADE; // この区間は scheduler の stuck回復ガードを止める
    try {
      if (shape === 'in' || shape === 'out') {
        const N = 24, arr = new Float32Array(N);
        for (let i = 0; i < N; i++) {
          const x = i / (N - 1);
          const k = shape === 'in' ? Math.sin(x * Math.PI / 2) : Math.cos(x * Math.PI / 2); // 等パワー曲線
          arr[i] = Math.max(0.0001, from + (target - from) * k);
        }
        g.setValueCurveAtTime(arr, c.currentTime, XFADE);
        g.setValueAtTime(target, c.currentTime + XFADE + 0.02); // カーブ後に終端値を固定
      } else {
        g.setValueAtTime(from, c.currentTime);
        g.linearRampToValueAtTime(target, c.currentTime + XFADE);
      }
    } catch (e) {
      // setValueCurveAtTime の重複自動化等で失敗したら線形へフォールバック（無音事故を防ぐ）
      try { g.cancelScheduledValues(c.currentTime); g.setValueAtTime(from, c.currentTime); g.linearRampToValueAtTime(target, c.currentTime + XFADE); } catch (e2) {}
    }
  }
  function startMusic(scene) {
    userMusicCtl = true;
    const c = ac(); if (!c) return;
    const s = SCENES[scene] ? scene : (bgmScene || 'day');
    if (!bgmOn) {
      bgmOn = true; nextNoteT = c.currentTime + 0.1; beat = 0;
      bgmScene = s; startPad(s); fadeSceneGain(s, SCENES[s].level || 1, 'in');
      scheduler(); startAmbience();
      try { console.info('[sound] BGM開始 scene=' + s + ' / rich=' + BGM_RICH + ' / bgmBus=' + (bgmBus ? bgmBus.gain.value.toFixed(2) : '?') + ' / ctx=' + (ctx ? ctx.state : '?')); } catch (e) {}
    } else {
      setMusicScene(s);
    }
  }
  // 明示制御もユーザー操作も無い場合に既定 'day' を起動（playSFX/ジェスチャから呼ぶ）
  function maybeAutoStartMusic() { if (!userMusicCtl && !bgmOn) startMusic('day'); }
  function setMusicScene(name) {
    window.__setMusicSceneCalled = true; // 診断：コアがシーン口を呼んだか
    if (!SCENES[name] || !ac()) return;
    if (!bgmOn) { startMusic(name); return; }
    if (name === bgmScene) return;
    const prev = bgmScene; bgmScene = name;
    startPad(name); fadeSceneGain(name, SCENES[name].level || 1, 'in'); // 等パワーで入れる
    if (prev && sceneNodes[prev]) fadeSceneGain(prev, 0, 'out'); // 等パワーで抜く。oscillatorは止めずgainのみ（競合回避）
    ensureScheduler(); // シーン切替時にループが死んでいたら必ず復活
  }
  function stopMusic() {
    userMusicCtl = true; bgmOn = false;
    if (bgmTimer) { clearTimeout(bgmTimer); bgmTimer = null; }
    Object.keys(sceneNodes).forEach((n) => { try { stopPad(n); sceneNodes[n].gain.gain.value = 0.0001; } catch (e) {} });
    bgmScene = null;
  }
  window.startMusic = startMusic;
  window.stopMusic = stopMusic;
  window.setMusicScene = setMusicScene;
  // 最初のユーザー操作で自動的に 'day' を開始（コアが明示制御したら抑止）
  // capture段で拾うので、コアが bubble段で stopPropagation しても発火する
  function autoStartMusic() { maybeAutoStartMusic(); }
  window.addEventListener('pointerdown', autoStartMusic, { once: true, capture: true });
  window.addEventListener('keydown', autoStartMusic, { once: true, capture: true });
  // タブ復帰時（背景化でsetTimeoutが止まった後）にループを復活
  try { document.addEventListener('visibilitychange', () => { if (!document.hidden) ensureScheduler(); }); } catch (e) {}

  // === ③ 3D空間音響（PannerNode・防御的: 口が無ければ黙って無効化）===========
  //   ・コアが window.getMobPositions() / window.getPlayerPose() を実装したら自動有効化
  //   ・未定義でもエラーを投げず空動作（事故ゼロ）。push型 playSFX('mob',{type,x,y,z}) も対応
  let spatialTimer = null;
  function setPannerPos(p, x, y, z) {
    if (p.positionX) { p.positionX.value = x || 0; p.positionY.value = y || 0; p.positionZ.value = z || 0; }
    else if (p.setPosition) { p.setPosition(x || 0, y || 0, z || 0); }
  }
  function makePanner(x, y, z) {
    const c = ac(); if (!c) return null;
    const p = c.createPanner();
    p.panningModel = 'equalpower'; p.distanceModel = 'inverse'; // equalpower=軽量
    p.refDistance = 4; p.maxDistance = 40; p.rolloffFactor = 1;
    setPannerPos(p, x, y, z); p.connect(sfxBus);
    return p;
  }
  function playMobSpatial(o) {
    const p = makePanner(o.x, o.y, o.z);
    if (!p) { mobCry(o.type, o.vol); return; }      // 失敗時は非空間で鳴らす（フォールバック）
    mobCry(o.type, o.vol, p);
    setTimeout(() => { try { p.disconnect(); } catch (e) {} }, 1800);
  }
  function updateListener(pose) {
    const c = ac(); if (!c || !pose) return;
    const L = c.listener;
    if (L.positionX) { L.positionX.value = pose.x || 0; L.positionY.value = pose.y || 0; L.positionZ.value = pose.z || 0; }
    else if (L.setPosition) { L.setPosition(pose.x || 0, pose.y || 0, pose.z || 0); }
    const yaw = pose.yaw || 0, fx = Math.sin(yaw), fz = -Math.cos(yaw); // 正面-Z基準（アバターと同基準）
    if (L.forwardX) { L.forwardX.value = fx; L.forwardY.value = 0; L.forwardZ.value = fz; L.upX.value = 0; L.upY.value = 1; L.upZ.value = 0; }
    else if (L.setOrientation) { L.setOrientation(fx, 0, fz, 0, 1, 0); }
  }
  // 環境鳴き：口があれば周囲モブの位置から距離減衰つきで散発的に鳴らす
  function spatialTick() {
    try {
      if (ac()) {
        const poseFn = window.getPlayerPose, mobFn = window.getMobPositions;
        const pose = (typeof poseFn === 'function' && poseFn()) || null;
        if (pose) updateListener(pose);
        if (typeof mobFn === 'function') {
          const list = mobFn() || [], p = pose || { x: 0, y: 0, z: 0 };
          for (let i = 0; i < list.length; i++) {
            const m = list[i]; if (!m) continue;
            const dx = m.x - p.x, dy = (m.y || 0) - (p.y || 0), dz = m.z - p.z;
            const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
            if (dist > 36) continue;
            if (Math.random() < 0.045 * (1 - dist / 36)) { // 近いほど鳴きやすい・低頻度
              window.playSFX('mob', { type: m.type, x: m.x, y: m.y || 0, z: m.z, vol: 0.9 });
            }
          }
        }
      }
    } catch (e) { /* 口未実装・想定外は黙って無視（防御） */ }
    spatialTimer = setTimeout(spatialTick, 700);
  }
  function startSpatial() { if (!spatialTimer) spatialTick(); }
  window.addEventListener('pointerdown', startSpatial, { once: true, capture: true });
  window.addEventListener('keydown', startSpatial, { once: true, capture: true });

  // === ① 環境音アンビエンス（ambバス・BGMの下・防御的: biome口優先/無ければsceneで代替）===
  //   ・連続音の「寝床(bed)」=ループノイズ→bandpass で 風/波/吹雪/こもり を表現
  //   ・単発音(bird/cricket/drip/murmur)を散発スケジュール。biome で切替
  const AMB = {
    plains:  { f: 520,  q: 0.7, g: 0.05, chirp: { type: 'bird',    rate: 0.5 } },
    desert:  { f: 950,  q: 0.4, g: 0.06, chirp: null },
    snow:    { f: 1500, q: 0.3, g: 0.07, chirp: null },
    ocean:   { f: 320,  q: 0.9, g: 0.07, chirp: null },
    water:   { f: 220,  q: 1.4, g: 0.08, chirp: null },                          // 水中こもり
    cave:    { f: 130,  q: 1.6, g: 0.05, chirp: { type: 'drip',    rate: 0.3 } },
    night:   { f: 620,  q: 0.6, g: 0.035, chirp: { type: 'cricket', rate: 0.7 } },
    village: { f: 500,  q: 0.5, g: 0.045, chirp: { type: 'murmur',  rate: 0.45 } },
  };
  let ambBed = null, ambFilter = null, ambBedGain = null, ambType = null, ambTimer = null;
  function startAmbienceBed() {
    const c = ac(); if (!c || ambBed) return;
    const n = Math.floor(c.sampleRate * 2), buf = c.createBuffer(1, n, c.sampleRate), d = buf.getChannelData(0);
    let last = 0; for (let i = 0; i < n; i++) { const w = Math.random() * 2 - 1; last = (last + 0.02 * w) / 1.02; d[i] = last; } // ピンクっぽい
    ambBed = c.createBufferSource(); ambBed.buffer = buf; ambBed.loop = true;
    ambFilter = c.createBiquadFilter(); ambFilter.type = 'bandpass'; ambFilter.frequency.value = 520; ambFilter.Q.value = 0.7;
    ambBedGain = c.createGain(); ambBedGain.gain.value = 0.0001;
    ambBed.connect(ambFilter).connect(ambBedGain).connect(ambBus);
    ambBed.start();
  }
  function currentAmbience() {
    try { if (typeof window.getBiome === 'function') { const b = window.getBiome(); if (b && AMB[b]) return b; } } catch (e) {}
    if (bgmScene === 'water') return 'ocean';   // 代替: シーンから推定
    if (bgmScene === 'night') return 'night';
    return 'plains';
  }
  function ambChirp(kind) {
    switch (kind) {
      case 'bird':    tone(2200 + Math.random() * 800, 0.08, 'sine', 0.05, 2600, ambBus); break;
      case 'cricket': for (let i = 0; i < 3; i++) tone(4000, 0.02, 'square', 0.02, 4000, ambBus, i * 0.03); break;
      case 'drip':    tone(900, 0.05, 'sine', 0.05, 300, ambBus); break;
      case 'murmur':  tone(170 + Math.random() * 60, 0.18, 'sawtooth', 0.03, 150, ambBus); break;
    }
  }
  function ambScheduler() {
    ambTimer = null;
    try {
      const c = ac();
      if (c) {
        const t = currentAmbience(), cfg = AMB[t] || AMB.plains;
        if (t !== ambType) { // 切替時に寝床のフィルタ/音量をクロスで変える
          ambType = t;
          if (ambFilter) { ambFilter.frequency.setTargetAtTime(cfg.f, c.currentTime, 0.6); ambFilter.Q.value = cfg.q; }
          if (ambBedGain) ambBedGain.gain.setTargetAtTime(cfg.g, c.currentTime, 0.8);
        }
        if (cfg.chirp && Math.random() < cfg.chirp.rate * 0.25) ambChirp(cfg.chirp.type);
      }
    } catch (e) { /* 口未実装・想定外は黙って無視 */ }
    ambTimer = setTimeout(ambScheduler, 250);
  }
  function startAmbience() { startAmbienceBed(); if (!ambTimer) ambScheduler(); }

  // ④ サウンド設定の受け渡し口（UIは3号機。ここは値とロジックのみ）
  //   get() → {master,sfx,bgm,muted} / set(key,value) / setMuted(bool)
  const clampGain = (v) => Math.max(0, Math.min(4, Number(v))); // 個別倍率は 0..4
  function emitChange() { try { window.dispatchEvent(new CustomEvent('soundsettingschange', { detail: window.SoundSettings.get() })); } catch (e) {} }
  window.SoundSettings = {
    get: () => ({ master: vol.master, sfx: vol.sfx, bgm: vol.bgm, amb: vol.amb, muted: vol.muted, gains: Object.assign({}, gains) }),
    set: (key, value) => {
      if (key === 'muted') { vol.muted = !!value; }
      else if (key in vol) { vol[key] = clamp01(Number(value)); }
      applyVolumes(); saveVol(); emitChange();
    },
    setMuted: (b) => window.SoundSettings.set('muted', b),
    // 個別SEの音量倍率（例:「足音うるさい」→ setGain('footstep', 0.5)）
    getGains: () => Object.assign({}, gains),
    getGain: (name) => (gains[name] != null ? gains[name] : 1),
    setGain: (name, mult) => { if (name in gains) { gains[name] = clampGain(mult); saveVol(); emitChange(); } },
  };

  // 3号機UI(UI_INTEGRATION.md)の希望IFに合わせた便利口（SoundSettingsへ委譲）
  window.setMasterVolume = (v) => window.SoundSettings.set('master', v);
  window.getMasterVolume = () => vol.master;
  window.setSfxVolume    = (v) => window.SoundSettings.set('sfx', v);
  window.getSfxVolume    = () => vol.sfx;
  window.setBgmVolume    = (v) => window.SoundSettings.set('bgm', v);
  window.getBgmVolume    = () => vol.bgm;
  window.setAmbVolume    = (v) => window.SoundSettings.set('amb', v); // 環境音
  window.getAmbVolume    = () => vol.amb;
  window.setMuted        = (b) => window.SoundSettings.set('muted', b);
  window.isMuted         = () => vol.muted;
  window.setSfxGain      = (name, v) => window.SoundSettings.setGain(name, v); // 個別SE倍率
  window.getSfxGain      = (name) => window.SoundSettings.getGain(name);

  // 決定的テスト：bgmBus 経路を直接鳴らす。鳴れば「bgmBus→master→出力」は生きていて
  // 原因は scene gain（gainで消えている）／鳴らなければ bgmBus 経路が断、と一発で切り分く。
  window.testBGMBeep = () => {
    const c = ac(); if (!c) return 'NG: AudioContext無し';
    const o = c.createOscillator(), g = c.createGain();
    o.type = 'square'; o.frequency.value = 440;
    g.gain.setValueAtTime(0.0001, c.currentTime);
    g.gain.exponentialRampToValueAtTime(0.3, c.currentTime + 0.02);
    g.gain.exponentialRampToValueAtTime(0.0001, c.currentTime + 0.6);
    o.connect(g).connect(bgmBus); o.start(); o.stop(c.currentTime + 0.65); // ★bgmBus直結
    return 'beep送出: 440Hz/0.6s/gain0.3 を bgmBus 経由で再生（聞こえれば経路OK＝原因はscene gain）';
  };

  // 診断：console で getSoundDiag() を叩けば状態が出る（H診断にも流用可）
  window.getSoundDiag = () => {
    const node = bgmScene ? sceneNodes[bgmScene] : null;
    let totalPad = 0; Object.keys(sceneNodes).forEach((n) => { totalPad += sceneNodes[n].pad.length; });
    return {
      audioContext: ctx ? ctx.state : 'none(未生成)',   // running / suspended / none
      bgmOn: bgmOn, bgmScene: bgmScene,
      // 「鳴る準備はできているのに音が出ない」をここで切り分ける ↓
      schedulerRunning: !!bgmTimer,                          // ノート生成ループが回っているか
      activeScenePadOscillators: node ? node.pad.length : 0, // アクティブシーンのpad数（0なら無音）
      totalPadOscillators: totalPad,
      activeSceneGain: node ? +node.gain.gain.value.toFixed(4) : null, // ←0なら原因確定（gainで消えてる）
      lastNoteAgoSec: (ctx && lastNoteTime) ? +(ctx.currentTime - lastNoteTime).toFixed(2) : null, // 直近ノートから何秒
      ambType: ambType,                                     // 現在の環境音タイプ
      ambBusGain: ambBus ? +ambBus.gain.value.toFixed(3) : null,
      bgmRich: BGM_RICH,                                    // ②BGMリッチ化の版（実機で追跡用）
      activeSceneLayers: node ? node.pad.length : 0,        // アクティブシーンの常駐レイヤー数（pad+LFO+sub+shimmer）
      bgmBusGain: bgmBus ? +bgmBus.gain.value.toFixed(3) : null,
      sfxBusGain: sfxBus ? +sfxBus.gain.value.toFixed(3) : null,
      masterGain: master ? +master.gain.value.toFixed(3) : null,
      muted: vol.muted,
      vol: { master: vol.master, sfx: vol.sfx, bgm: vol.bgm },
      musicSceneCalledByCore: typeof window.__setMusicSceneCalled === 'boolean' ? window.__setMusicSceneCalled : '(未計測)',
    };
  };

  // 設定の永続化（localStorage）：起動時に復元し、変更時に保存（音量＋個別倍率）
  const VOL_KEY = 'vw_sound_v1';
  function saveVol() { try { localStorage.setItem(VOL_KEY, JSON.stringify({ master: vol.master, sfx: vol.sfx, bgm: vol.bgm, amb: vol.amb, muted: vol.muted, gains: gains })); } catch (e) {} }
  (function loadVol() {
    try {
      const s = JSON.parse(localStorage.getItem(VOL_KEY) || 'null');
      if (s) {
        ['master', 'sfx', 'bgm', 'amb'].forEach((k) => { if (typeof s[k] === 'number') vol[k] = clamp01(s[k]); });
        vol.muted = !!s.muted;
        if (s.gains) Object.keys(gains).forEach((k) => { if (typeof s.gains[k] === 'number') gains[k] = Math.max(0, Math.min(4, s.gains[k])); });
      }
    } catch (e) {}
  })();
})();
