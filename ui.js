/* =====================================================================
 * ui.js — VOXEL WORLD の UI / HUD レイヤー（3号機担当）
 * ---------------------------------------------------------------------
 *  ・コア（index.html）は一切改変しない。状態は window.VoxelGame.state()
 *    から読み取るだけ（書き換えない）。連携仕様は UI_INTEGRATION.md。
 *  ・classic script 1本で自走。自前で <style> を注入する。
 *  ・state() が未実装の間は休止（描画せず待機ログを1回だけ出す）。
 *    → これにより (2)(3) の配線前に <script src="ui.js"> を入れても
 *       既存表示を一切壊さない（安全な段階導入）。
 *
 *  実装範囲（このファイルの現状）:
 *    ① HUD刷新 … 体力/空腹/息ゲージ・ホットバー・選択中アイテム・
 *                 レーダーミニマップ・ダメージ赤フラッシュ・回復パルス
 *    ②③④ は後続コミットで追記（window.UI.open(...) を生やす）。
 * ===================================================================== */
(function () {
  'use strict';

  // 二重読込ガード
  if (window.__VOXEL_UI__) return;
  window.__VOXEL_UI__ = true;

  // コアの inline HUD を停止してもらうためのハンドシェイク（UI_INTEGRATION.md (3)）
  window.UI_TAKEOVER = true;

  // ---- 安全ユーティリティ ------------------------------------------------
  // ★重要: 段数描画は必ず Math.max(0, n) でクランプ（負値 repeat のクラッシュ防止）
  const clampN = (n) => Math.max(0, Math.floor(Number.isFinite(n) ? n : 0));
  const clamp01 = (v) => Math.max(0, Math.min(1, v));
  const el = (tag, css, parent) => {
    const e = document.createElement(tag);
    if (css) e.style.cssText = css;
    if (parent) parent.appendChild(e);
    return e;
  };

  // =====================================================================
  // スタイル注入
  // =====================================================================
  function injectStyle() {
    const s = document.createElement('style');
    s.id = 'voxel-ui-style';
    s.textContent = `
      #ui-root { position:fixed; inset:0; z-index:15; pointer-events:none;
        font-family: system-ui, sans-serif; color:#fff; user-select:none; }
      #ui-root .panel { text-shadow:0 0 3px #000, 0 0 3px #000; }

      /* 下部中央：ステータス＋ホットバー */
      #ui-bottom { position:fixed; left:50%; bottom:14px; transform:translateX(-50%);
        display:flex; flex-direction:column; align-items:center; gap:6px; }

      /* ゲージ（体力/空腹/息） */
      .ui-gauges { display:flex; flex-direction:column; gap:3px; align-items:center; }
      .ui-row { display:flex; align-items:center; gap:5px; }
      .ui-segs { display:flex; gap:2px; }
      .ui-seg { width:13px; height:13px; border-radius:3px; background:rgba(255,255,255,.14);
        box-shadow:0 0 2px rgba(0,0,0,.6) inset; transition:background .12s, transform .12s; }
      .ui-seg.f-hp   { background:#ff4d5e; }
      .ui-seg.h-hp   { background:linear-gradient(90deg,#ff4d5e 50%,rgba(255,255,255,.14) 50%); }
      .ui-seg.f-food { background:#f3a23a; }
      .ui-seg.h-food { background:linear-gradient(90deg,#f3a23a 50%,rgba(255,255,255,.14) 50%); }
      .ui-seg.f-air  { background:#46c7ff; }
      .ui-seg.low    { animation: ui-pulse .7s ease-in-out infinite; }
      @keyframes ui-pulse { 0%,100%{ transform:scale(1) } 50%{ transform:scale(1.18) } }
      .ui-num { font-size:11px; opacity:.85; min-width:34px; }

      /* ホットバー */
      #ui-hotbar { display:flex; gap:5px; padding:6px; border-radius:10px;
        background:rgba(8,14,26,.42); backdrop-filter:blur(2px);
        box-shadow:0 2px 10px rgba(0,0,0,.35); }
      .ui-slot { position:relative; width:50px; height:50px; border-radius:8px;
        border:2px solid rgba(255,255,255,.22); display:flex; flex-direction:column;
        align-items:center; justify-content:center; transition:border-color .12s, transform .12s; }
      .ui-slot.active { border-color:#ffd54a; box-shadow:0 0 12px #ffd54a; transform:translateY(-4px); }
      .ui-slot .sw { width:24px; height:24px; border-radius:5px; border:1px solid rgba(0,0,0,.35); }
      .ui-slot .key { position:absolute; left:4px; top:2px; font-size:10px; opacity:.7; }
      .ui-slot .cnt { position:absolute; right:4px; bottom:2px; font-size:12px; font-weight:bold;
        text-shadow:0 0 2px #000,0 0 2px #000; }
      .ui-slot .cnt.zero { opacity:.35; }
      #ui-selname { font-size:13px; min-height:16px; opacity:.95; }

      /* 右上：レーダー＋情報 */
      #ui-radar-wrap { position:fixed; right:12px; top:12px; display:flex; flex-direction:column;
        align-items:flex-end; gap:5px; }
      #ui-radar { width:128px; height:128px; border-radius:50%;
        background:radial-gradient(circle at 50% 50%, rgba(10,20,35,.55), rgba(10,20,35,.78));
        border:2px solid rgba(255,255,255,.25); box-shadow:0 2px 10px rgba(0,0,0,.4); }
      #ui-info { font-size:12px; text-align:right; line-height:1.5; }
      #ui-info .b { font-weight:bold; }

      /* 全画面の被ダメージ／回復ヴィネット */
      #ui-hurt, #ui-heal { position:fixed; inset:0; z-index:24; pointer-events:none; opacity:0; }
      #ui-hurt { background:radial-gradient(circle, rgba(180,0,0,0) 42%, rgba(190,0,10,.62) 100%); }
      #ui-heal { background:radial-gradient(circle, rgba(0,180,40,0) 50%, rgba(40,210,90,.32) 100%); }

      /* ダメージFXレイヤー（HUDより上・最前面の演出） */
      #ui-fx-canvas { position:fixed; inset:0; z-index:26; pointer-events:none; }
      #ui-fx { position:fixed; inset:0; z-index:27; pointer-events:none; overflow:hidden; }
      .ui-pop { position:absolute; transform:translate(-50%,-50%); font-weight:900;
        font-family: system-ui, sans-serif; white-space:nowrap; will-change:transform,opacity;
        text-shadow:0 1px 2px #000, 0 0 4px #000; letter-spacing:.5px; }
      .ui-pop.dmg  { color:#ffd9a0; font-size:20px; }
      .ui-pop.crit { color:#ffec5c; font-size:30px; text-shadow:0 0 6px #ff7a00, 0 1px 2px #000; }
      .ui-pop.heal { color:#7cff9b; font-size:18px; }
      .ui-pop.self { color:#ff6b6b; font-size:22px; }

      @media (max-width:640px) {
        #ui-radar { width:96px; height:96px; }
        .ui-slot { width:42px; height:42px; }
        .ui-slot .sw { width:20px; height:20px; }
      }
    `;
    document.head.appendChild(s);
  }

  // =====================================================================
  // DOM 構築（一度だけ）
  // =====================================================================
  let dom = null;
  function buildDOM() {
    const root = el('div', '', document.body);
    root.id = 'ui-root';

    // 下部：ゲージ＋ホットバー
    const bottom = el('div', '', root); bottom.id = 'ui-bottom';
    const gauges = el('div', '', bottom); gauges.className = 'ui-gauges panel';

    const breathRow = el('div', 'display:none;', gauges); breathRow.className = 'ui-row';
    const breathSegs = el('div', '', breathRow); breathSegs.className = 'ui-segs';

    const foodRow = el('div', '', gauges); foodRow.className = 'ui-row';
    const foodSegs = el('div', '', foodRow); foodSegs.className = 'ui-segs';
    const foodNum = el('div', '', foodRow); foodNum.className = 'ui-num';

    const hpRow = el('div', '', gauges); hpRow.className = 'ui-row';
    const hpSegs = el('div', '', hpRow); hpSegs.className = 'ui-segs';
    const hpNum = el('div', '', hpRow); hpNum.className = 'ui-num';

    const selName = el('div', '', bottom); selName.id = 'ui-selname'; selName.className = 'panel';
    const hotbar = el('div', '', bottom); hotbar.id = 'ui-hotbar';

    // 右上：レーダー＋情報
    const radarWrap = el('div', '', root); radarWrap.id = 'ui-radar-wrap';
    const radar = el('canvas', '', radarWrap); radar.id = 'ui-radar';
    radar.width = 128; radar.height = 128;
    const info = el('div', '', radarWrap); info.id = 'ui-info'; info.className = 'panel';

    // 全画面ヴィネット
    const hurt = el('div', '', root); hurt.id = 'ui-hurt';
    const heal = el('div', '', root); heal.id = 'ui-heal';

    // ダメージFXレイヤー（HUD休止中でも動くよう root 直下に独立配置）
    const fxCanvas = el('canvas', '', document.body); fxCanvas.id = 'ui-fx-canvas';
    const fxLayer = el('div', '', document.body); fxLayer.id = 'ui-fx';

    dom = {
      root, breathRow, breathSegs, foodSegs, foodNum, hpSegs, hpNum,
      selName, hotbar, radar, rctx: radar.getContext('2d'), info, hurt, heal,
      fxCanvas, fxctx: fxCanvas.getContext('2d'), fxLayer,
      hpSegEls: [], foodSegEls: [], breathSegEls: [], slotEls: [],
    };
    resizeFX();
    window.addEventListener('resize', resizeFX);
  }

  function resizeFX() {
    if (!dom) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    dom.fxCanvas.width = Math.floor(innerWidth * dpr);
    dom.fxCanvas.height = Math.floor(innerHeight * dpr);
    dom.fxCanvas.style.width = innerWidth + 'px';
    dom.fxCanvas.style.height = innerHeight + 'px';
    dom.fxctx.setTransform(dpr, 0, 0, dpr, 0, 0); // 以降は CSS px で描ける
  }

  // セグメント列を必要数だけ用意して使い回す（毎フレーム再生成しない）
  function ensureSegs(container, store, count) {
    while (store.length < count) { const e = el('div', '', container); e.className = 'ui-seg'; store.push(e); }
    for (let i = 0; i < store.length; i++) store[i].style.display = i < count ? '' : 'none';
  }

  // n（=満タン2につき1段）の段表示。full/half/empty とクラスを付け替えるだけ
  function paintSegs(store, value, maxValue, fullCls, halfCls, lowAt) {
    const segCount = clampN(Math.ceil(maxValue / 2));
    const full = clampN(Math.floor(value / 2));
    const half = value - full * 2 >= 1;
    const low = value <= lowAt;
    for (let i = 0; i < segCount; i++) {
      const seg = store[i];
      if (!seg) continue;
      let cls = 'ui-seg';
      if (i < full) cls += ' ' + fullCls;
      else if (i === full && half) cls += ' ' + halfCls;
      if (low && i < Math.max(full + (half ? 1 : 0), 1)) cls += ' low';
      seg.className = cls;
    }
  }

  // =====================================================================
  // ホットバー描画（差分があるときだけ作り直す）
  // =====================================================================
  let hotbarSig = '';
  function paintHotbar(hotbar) {
    const sig = hotbar.map(h => `${h.block}:${h.count}:${h.active ? 1 : 0}`).join('|');
    if (sig === hotbarSig) return;
    hotbarSig = sig;

    // スロット要素を必要数だけ用意
    while (dom.slotEls.length < hotbar.length) {
      const slot = el('div', '', dom.hotbar); slot.className = 'ui-slot';
      const key = el('div', '', slot); key.className = 'key';
      const sw = el('div', '', slot); sw.className = 'sw';
      const cnt = el('div', '', slot); cnt.className = 'cnt';
      dom.slotEls.push({ slot, key, sw, cnt });
    }
    for (let i = 0; i < dom.slotEls.length; i++) {
      const ui = dom.slotEls[i], h = hotbar[i];
      if (!h) { ui.slot.style.display = 'none'; continue; }
      ui.slot.style.display = '';
      ui.slot.className = 'ui-slot' + (h.active ? ' active' : '');
      ui.key.textContent = (i + 1 <= 9) ? (i + 1) : '';
      ui.sw.style.background = h.swatch || '#888';
      ui.cnt.textContent = h.count;
      ui.cnt.className = 'cnt' + (h.count > 0 ? '' : ' zero');
      ui.slot.title = h.name || '';
    }
  }

  // =====================================================================
  // レーダーミニマップ（北を上にしたシンプル版・プレイヤー中心）
  // =====================================================================
  const RADAR_RANGE = 44; // 半径（ブロック）
  function paintRadar(st) {
    const ctx = dom.rctx, W = 128, R = W / 2, scale = (R - 8) / RADAR_RANGE;
    ctx.clearRect(0, 0, W, W);

    // 同心円グリッド
    ctx.strokeStyle = 'rgba(255,255,255,.12)'; ctx.lineWidth = 1;
    for (let r = (R - 8) / 2; r <= R - 8; r += (R - 8) / 2) {
      ctx.beginPath(); ctx.arc(R, R, r, 0, Math.PI * 2); ctx.stroke();
    }
    // 方位 N
    ctx.fillStyle = 'rgba(255,255,255,.5)'; ctx.font = 'bold 10px system-ui';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText('N', R, 9);

    // モブ blip（北上＝world +x→右, +z→下）
    const px = st.pos ? st.pos.x : 0, pz = st.pos ? st.pos.z : 0;
    const mobs = Array.isArray(st.mobs) ? st.mobs : [];
    for (const m of mobs) {
      const dx = (m.x - px) * scale, dz = (m.z - pz) * scale;
      if (dx * dx + dz * dz > (R - 8) * (R - 8)) continue; // 範囲外は出さない
      ctx.beginPath();
      ctx.arc(R + dx, R + dz, m.hostile ? 3.2 : 2.6, 0, Math.PI * 2);
      ctx.fillStyle = m.hostile ? '#ff4d5e' : (m.type === 'villager' ? '#6fe3ff' : '#9be86a');
      ctx.fill();
    }

    // プレイヤー（中心の向き付き三角）。yaw から進行方向の矢印を描く
    const yaw = st.yaw || 0;
    const fx = -Math.sin(yaw), fz = -Math.cos(yaw); // 前方ベクトル（北上座標へ投影）
    ctx.save();
    ctx.translate(R, R);
    ctx.rotate(Math.atan2(fx, -fz)); // 上向きを前方に
    ctx.beginPath(); ctx.moveTo(0, -6); ctx.lineTo(4.5, 5); ctx.lineTo(-4.5, 5); ctx.closePath();
    ctx.fillStyle = '#ffd54a'; ctx.fill();
    ctx.restore();
  }

  // =====================================================================
  // ダメージ／回復演出
  // =====================================================================
  let hurtT = 0, healT = 0, lastHp = null;
  function flashDamage(amount) {
    hurtT = Math.min(1, 0.45 + clamp01((amount || 1) / 12) * 0.55);
  }
  function flashHeal() { healT = 0.7; }

  // コアの既存フックに相乗り（コア改変不要）
  function hookDamage() {
    const prev = window.onPlayerHurt;
    window.onPlayerHurt = function (cause, amount) {
      try { if (typeof prev === 'function') prev(cause, amount); } catch (e) {}
      flashDamage(amount);
    };
  }

  // =====================================================================
  // ダメージポップ ＆ ヒットエフェクト
  //   ・口は ui.js が「定義」し、1号機（戦闘）が命中時に呼ぶ:
  //       window.spawnDamagePopup(x, y, z, amount, opts?)
  //       window.spawnHitEffect(x, y, z, opts?)
  //   ・world→screen 投影は window.VoxelGame.project(x,y,z) に依存。
  //     未定義でも安全（座標が画面内とみなせる時だけ描画、それ以外は黙って捨てる）。
  //   ・HUD（state()）が休止中でも、この演出だけは独立して動作する。
  // =====================================================================
  const popups = []; // {el, x, y, vy, life, ttl}
  const hits = [];   // {x, y, life, ttl, kind, ang}
  const MAX_POPUPS = 40, MAX_HITS = 40;

  // world(x,y,z) → screen{px,py,visible}。projector が無い場合は null
  function projectWorld(x, y, z) {
    const vg = window.VoxelGame;
    if (vg && typeof vg.project === 'function') {
      try {
        const p = vg.project(x, y, z);
        if (p && Number.isFinite(p.x) && Number.isFinite(p.y)) {
          return { px: p.x, py: p.y, visible: p.visible !== false };
        }
      } catch (e) {}
    }
    return null;
  }

  // 命中位置を画面座標に解決する。
  //   ・projector があればそれを使う（推奨）
  //   ・無くても opts.screen=true なら (x,y) を画面pxとして扱う
  //   ・どちらも不可なら null（＝安全に無効化）
  function resolveScreen(x, y, z, opts) {
    const p = projectWorld(x, y, z);
    if (p) return p.visible ? p : null;
    if (opts && opts.screen) return { px: x, py: y, visible: true };
    return null;
  }

  // ダメージ数字ポップ（命中位置からふわっと浮いて消える）
  function spawnDamagePopup(x, y, z, amount, opts) {
    opts = opts || {};
    if (!dom) return;
    const s = resolveScreen(x, y, z, opts);
    if (!s) return; // 画面外/投影不可は捨てる
    if (popups.length >= MAX_POPUPS) { const old = popups.shift(); if (old.el) old.el.remove(); }

    const amt = Math.round(Number(amount) || 0);
    const heal = opts.heal || amt < 0;
    const self = !!opts.self; // プレイヤー被ダメ
    const crit = !!opts.crit;
    const e = document.createElement('div');
    e.className = 'ui-pop ' + (heal ? 'heal' : self ? 'self' : crit ? 'crit' : 'dmg');
    e.textContent = (heal ? '+' + Math.abs(amt) : (crit ? '✦' + Math.abs(amt) : Math.abs(amt)));
    // 同一点の重なりを避けて少し横へ散らす（index で決め打ち＝乱数不使用）
    const jitter = ((popups.length % 5) - 2) * 9;
    e.style.left = (s.px + jitter) + 'px';
    e.style.top = s.py + 'px';
    dom.fxLayer.appendChild(e);
    popups.push({ el: e, x: s.px + jitter, y: s.py, vy: crit ? 64 : 48, life: 0, ttl: crit ? 1.1 : 0.85 });

    // 命中点の閃光も同時に（ヒットの手応え）
    spawnHitEffect(x, y, z, { screen: opts.screen, crit, kind: heal ? 'heal' : 'hit', _resolved: s });
    if (self) flashDamage(Math.abs(amt)); // プレイヤー被ダメは赤フラッシュと統合
  }

  // 命中点の一瞬の閃光／斬撃線
  function spawnHitEffect(x, y, z, opts) {
    opts = opts || {};
    if (!dom) return;
    const s = opts._resolved || resolveScreen(x, y, z, opts);
    if (!s) return;
    if (hits.length >= MAX_HITS) hits.shift();
    // 斬撃線の角度は呼び出し位置で散らす（乱数不使用＝決定的）
    const ang = ((hits.length * 47) % 180) * Math.PI / 180;
    hits.push({ x: s.px, y: s.py, life: 0, ttl: opts.crit ? 0.34 : 0.24, kind: opts.kind || 'hit', crit: !!opts.crit, ang });
  }

  // 毎フレーム：ポップの浮上フェード＆ヒット閃光の描画
  function stepFX(dt) {
    if (!dom) return;
    // --- ダメージ数字 ---
    for (let i = popups.length - 1; i >= 0; i--) {
      const p = popups[i];
      p.life += dt;
      const k = p.life / p.ttl;
      if (k >= 1) { if (p.el) p.el.remove(); popups.splice(i, 1); continue; }
      p.y -= p.vy * dt; p.vy *= (1 - dt * 1.6); // だんだん減速しながら上昇
      const pop = k < 0.18 ? 1 + (0.18 - k) * 1.6 : 1; // 出現時に少し膨らむ
      const op = k < 0.7 ? 1 : 1 - (k - 0.7) / 0.3;     // 後半でフェード
      p.el.style.top = p.y + 'px';
      p.el.style.opacity = clamp01(op).toFixed(3);
      p.el.style.transform = `translate(-50%,-50%) scale(${pop.toFixed(3)})`;
    }
    // --- ヒット閃光／斬撃線（canvas） ---
    const ctx = dom.fxctx;
    ctx.clearRect(0, 0, innerWidth, innerHeight);
    for (let i = hits.length - 1; i >= 0; i--) {
      const h = hits[i];
      h.life += dt;
      const k = h.life / h.ttl;
      if (k >= 1) { hits.splice(i, 1); continue; }
      const a = clamp01(1 - k);
      const r = (h.crit ? 26 : 16) * (0.4 + k * 1.3);
      ctx.save();
      ctx.translate(h.x, h.y);
      // 放射状の閃光リング
      ctx.globalAlpha = a * 0.9;
      ctx.strokeStyle = h.kind === 'heal' ? '#7cff9b' : (h.crit ? '#ffec5c' : '#fff2cc');
      ctx.lineWidth = h.crit ? 3 : 2;
      ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.stroke();
      // 斬撃線（クロス）
      ctx.globalAlpha = a;
      ctx.rotate(h.ang);
      const len = (h.crit ? 22 : 14) * (0.6 + k);
      ctx.beginPath(); ctx.moveTo(-len, 0); ctx.lineTo(len, 0); ctx.stroke();
      ctx.restore();
    }
  }

  // 口を公開（1号機が hit 時に呼ぶ）。安全に何度上書きされても無害
  function exposeFXHooks() {
    window.spawnDamagePopup = spawnDamagePopup;
    window.spawnHitEffect = spawnHitEffect;
    window.UI = window.UI || {};
    window.UI.spawnDamagePopup = spawnDamagePopup;
    window.UI.spawnHitEffect = spawnHitEffect;
  }

  // =====================================================================
  // メインループ
  // =====================================================================
  function readState() {
    try {
      if (window.VoxelGame && typeof window.VoxelGame.state === 'function') return window.VoxelGame.state();
    } catch (e) { /* state() が一時的に投げても描画を止めない */ }
    return null;
  }

  let warnedOnce = false, running = false, lastDt = 0;
  function tick(t) {
    requestAnimationFrame(tick);
    const dt = lastDt ? Math.min(0.05, (t - lastDt) / 1000) : 0.016; lastDt = t;

    // FX（ダメージポップ／ヒット閃光）は HUD の有無に関わらず常に駆動する
    stepFX(dt);

    const st = readState();
    if (!st) {
      if (!warnedOnce) {
        warnedOnce = true;
        console.info('[ui] 待機中: window.VoxelGame.state() 未実装のため HUD は休止します（UI_INTEGRATION.md (2) を参照）。FX口(spawnDamagePopup等)は有効です。');
      }
      if (dom) dom.root.style.display = 'none';
      return;
    }
    if (dom.root.style.display === 'none') dom.root.style.display = '';

    // --- ゲージ ---
    const maxHp = st.maxHp || 20, maxHunger = st.maxHunger || 20, maxBreath = st.maxBreath || 10;
    ensureSegs(dom.hpSegs, dom.hpSegEls, clampN(Math.ceil(maxHp / 2)));
    ensureSegs(dom.foodSegs, dom.foodSegEls, clampN(Math.ceil(maxHunger / 2)));
    paintSegs(dom.hpSegEls, clampN(st.hp), maxHp, 'f-hp', 'h-hp', 6);
    paintSegs(dom.foodSegEls, clampN(st.hunger), maxHunger, 'f-food', 'h-food', 4);
    dom.hpNum.textContent = `${clampN(st.hp)}/${maxHp}`;
    dom.foodNum.textContent = `${clampN(st.hunger)}/${maxHunger}`;

    // 息ゲージ（水中＝breath が満タン未満のときだけ）
    const showBreath = st.inWater || (typeof st.breath === 'number' && st.breath < maxBreath - 0.01);
    if (showBreath) {
      dom.breathRow.style.display = '';
      ensureSegs(dom.breathSegs, dom.breathSegEls, clampN(Math.ceil(maxBreath)));
      const b = clampN(Math.round(st.breath));
      for (let i = 0; i < dom.breathSegEls.length; i++) {
        const seg = dom.breathSegEls[i];
        seg.className = 'ui-seg' + (i < b ? ' f-air' : '') + (b <= 2 && i < Math.max(b, 1) ? ' low' : '');
      }
    } else {
      dom.breathRow.style.display = 'none';
    }

    // --- ホットバー＆選択名 ---
    const hotbar = Array.isArray(st.hotbar) ? st.hotbar : [];
    paintHotbar(hotbar);
    const sel = hotbar.find(h => h.active);
    dom.selName.textContent = sel ? `${sel.name}（所持 ${clampN(sel.count)}）` : '';

    // --- レーダー＆情報 ---
    paintRadar(st);
    const time = st.time || {};
    const hh = String(clampN(time.hh)).padStart(2, '0'), mm = String(clampN(time.mm)).padStart(2, '0');
    dom.info.innerHTML =
      `<span class="b">${hh}:${mm}</span> ${time.phase || ''} / ${st.weather || ''}<br>` +
      `${st.biome || ''}${st.riding ? ' 🐴騎乗' : ''}`;

    // --- 演出 ---
    if (lastHp != null && st.hp > lastHp + 0.01) flashHeal(); // HP増＝回復パルス
    lastHp = st.hp;
    hurtT = Math.max(0, hurtT - dt * 2.2);
    healT = Math.max(0, healT - dt * 1.6);
    dom.hurt.style.opacity = hurtT.toFixed(3);
    dom.heal.style.opacity = (healT * 0.9).toFixed(3);
  }

  // =====================================================================
  // 起動
  // =====================================================================
  function start() {
    if (running) return; running = true;
    injectStyle();
    buildDOM();
    hookDamage();
    exposeFXHooks(); // window.spawnDamagePopup / spawnHitEffect を公開
    requestAnimationFrame(tick);
    // 後続②③④ 用のUI口（現状は枠だけ）
    window.UI = window.UI || {};
    console.info('[ui] HUD＋FXレイヤー起動（3号機）。state()=HUD / spawnDamagePopup()=戦闘演出。');
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
