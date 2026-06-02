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
  const vol = { master: 1.0, sfx: 1.0, bgm: 0.6, muted: false };

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
  function tone(freq, dur, type, gain, slideTo, dest) {
    const c = ac(); if (!c) return;
    const t = c.currentTime, o = c.createOscillator(), g = c.createGain();
    o.type = type || 'sine';
    o.frequency.setValueAtTime(freq, t);
    if (slideTo) o.frequency.exponentialRampToValueAtTime(Math.max(1, slideTo), t + dur);
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(gain || 0.2, t + 0.01);
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
    const g = c.createGain(); g.gain.setValueAtTime(gain || 0.2, t); g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
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
  function mobCry(type, vmul) {
    const v = vmul || 1;
    switch (type) {
      case 'cow':      tone(140, 0.45, 'sawtooth', 0.10 * v, 110); break;
      case 'sheep':    tone(330, 0.30, 'sawtooth', 0.09 * v, 300); tone(360, 0.18, 'sawtooth', 0.06 * v, 320); break;
      case 'chicken':  tone(900, 0.06, 'square', 0.07 * v, 1200); tone(1100, 0.05, 'square', 0.06 * v, 800); break;
      case 'pig':      tone(220, 0.18, 'sawtooth', 0.10 * v, 160); noise(0.10, 0.05 * v, 700); break;
      case 'horse':    tone(420, 0.35, 'sawtooth', 0.10 * v, 180); noise(0.15, 0.05 * v, 900); break;
      case 'villager': tone(260, 0.22, 'sine', 0.09 * v, 230); break;
      case 'slime':    noise(0.18, 0.10 * v, 500, 'lowpass'); break;
      case 'zombie':   tone(120, 0.5, 'sawtooth', 0.10 * v, 90); noise(0.3, 0.05 * v, 400); break;
      case 'skeleton': for (let i = 0; i < 4; i++) noise(0.04, 0.07 * v, 2500, 'bandpass'); break; // カタカタ
      case 'golem':    tone(70, 0.6, 'sine', 0.14 * v, 50); noise(0.4, 0.08 * v, 200); break;
      default:         tone(300, 0.2, 'sine', 0.08 * v, 280);
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
    mob(o)      { mobCry(o && o.type, o && o.vol); },                                       // モブ鳴き声
  };

  // 公開API：playSFX(name, opts) ── opts は省略可（後方互換）
  window.playSFX = (name, opts) => { try { (SFX[name] || (() => {}))(opts); } catch (e) {} };

  // 既存トリガーをサウンドに接続
  window.onThunderSound = () => window.playSFX('thunder');
  window.onPlayerHurt   = () => window.playSFX('hurt');

  // ④ サウンド設定の受け渡し口（UIは3号機。ここは値とロジックのみ）
  //   get() → {master,sfx,bgm,muted} / set(key,value) / setMuted(bool)
  window.SoundSettings = {
    get: () => ({ master: vol.master, sfx: vol.sfx, bgm: vol.bgm, muted: vol.muted }),
    set: (key, value) => {
      if (key === 'muted') { vol.muted = !!value; }
      else if (key in vol) { vol[key] = clamp01(Number(value)); }
      applyVolumes();
      try { window.dispatchEvent(new CustomEvent('soundsettingschange', { detail: window.SoundSettings.get() })); } catch (e) {}
    },
    setMuted: (b) => window.SoundSettings.set('muted', b),
  };
})();
