// ===================================================================
// サウンド土台（WebAudio 合成音・本体コードと疎結合）
//   ・index.html 側は window.playSFX('name') を呼ぶだけ（未読込でも壊れない）
//   ・既存トリガー window.onThunderSound / window.onPlayerHurt もここで実装
//   ・素材は仮の合成音。後で音声ファイル再生に差し替え可能
// ===================================================================
(function () {
  let ctx = null;
  function ac() {
    if (!ctx) { const AC = window.AudioContext || window.webkitAudioContext; if (!AC) return null; ctx = new AC(); }
    if (ctx.state === 'suspended') ctx.resume(); // ユーザー操作起点で再開
    return ctx;
  }
  // 単音（周波数スライド可）
  function tone(freq, dur, type, gain, slideTo) {
    const c = ac(); if (!c) return;
    const t = c.currentTime, o = c.createOscillator(), g = c.createGain();
    o.type = type || 'sine';
    o.frequency.setValueAtTime(freq, t);
    if (slideTo) o.frequency.exponentialRampToValueAtTime(Math.max(1, slideTo), t + dur);
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(gain || 0.2, t + 0.01);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g).connect(c.destination);
    o.start(t); o.stop(t + dur + 0.02);
  }
  // ノイズ（破裂音・雷・打撃用）
  function noise(dur, gain, filterFreq) {
    const c = ac(); if (!c) return;
    const t = c.currentTime, n = Math.floor(c.sampleRate * dur);
    const buf = c.createBuffer(1, n, c.sampleRate), d = buf.getChannelData(0);
    for (let i = 0; i < n; i++) d[i] = Math.random() * 2 - 1;
    const src = c.createBufferSource(); src.buffer = buf;
    const g = c.createGain(); g.gain.setValueAtTime(gain || 0.2, t); g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    const f = c.createBiquadFilter(); f.type = 'lowpass'; f.frequency.value = filterFreq || 1000;
    src.connect(f).connect(g).connect(c.destination);
    src.start(t); src.stop(t + dur);
  }
  // 効果音テーブル（仮の合成音）
  const SFX = {
    thunder() { noise(0.6, 0.5, 500); tone(64, 0.5, 'sine', 0.4, 40); },
    hurt()    { tone(200, 0.18, 'square', 0.22, 120); },
    attack()  { tone(180, 0.07, 'square', 0.18, 90); noise(0.05, 0.08, 2200); },
    hit()     { noise(0.08, 0.16, 1600); },
    pickup()  { tone(660, 0.08, 'sine', 0.16, 990); },
    eat()     { tone(300, 0.12, 'sine', 0.14, 360); },
    jump()    { tone(330, 0.09, 'sine', 0.10, 520); },
    break()   { noise(0.12, 0.16, 900); },
    place()   { tone(220, 0.06, 'sine', 0.13, 180); },
  };
  window.playSFX = (name) => { try { (SFX[name] || (() => {}))(); } catch (e) {} };
  // 既存トリガーをサウンドに接続
  window.onThunderSound = () => window.playSFX('thunder');
  window.onPlayerHurt   = () => window.playSFX('hurt');
})();
