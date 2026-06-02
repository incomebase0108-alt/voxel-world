// ===================================================================
// サウンドシステム（WebAudio・本体コードと疎結合）  ── 2号機 / 音響担当
//   ・index.html 側は window.playSFX('name', opts?) を呼ぶだけ（未読込でも壊れない）
//   ・既存トリガー window.onThunderSound / window.onPlayerHurt もここで実装
//   ・素材は仮の合成音。後で音声ファイル再生に差し替え可能
//   ・音量は master / sfx / bgm の3バス構成（④設定の受け渡し口 window.SoundSettings）
// ===================================================================
(function () {
  let ctx = null, master = null, sfxBus = null, bgmBus = null;

  // ④ 音量状態（0..1）。UI見た目は3号機、ここは値の受け渡し口のみ。
  const vol = { master: 1.0, sfx: 1.0, bgm: 0.75, muted: false };

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
      sfxBus.connect(master); bgmBus.connect(master); master.connect(ctx.destination);
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
    swim()      { noise(0.18, 0.06, 600, 'lowpass'); },                                     // 水中移動
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
  // level = シーン間の音量バランス（0..1.2程度）。water は静かだが「水中だと分かる」程度に。
  const SCENES = {
    day:    { tempo: 104, scale: [220.00, 246.94, 277.18, 329.63, 369.99], pad: [110.00, 164.81, 220.00], wave: 'triangle', density: 0.55, drums: false, level: 1.0 },
    night:  { tempo: 76,  scale: [164.81, 196.00, 220.00, 261.63, 293.66], pad: [123.47, 164.81, 220.00], wave: 'sine',     density: 0.42, drums: false, level: 0.9 },
    combat: { tempo: 148, scale: [146.83, 174.61, 196.00, 220.00, 261.63], pad: [110.00, 146.83, 220.00], wave: 'sawtooth', density: 0.85, drums: true,  level: 1.0 },
    water:  { tempo: 72,  scale: [293.66, 349.23, 392.00, 440.00, 523.25], pad: [196.00, 293.66, 392.00], wave: 'sine',     density: 0.55, drums: false, level: 0.9 },
  };
  let bgmOn = false, bgmScene = null, bgmTimer = null, nextNoteT = 0, beat = 0, userMusicCtl = false, lastNoteTime = 0;
  const sceneNodes = {}; // name -> { gain, pad:[{o}] }

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
    if (node.pad.length) return; // 既に常駐済みなら二重生成しない
    const sc = SCENES[name];
    sc.pad.forEach((f, i) => {
      const o = c.createOscillator(), g = c.createGain();
      o.type = name === 'combat' ? 'sawtooth' : 'sine';
      o.frequency.value = f * (1 + (i - 1) * 0.003); // 微デチューンで厚み
      g.gain.value = 0.09;
      o.connect(g).connect(node.gain); o.start();
      node.pad.push({ o });
    });
  }
  function stopPad(name) {
    const node = sceneNodes[name]; if (!node) return;
    node.pad.forEach(({ o }) => { try { o.stop(); } catch (e) {} });
    node.pad = [];
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
  function scheduler() {
    if (!bgmOn) return;
    const c = ac();
    if (c && bgmScene && SCENES[bgmScene]) {
      const sc = SCENES[bgmScene], node = sceneGain(bgmScene), spb = 60 / sc.tempo / 2; // 8分音符
      while (nextNoteT < c.currentTime + 0.2) {
        if (Math.random() < sc.density) {
          const f = sc.scale[(Math.random() * sc.scale.length) | 0] * (Math.random() < 0.3 ? 2 : 1);
          bgmNote(f, spb * (Math.random() < 0.5 ? 1.6 : 0.9), node.gain, 0.12, sc.wave);
        }
        if (sc.drums && beat % 2 === 0) kick(node.gain);
        nextNoteT += spb; beat++;
      }
    }
    bgmTimer = setTimeout(scheduler, 60);
  }
  function fadeSceneGain(name, to) {
    const c = ac(), g = sceneGain(name).gain;
    g.cancelScheduledValues(c.currentTime);
    g.setValueAtTime(Math.max(0.0001, g.value), c.currentTime);
    g.linearRampToValueAtTime(Math.max(0.0001, to), c.currentTime + XFADE);
  }
  function startMusic(scene) {
    userMusicCtl = true;
    const c = ac(); if (!c) return;
    const s = SCENES[scene] ? scene : (bgmScene || 'day');
    if (!bgmOn) {
      bgmOn = true; nextNoteT = c.currentTime + 0.1; beat = 0;
      bgmScene = s; startPad(s); fadeSceneGain(s, SCENES[s].level || 1);
      scheduler();
      try { console.info('[sound] BGM開始 scene=' + s + ' / bgmBus=' + (bgmBus ? bgmBus.gain.value.toFixed(2) : '?') + ' / ctx=' + (ctx ? ctx.state : '?')); } catch (e) {}
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
    startPad(name); fadeSceneGain(name, SCENES[name].level || 1);
    if (prev && sceneNodes[prev]) fadeSceneGain(prev, 0); // 旋律もpadもgainで消す。oscillatorは止めない（競合回避）
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

  // ④ サウンド設定の受け渡し口（UIは3号機。ここは値とロジックのみ）
  //   get() → {master,sfx,bgm,muted} / set(key,value) / setMuted(bool)
  const clampGain = (v) => Math.max(0, Math.min(4, Number(v))); // 個別倍率は 0..4
  function emitChange() { try { window.dispatchEvent(new CustomEvent('soundsettingschange', { detail: window.SoundSettings.get() })); } catch (e) {} }
  window.SoundSettings = {
    get: () => ({ master: vol.master, sfx: vol.sfx, bgm: vol.bgm, muted: vol.muted, gains: Object.assign({}, gains) }),
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
  window.setMuted        = (b) => window.SoundSettings.set('muted', b);
  window.isMuted         = () => vol.muted;
  window.setSfxGain      = (name, v) => window.SoundSettings.setGain(name, v); // 個別SE倍率
  window.getSfxGain      = (name) => window.SoundSettings.getGain(name);

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
  function saveVol() { try { localStorage.setItem(VOL_KEY, JSON.stringify({ master: vol.master, sfx: vol.sfx, bgm: vol.bgm, muted: vol.muted, gains: gains })); } catch (e) {} }
  (function loadVol() {
    try {
      const s = JSON.parse(localStorage.getItem(VOL_KEY) || 'null');
      if (s) {
        ['master', 'sfx', 'bgm'].forEach((k) => { if (typeof s[k] === 'number') vol[k] = clamp01(s[k]); });
        vol.muted = !!s.muted;
        if (s.gains) Object.keys(gains).forEach((k) => { if (typeof s.gains[k] === 'number') gains[k] = Math.max(0, Math.min(4, s.gains[k])); });
      }
    } catch (e) {}
  })();
})();
