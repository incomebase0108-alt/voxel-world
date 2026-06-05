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
    whiff: 1, charge_start: 1, charge_full: 1, levelup: 1, boss_roar: 1, boss_defeat: 1,
    companion_join: 1, companion_reply: 1, companion_hit: 1, companion_leave: 1, // 仲間システム
    // チンチラ世界の動物SE（敵/仲間/ペット）。個別倍率で「狼うるさい」等に即対応。
    wolf_howl: 1, wolf_growl: 1, snake_hiss: 1, snake_strike: 1, weasel_screech: 1, bird_screech: 1, bird_wingflap: 1, attack_bite: 1, // 敵
    animal_hurt: 1, animal_die: 1,                                                                     // 被ダメ/死亡（共通・種別ピッチ）
    squirrel_chitter: 1, rabbit_thump: 1, guineapig_wheek: 1, hedgehog_huff: 1,                       // 仲間
    pet_squeak: 1, pet_bite: 1, pet_happy: 1, pet_pee: 1,                                              // ペット(さくら)
  };
  let curMul = 1; // 再生中SEの倍率（tone/noise が参照。playSFX が設定）
  let limiter = null; // ③ master 直前のセーフティ・リミッタ（多数のSE＋BGM重畳時のクリップ防止）

  function ac() {
    if (!ctx) {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return null;
      ctx = new AC();
      // バス構成： source → (sfxBus|bgmBus|ambBus) → master → limiter → destination
      master = ctx.createGain();
      sfxBus = ctx.createGain();
      bgmBus = ctx.createGain();
      ambBus = ctx.createGain(); // ① 環境音アンビエンス（BGMの下）
      // セーフティ・リミッタ：ピークだけを抑える透明な設定（threshold高め＋速いattack＝音色は変えずクリップのみ防止）。
      limiter = ctx.createDynamicsCompressor();
      try {
        limiter.threshold.value = -3.0;  // -3dB を超えるピークのみ抑制
        limiter.knee.value = 0;          // ハードニー＝リミッタ的
        limiter.ratio.value = 20;        // 実質ブリックウォール
        limiter.attack.value = 0.003;
        limiter.release.value = 0.25;
      } catch (e) {}
      sfxBus.connect(master); bgmBus.connect(master); ambBus.connect(master);
      master.connect(limiter); limiter.connect(ctx.destination); // master → limiter → 出力
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
  // ノイズ（破裂音・雷・打撃・足音用）。at=発音オフセット秒（連打/羽ばたき等のリズム用・省略時0）
  function noise(dur, gain, filterFreq, type, dest, at) {
    const c = ac(); if (!c) return;
    const t = c.currentTime + (at || 0), n = Math.floor(c.sampleRate * dur);
    const buf = c.createBuffer(1, n, c.sampleRate), d = buf.getChannelData(0);
    for (let i = 0; i < n; i++) d[i] = Math.random() * 2 - 1;
    const src = c.createBufferSource(); src.buffer = buf;
    const g = c.createGain(); g.gain.setValueAtTime((gain || 0.2) * curMul, t); g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    const f = c.createBiquadFilter(); f.type = type || 'lowpass'; f.frequency.value = filterFreq || 1000;
    src.connect(f).connect(g).connect(dest || sfxBus);
    src.start(t); src.stop(t + dur);
  }
  // 動物SEの 3D 定位先（opts.dest にパンナーが入っていれば 3D 経由・無ければ sfxBus）。distance減衰は makePanner 側の inverse モデル。
  const aDest = (o) => (o && o.dest) || null;

  // 被ダメ(hurt)/死亡(die)は種ごとに基準ピッチと音色を変えて聞き分け可能に（playAnimalSFX が opts.species を注入）。
  //   hurt=短い痛みの悲鳴／die=力尽きる下降。snake だけは噴気的（hiss系）に分岐。汎用 animal_hurt/animal_die から呼ぶ。
  const VOICE = {
    wolf:      { base: 430,  wave: 'sawtooth' }, // キャイン（中低）
    snake:     { base: 0,    wave: 'hiss'     }, // 噴気
    weasel:    { base: 1500, wave: 'square'   }, // 甲高い
    bird:      { base: 1700, wave: 'sawtooth' }, // 鋭い
    squirrel:  { base: 1700, wave: 'square'   },
    rabbit:    { base: 780,  wave: 'sine'     },
    guineapig: { base: 950,  wave: 'sawtooth' },
    hedgehog:  { base: 1250, wave: 'square'   },
    pet:       { base: 1100, wave: 'sine'     },
  };
  function animHurt(sp, o) {
    const V = VOICE[sp] || VOICE.pet, d = aDest(o), v = (o && o.vol) || 1;
    if (V.wave === 'hiss') { noise(0.12, 0.10 * v, 5000, 'highpass', d); tone(320, 0.08, 'square', 0.05 * v, 180, d); return; } // 蛇のシュッと縮む
    tone(V.base, 0.12, V.wave, 0.12 * v, V.base * 0.55, d);    // 痛みの悲鳴（下降）
    noise(0.05, 0.05 * v, 2200, 'highpass', d);               // ヒットのざらつき
  }
  function animDie(sp, o) {
    const V = VOICE[sp] || VOICE.pet, d = aDest(o), v = (o && o.vol) || 1;
    if (V.wave === 'hiss') { noise(0.32, 0.07 * v, 3500, 'highpass', d); tone(230, 0.30, 'sawtooth', 0.06 * v, 90, d); noise(0.18, 0.04 * v, 500, 'lowpass', d, 0.06); return; }
    tone(V.base * 0.92, 0.32, V.wave, 0.11 * v, V.base * 0.30, d);        // 力尽きる下降
    tone(V.base * 0.88, 0.32, 'sine', 0.05 * v, V.base * 0.28, d, 0.02);  // デチューンの厚み
    noise(0.18, 0.04 * v, 600, 'lowpass', d, 0.06);                      // 崩れ落ち
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
    pet_dust()    { noise(0.12, 0.05, 1100, 'bandpass'); tone(420, 0.06, 'sine', 0.03, 240); },        // ペット砂浴び（やわらかい砂の「ふっ」）
    // ※ 動物8種の種別SE（wolf_howl/wolf_growl/snake_hiss/squirrel_chitter/rabbit_thump/hedgehog_huff/
    //   bird_chirp/bird_flap）は下の「チンチラ世界の動物SE」ブロックに集約（3D定位対応の本実装）。
    //   1号機 critterSE(index.html) が呼ぶキーはすべてそちらに揃えてある（後方互換）。
    // レベルアップ（1号機の playSFX('levelup') 連携）：上昇アルペジオ＋締めのきらめき
    levelup() {
      const seq = [523.25, 659.25, 783.99, 1046.50]; // C5-E5-G5-C6
      seq.forEach((f, i) => tone(f, 0.20, 'square', 0.12, f, null, i * 0.09));
      tone(1318.51, 0.30, 'sine', 0.10, 1568.00, null, 0.40); // 締め(E6→G6きらめき)
    },
    // ① ボス出現の威圧音。1号機 window.onBossAppear(type) 連携。type=ボス三系統で個性付与（未指定でも汎用咆哮として成立）。
    //   共通土台＝地響きサブ＋低域うなり＋デチューン咆哮(うなり)＋三全音上(不協和)で「威圧」を作る。
    boss_roar(o) {
      const type = o && o.type;
      tone(60,   1.10, 'sine',     0.32, 34);            // 地響き（felt-bass・下降）
      noise(0.90, 0.20, 240, 'lowpass');                 // 低域のうなり（咆哮の胴体）
      tone(82,   0.95, 'sawtooth', 0.15, 66);            // 咆哮（低）
      tone(86.5, 0.95, 'sawtooth', 0.13, 70);            // デチューン（うなり感）
      tone(116,  0.70, 'sawtooth', 0.09, 98);            // 三全音上（威圧の不協和）
      switch (type) {
        case 'golem':         // 石の巨像：さらに低く・岩の崩れ
          tone(44, 1.00, 'sine', 0.18, 30);
          noise(0.55, 0.16, 180, 'lowpass');
          for (let i = 0; i < 4; i++) noise(0.06, 0.10, 320, 'lowpass'); // ゴロゴロ崩れ
          break;
        case 'dragon':        // 竜：高域へ駆け上がる金切り咆哮＋炎のブレス
          tone(300,  0.60, 'sawtooth', 0.10, 1400);      // 立ち上がる咆哮
          tone(1500, 0.50, 'sawtooth', 0.05, 600);       // 金切り（下降）
          noise(0.70, 0.11, 2600, 'highpass');           // 炎のブレス（高域ノイズ）
          break;
        case 'skeleton_king': // 骸骨王：骨のカタカタ＋中空の不協和な鐘
          for (let i = 0; i < 8; i++) noise(0.03, 0.06, 2800, 'bandpass'); // 骨カタカタ
          tone(220, 0.90, 'square', 0.06, 110);          // 中空の不気味音
          tone(370, 1.00, 'sine', 0.05, 370); tone(392, 1.00, 'sine', 0.04, 392); // 短2度ずれの鐘
          break;
      }
    },
    // ② ボス撃破の勝利ファンファーレ。1号機 window.onBossDefeat(type) 連携（達成感の音）。
    //   上昇ブラス分散和音(D-G-B-D) → 解決する長三和音(G major) → 高域きらめきの余韻＋ティンパニ風の一撃。
    boss_defeat() {
      const brass = (f, dur, g, at) => tone(f, dur, 'sawtooth', g, f, null, at); // 持続ブラス（スライド無し）
      brass(293.66, 0.16, 0.11, 0.00); // D4
      brass(392.00, 0.16, 0.11, 0.12); // G4
      brass(493.88, 0.16, 0.11, 0.24); // B4
      brass(587.33, 0.42, 0.13, 0.36); // D5（伸ばし）
      [392.00, 493.88, 587.33].forEach((f) => tone(f, 0.90, 'sawtooth', 0.09, f, null, 0.42)); // 解決のG長三和音
      tone(98.00, 1.00, 'triangle', 0.11, 98.00, null, 0.42);                                   // 低音の土台（G2トニック）
      tone(180, 0.18, 'sine', 0.15, 60, null, 0.00); tone(180, 0.18, 'sine', 0.13, 60, null, 0.24); // ティンパニ風の一撃×2
      tone(1174.66, 0.55, 'sine', 0.06, 1567.98, null, 0.55);  // きらめき(D6→G6)
      tone(1567.98, 0.50, 'triangle', 0.05, 1567.98, null, 0.72); // 締めの高域
    },

    // === 仲間システム（NPCが仲間になる新機能）。1号機が口を呼ぶだけ・未呼出なら無音待機 ===
    //   type は仲間種（'knight'|'archer'|'mage' 等）。省略でも汎用音として成立。
    // ① 仲間加入＝心強い・温かい上昇ファンファーレ（「頼れる味方が増えた」安心感。勝利感より温かさ寄り）。
    companion_join(o) {
      const type = o && o.type;
      const seq = [261.63, 329.63, 392.00, 523.25];                              // C4-E4-G4-C5 長三和音→オクターブ着地
      seq.forEach((f, i) => tone(f, 0.22, 'triangle', 0.11, f, null, i * 0.07));
      tone(130.81, 0.55, 'sine', 0.10, 130.81, null, 0.00);                       // 低い根音ドローン(C3)＝地に足のついた安心
      tone(392.00, 0.45, 'sine', 0.06, 587.33, null, 0.28);                       // ふわりと上へ(G4→D5 きらめき)
      // type で軽い個性（任意・未指定でも汎用で成立）
      if (type === 'archer')      tone(880.00, 0.10, 'sine',     0.05, 1320.00, null, 0.30); // 弓兵: 軽やかな高音
      else if (type === 'mage')   tone(659.25, 0.30, 'sine',     0.05,  988.00, null, 0.24); // 魔法使い: 魔法的なきらめき
      else if (type === 'knight') tone(98.00,  0.40, 'sawtooth', 0.06,   98.00, null, 0.10); // 騎士: 重厚な低音
    },
    // ② 指示を受けた時の了解音（短く明るい「了解！」の二音）。頻繁に鳴るので短く軽く。type で僅かに音高を変え個体感。
    companion_reply(o) {
      const k = (o && o.type === 'mage') ? 1.12 : (o && o.type === 'knight') ? 0.9 : 1.0;
      tone(523.25 * k, 0.07, 'sine', 0.10, 659.25 * k, null, 0.00);
      tone(783.99 * k, 0.09, 'sine', 0.09, 880.00 * k, null, 0.06);
    },
    // ③ 仲間が攻撃を受けた（被ダメ）。プレイヤーの hurt と区別できる「味方が傷ついた」短い悲鳴＋衝撃。
    companion_hit() {
      noise(0.06, 0.12, 1400);                          // 衝撃
      tone(440, 0.16, 'square', 0.13, 240);             // 痛みの悲鳴（下降・hurtより高め＝別個体と分かる）
      tone(330, 0.12, 'sine', 0.06, 220, null, 0.04);   // 心配なうめき
    },
    // ④ 仲間の離脱（倒れた/解雇）。物悲しい下降。短いが余韻を残す。
    companion_leave() {
      const seq = [392.00, 329.63, 261.63];                                       // G4-E4-C4 下降（哀しい解決）
      seq.forEach((f, i) => tone(f, 0.30, 'triangle', 0.10, f, null, i * 0.12));
      tone(196.00, 0.50, 'sine', 0.07, 130.81, null, 0.24);                       // 低音が沈む(G3→C3)
      noise(0.18, 0.06, 300, 'lowpass');                                          // 崩れ落ちる土の音
    },

    // === チンチラ世界の動物SE（敵8種＋仲間＋ペット）===========================
    //   各音は opts.dest にパンナーがあれば 3D 定位（playAnimalSFX が座標から自動付与）。
    //   opts.vol で個体ごとの強弱（省略=1）。1号機は playAnimalSFX(種, イベント) か playSFX(キー) で鳴らすだけ。
    // ── 敵 ──
    wolf_howl(o)      { const d = aDest(o), v = (o && o.vol) || 1;                 // 遠吠え：低く立ち上がり→山から長く下降（A3→A#4→G4）
                        tone(247, 0.55, 'sawtooth', 0.09 * v, 466, d);
                        tone(466, 0.95, 'sawtooth', 0.10 * v, 392, d, 0.5);
                        tone(470, 0.95, 'sine',     0.05 * v, 396, d, 0.5);        // デチューンで厚み（うなり感）
                        noise(0.40, 0.02 * v, 1200, 'bandpass', d, 0.1); },        // 息のざらつき
    wolf_growl(o)     { const d = aDest(o), v = (o && o.vol) || 1;                 // うなり：低い鋸波のビート＋胴のゴロゴロ
                        tone(90, 0.50, 'sawtooth', 0.12 * v, 70, d);
                        tone(95, 0.50, 'sawtooth', 0.10 * v, 74, d);               // 微妙にずらしてうなりのビート
                        noise(0.45, 0.05 * v, 320, 'lowpass', d); },
    snake_hiss(o)     { const d = aDest(o), v = (o && o.vol) || 1;                 // シューッ：高域ノイズの持続
                        noise(0.55, 0.10 * v, 6500, 'highpass', d);
                        noise(0.50, 0.05 * v, 4000, 'bandpass', d, 0.05); },
    weasel_screech(o) { const d = aDest(o), v = (o && o.vol) || 1;                 // 甲高い威嚇：鋭い金切り＋ざらつき
                        tone(1400, 0.18, 'square',   0.07 * v, 2100, d);
                        tone(1900, 0.14, 'sawtooth', 0.05 * v, 1200, d, 0.08);
                        noise(0.12, 0.04 * v, 3000, 'highpass', d); },
    bird_screech(o)   { const d = aDest(o), v = (o && o.vol) || 1;                 // 猛禽の鳴き：高域から下降する叫びを2発
                        tone(2200, 0.16, 'sawtooth', 0.06 * v, 1500, d);
                        tone(2000, 0.20, 'sawtooth', 0.06 * v, 1300, d, 0.18);
                        noise(0.10, 0.02 * v, 4000, 'highpass', d); },
    bird_wingflap(o)  { const d = aDest(o), v = (o && o.vol) || 1;                 // 羽ばたき：低い風切りノイズを3拍
                        for (let i = 0; i < 3; i++) { noise(0.10, 0.07 * v, 700, 'lowpass', d, i * 0.16); tone(120, 0.08, 'sine', 0.03 * v, 80, d, i * 0.16); } },
    // 近接攻撃のヒット（spot の鳴き声と聞き分けるための「噛みつき」系。捕食者の attack に使用）
    attack_bite(o)    { const d = aDest(o), v = (o && o.vol) || 1;                 // 噛みつき：鋭いスナップ＋肉を捉える低い衝撃
                        noise(0.05, 0.11 * v, 2400, 'highpass', d);
                        tone(170, 0.07, 'square', 0.10 * v, 90, d);
                        noise(0.06, 0.06 * v, 500, 'lowpass', d, 0.02); },
    snake_strike(o)   { const d = aDest(o), v = (o && o.vol) || 1;                 // 蛇の毒牙ラッシュ：素早い噴気→噛みつき
                        noise(0.10, 0.10 * v, 6000, 'highpass', d);
                        noise(0.05, 0.09 * v, 2200, 'highpass', d, 0.07);
                        tone(150, 0.05, 'square', 0.08 * v, 80, d, 0.07); },
    // ── 仲間 ──
    squirrel_chitter(o){ const d = aDest(o), v = (o && o.vol) || 1;                // チチッ：高い square を素早く連打
                        for (let i = 0; i < 4; i++) tone(2000 + Math.random() * 400, 0.04, 'square', 0.05 * v, 2600, d, i * 0.06); },
    rabbit_thump(o)   { const d = aDest(o), v = (o && o.vol) || 1;                 // 後足スタンピング：低い打撃を2発
                        for (let i = 0; i < 2; i++) { tone(90, 0.10, 'sine', 0.16 * v, 55, d, i * 0.18); noise(0.06, 0.06 * v, 200, 'lowpass', d, i * 0.18); } },
    guineapig_wheek(o){ const d = aDest(o), v = (o && o.vol) || 1;                 // ウィーク鳴き：上昇→下降の口笛様
                        tone(700, 0.18, 'sawtooth', 0.08 * v, 1500, d);
                        tone(1500, 0.22, 'sawtooth', 0.09 * v, 900, d, 0.16); },
    hedgehog_huff(o)  { const d = aDest(o), v = (o && o.vol) || 1;                 // 丸まりフスフス：短い鼻息ノイズを3拍
                        for (let i = 0; i < 3; i++) noise(0.07, 0.05 * v, 1800, 'bandpass', d, i * 0.12); },
    // ── ペット（さくら）──
    pet_squeak(o)     { const d = aDest(o), v = (o && o.vol) || 1;                 // 鳴き：かわいい高い短音
                        tone(900, 0.10, 'sine', 0.10 * v, 1500, d);
                        tone(1500, 0.08, 'sine', 0.07 * v, 1100, d, 0.08); },
    pet_bite(o)       { const d = aDest(o), v = (o && o.vol) || 1;                 // 噛みつき：鋭いスナップ＋低いカチッ
                        noise(0.04, 0.10 * v, 2500, 'highpass', d);
                        tone(180, 0.05, 'square', 0.08 * v, 90, d); },
    pet_happy(o)      { const d = aDest(o), v = (o && o.vol) || 1;                 // ごきげん：上昇するきらきらチャープ3音
                        [880, 1100, 1320].forEach((f, i) => tone(f, 0.10, 'sine', 0.08 * v, f * 1.2, d, i * 0.08)); },
    pet_pee(o)        { const d = aDest(o), v = (o && o.vol) || 1;                 // 威嚇オシッコ：噴射のシャーッ＋威嚇のキュッ
                        noise(0.35, 0.05 * v, 3500, 'highpass', d);
                        tone(1300, 0.10, 'square', 0.05 * v, 1900, d); },
    // ── 全種共通の被ダメ/死亡（opts.species で種ごとにピッチ・音色を変える＝聞き分け。playAnimalSFX が species を注入）──
    animal_hurt(o)    { animHurt(o && o.species, o); },                            // 短い痛みの悲鳴
    animal_die(o)     { animDie(o && o.species, o); },                             // 力尽きる下降
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

  // === ① ボス連携（防御的: 1号機が口を呼ぶだけ・未呼出なら無音待機）=====
  //   window.onBossAppear(type) … ボス出現の威圧音。type='golem'|'dragon'|'skeleton_king'（省略=汎用咆哮）
  //   戦闘BGMは既存 window.setMusicScene('boss') で combat より重厚な boss シーンへ（口は②で公開済み）
  window.onBossAppear  = (type) => window.playSFX('boss_roar', { type });
  //   window.onBossDefeat(type) … ② ボス撃破の勝利ファンファーレ（達成感）。撃破確定時に1回呼ぶだけ。
  //   撃破後は戦闘継続でなければコアが setMusicScene を day/night 等へ戻せばBGMも平常へ（既存挙動）。
  window.onBossDefeat  = (type) => window.playSFX('boss_defeat', { type });

  // === 仲間システム連携（防御的: 1号機が口を呼ぶだけ・未呼出なら無音待機）=====
  //   window.onCompanionJoin(type)  … ① NPCが仲間になった時の心強い加入音。type=仲間種（'knight'|'archer'|'mage' 等／省略=汎用）
  //   window.onCompanionReply(type) … ② 指示を受けた時の了解音（コマンド発行時の「了解！」）。type省略可【②用に新設＝1号機へ呼出依頼】
  //   window.onCompanionHit(type?)  … ③ 仲間が攻撃を受けた被ダメ音（味方が傷ついた）。typeは任意（将来の個体差用・現状未使用でも安全）
  //   window.onCompanionLeave(type?)… ④ 仲間が倒れた/解雇された離脱音（物悲しい）
  window.onCompanionJoin  = (type) => window.playSFX('companion_join',  { type });
  window.onCompanionReply = (type) => window.playSFX('companion_reply', { type });
  window.onCompanionHit   = (type) => window.playSFX('companion_hit',   { type });
  window.onCompanionLeave = (type) => window.playSFX('companion_leave', { type });

  // === チンチラ世界の動物SE 公開口（防御的: 1号機が呼ぶだけ・未配線でも無音で安全）=====
  //   window.playAnimalSFX(species, event, opts) … species×event を SEキーへ写像して鳴らす（推奨API）。
  //     ・event: 'spot'|'attack'|'hurt'|'die'|'skill'|'tamed'|'happy'、および 1号機 critterSE 語彙 'howl'|'dive'|'curl'|'alert'|'tame'(=tamed)。未知eventは各種の default 音。
  //     ・opts.x/y/z があれば 3D 定位（距離減衰つき）。opts.vol で強弱（省略=1）。
  //     ・未知 species は黙って無音（事故ゼロ）。個別に鳴らしたい時は従来どおり playSFX('wolf_howl') でも可。
  const ANIMAL_ALIAS = { sakura: 'pet', 'さくら': 'pet', raptor: 'bird', hawk: 'bird', eagle: 'bird', owl: 'bird', cavy: 'guineapig' };
  const ANIMAL_SFX = {
    //   ※ 1号機 critterSE(index.html) の event 語彙（howl/dive/curl/alert/spot/attack/tame…）も網羅。'tame' は下で 'tamed' へ正規化。
    //   spot=鳴き声で発見を知らせる／attack=噛みつき等の打撃音で聞き分け／hurt・die=共通ジェネリック(種別ピッチ)。
    // 敵
    wolf:      { spot: 'wolf_growl',     howl: 'wolf_howl',       attack: 'attack_bite',   hurt: 'animal_hurt',    die: 'animal_die',     skill: 'wolf_howl',     default: 'wolf_growl' },
    snake:     { spot: 'snake_hiss',     attack: 'snake_strike',  hurt: 'animal_hurt',     die: 'animal_die',      skill: 'snake_hiss',                            default: 'snake_hiss' },
    weasel:    { spot: 'weasel_screech', attack: 'attack_bite',   hurt: 'animal_hurt',     die: 'animal_die',      skill: 'weasel_screech',                        default: 'weasel_screech' },
    bird:      { spot: 'bird_screech',   dive: 'bird_wingflap',   attack: 'bird_wingflap', hurt: 'animal_hurt',    die: 'animal_die',     skill: 'bird_wingflap', screech: 'bird_screech', default: 'bird_screech' },
    // 仲間
    squirrel:  { spot: 'squirrel_chitter', attack: 'squirrel_chitter', hurt: 'animal_hurt', die: 'animal_die', skill: 'squirrel_chitter', tamed: 'squirrel_chitter', happy: 'squirrel_chitter', default: 'squirrel_chitter' },
    rabbit:    { spot: 'rabbit_thump',     alert: 'rabbit_thump',      hurt: 'animal_hurt', die: 'animal_die', skill: 'rabbit_thump',     tamed: 'rabbit_thump',                               default: 'rabbit_thump' },
    guineapig: { spot: 'guineapig_wheek',  hurt: 'animal_hurt',        die: 'animal_die',   skill: 'guineapig_wheek',  tamed: 'guineapig_wheek',  happy: 'guineapig_wheek',                   default: 'guineapig_wheek' },
    hedgehog:  { spot: 'hedgehog_huff',    curl: 'hedgehog_huff',      hurt: 'animal_hurt', die: 'animal_die', skill: 'hedgehog_huff',    tamed: 'hedgehog_huff',                              default: 'hedgehog_huff' },
    // ペット（さくら）
    pet:       { spot: 'pet_squeak', attack: 'pet_bite', skill: 'pet_pee', happy: 'pet_happy', tamed: 'pet_happy', hurt: 'pet_squeak', die: 'pet_squeak', default: 'pet_squeak' },
  };
  // SEキーを 3D 定位つきで再生（座標があればパンナー経由・無ければ sfxBus）。makePanner は ③ 空間音響で定義（hoist 済）。
  function playAnimalKey(key, o) {
    let p = null;
    if (o && o.x != null && typeof makePanner === 'function') p = makePanner(o.x, o.y, o.z); // 失敗時 null → 非空間で鳴る
    window.playSFX(key, Object.assign({}, o, { dest: p }));
    if (p) setTimeout(() => { try { p.disconnect(); } catch (e) {} }, 2000); // 余韻ぶん残して片付け
  }
  const EVENT_ALIAS = { tame: 'tamed' }; // 1号機 critterSE は 'tame'、こちらの正準は 'tamed'
  window.playAnimalSFX = (species, event, opts) => {
    try {
      const sp = ANIMAL_ALIAS[species] || species;
      const ev = EVENT_ALIAS[event] || event;
      const tbl = ANIMAL_SFX[sp]; if (!tbl) return;             // 未知種は黙って無音
      const key = tbl[ev] || tbl.default; if (!key) return;
      playAnimalKey(key, Object.assign({}, opts, { species: sp })); // species を注入＝共通 hurt/die が種別ピッチで鳴る
    } catch (e) { /* 防御 */ }
  };
  // 旧来の onXxx スタイルを好む配線向けの別名（任意・未使用でも安全）
  window.onAnimalSound = (species, event, opts) => window.playAnimalSFX(species, event, opts);

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
    // ① ボス戦専用シーン（combatより重厚）。1号機のボス三系統(golem/dragon/skeleton_king)接近時に setMusicScene('boss')。
    //   combatより低い音域＋三全音テンション(G#3=207.65 vs 根音D)＋重いサブベース(bassG高)で威圧感。テンポはやや遅く=重い。
    boss:   { tempo: 132, scale: [146.83, 174.61, 207.65, 220.00, 261.63], pad: [73.42,  87.31,  110.00], wave: 'sawtooth', density: 0.90, drums: true,  level: 1.1, bassG: 0.11,  shimmer: false, bassline: true,  tremHz: 0.5,  tremDepth: 0.13 },
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
      o.type = (name === 'combat' || name === 'boss') ? 'sawtooth' : 'sine'; // boss も鋸波で攻撃的に
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
    // ③ 特別な場所の荘厳な環境音。1号機が window.getBiome() で 'castle'/'shrine' を返せば連動（無くても他biomeは不変）。
    castle:  { f: 180,  q: 1.2, g: 0.05,  chirp: { type: 'choir',   rate: 0.16 } }, // 王国城: 低い大広間のうなり＋荘厳な聖歌/オルガンの swell
    shrine:  { f: 760,  q: 0.8, g: 0.035, chirp: { type: 'chime',   rate: 0.22 } }, // 祠: 静謐な空気＋ときおりの清らかな鈴
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
      // ③ 荘厳系: ゆっくり立ち上がる聖歌/オルガンの和音 swell（王国城）と、清らかな鈴（祠）
      case 'choir': { // G major のロング三和音をやわらかく重ねる（オルガン/聖歌の swell）
        [196.00, 293.66, 392.00].forEach((f, i) => tone(f, 2.2, 'triangle', 0.030, f, ambBus, i * 0.05));
        tone(98.00, 2.4, 'sine', 0.024, 98.00, ambBus); // 根音1oct下のドローンで荘厳さ
        break;
      }
      case 'chime': { // 倍音つきの澄んだ鈴（非整数倍音でベル感・長い余韻）
        const f0 = 880 * (Math.random() < 0.5 ? 1 : 1.5); // たまに5度上
        tone(f0,        1.6, 'sine', 0.040, f0,        ambBus);
        tone(f0 * 2.76, 1.2, 'sine', 0.016, f0 * 2.76, ambBus); // 金属的な倍音
        tone(f0 * 1.5,  1.0, 'sine', 0.014, f0 * 1.5,  ambBus);
        break;
      }
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
      limiterReductionDb: limiter ? +limiter.reduction.toFixed(2) : null, // ③ リミッタが今どれだけ抑制中か（0=余裕／負=ピーク抑制中）
      spatial: { listenerHook: typeof window.getPlayerPose === 'function', mobHook: typeof window.getMobPositions === 'function', biomeHook: typeof window.getBiome === 'function' }, // ③ コア側の読み取り口が揃っているか
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
