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

  // ---- アイコン（4号機 tools/icons/icon_*.png・128px透過PNG） -------------
  const ICON_BASE = 'tools/icons/';
  // state() entry.icon があれば最優先。無ければ日本語名→アイコン名でフォールバック。
  const NAME2ICON = {
    '草':'block_grass', '土':'block_dirt', '石':'block_stone', '原木':'block_wood',
    '葉':'block_leaves', '砂':'block_sand', '雪':null /* 未整備=スウォッチ */,
    '木材':'block_planks', '石レンガ':'block_stonebrick', 'ガラス':'block_glass',
    '肉':'item_meat', '卵':'item_egg', 'コイン':'item_coin', 'りんご':'item_apple',
  };
  function iconUrl(entry) {
    if (!entry) return null;
    const base = entry.icon || NAME2ICON[entry.name];
    return base ? ICON_BASE + 'icon_' + base + '.png' : null;
  }
  // コア統合済み（state()が生えている）かどうか。②のEキー有効化のゲートに使う
  function coreIntegrated() { return !!(window.VoxelGame && typeof window.VoxelGame.state === 'function'); }
  // 操作口（読み取りのみの原則のもと、状態変更はコアの口経由でのみ行う）
  function callSelect(block) {
    const vg = window.VoxelGame;
    if (vg && typeof vg.selectBlock === 'function') { try { vg.selectBlock(block); return true; } catch (e) {} }
    return false;
  }
  function callCraft(index) {
    const vg = window.VoxelGame;
    if (vg && typeof vg.craft === 'function') { try { vg.craft(index); return true; } catch (e) {} }
    return false;
  }

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

      /* スロット内アイコン（4号機 128px PNG） */
      .ui-slot .ic { width:30px; height:30px; image-rendering:auto;
        filter:drop-shadow(0 1px 1px rgba(0,0,0,.5)); pointer-events:none; }

      /* ② インベントリ／クラフト画面 */
      #ui-inv { position:fixed; inset:0; z-index:30; display:none; pointer-events:auto;
        align-items:center; justify-content:center; background:rgba(8,14,26,.82);
        backdrop-filter:blur(3px); }
      #ui-inv.open { display:flex; }
      .uiv-panel { width:min(720px,92vw); max-height:88vh; overflow:auto; color:#fff;
        background:linear-gradient(180deg, rgba(28,38,58,.96), rgba(18,26,42,.96));
        border:1px solid rgba(255,255,255,.14); border-radius:14px; padding:18px 20px;
        box-shadow:0 18px 60px rgba(0,0,0,.5); }
      .uiv-head { display:flex; align-items:center; justify-content:space-between; margin-bottom:12px; }
      .uiv-title { font-size:18px; font-weight:800; letter-spacing:1px; }
      .uiv-x { pointer-events:auto; cursor:pointer; border:1px solid rgba(255,255,255,.25);
        border-radius:8px; padding:4px 10px; font-size:13px; opacity:.85; }
      .uiv-x:hover { opacity:1; background:rgba(255,255,255,.08); }
      .uiv-sec { font-size:13px; opacity:.8; margin:14px 0 8px; border-bottom:1px solid rgba(255,255,255,.1); padding-bottom:4px; }
      .uiv-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(74px,1fr)); gap:8px; }
      .uiv-cell { position:relative; cursor:pointer; border:2px solid rgba(255,255,255,.16);
        border-radius:10px; padding:8px 4px 6px; text-align:center; transition:border-color .1s, transform .1s, background .1s; }
      .uiv-cell:hover { border-color:rgba(255,255,255,.5); background:rgba(255,255,255,.06); transform:translateY(-2px); }
      .uiv-cell.active { border-color:#ffd54a; box-shadow:0 0 12px rgba(255,213,74,.5); }
      .uiv-cell.empty { opacity:.4; }
      .uiv-cell .ic { width:44px; height:44px; margin:0 auto 4px; display:block; }
      .uiv-cell .sw { width:40px; height:40px; margin:0 auto 4px; border-radius:6px; border:1px solid rgba(0,0,0,.3); }
      .uiv-cell .nm { font-size:11px; line-height:1.2; }
      .uiv-cell .ct { position:absolute; right:5px; top:4px; font-size:12px; font-weight:bold; text-shadow:0 0 2px #000,0 0 2px #000; }
      .uiv-craft { display:grid; grid-template-columns:repeat(auto-fill, minmax(150px,1fr)); gap:8px; }
      .uiv-recipe { pointer-events:auto; cursor:pointer; text-align:left; color:#fff;
        border:2px solid rgba(255,255,255,.16); border-radius:10px; padding:8px 10px;
        background:rgba(0,0,0,.25); display:flex; align-items:center; gap:8px; transition:.1s; }
      .uiv-recipe:hover:not(:disabled) { border-color:#9be86a; background:rgba(60,120,40,.3); }
      .uiv-recipe:disabled { opacity:.4; cursor:not-allowed; }
      .uiv-recipe .ic, .uiv-recipe .sw { width:32px; height:32px; border-radius:6px; flex:0 0 auto; }
      .uiv-recipe .rt { font-size:12px; line-height:1.35; }
      .uiv-recipe .rt b { font-size:13px; }
      #ui-tip { position:fixed; z-index:32; pointer-events:none; display:none; max-width:220px;
        background:rgba(0,0,0,.9); color:#fff; border:1px solid rgba(255,255,255,.2); border-radius:7px;
        padding:6px 9px; font-size:12px; line-height:1.4; box-shadow:0 4px 16px rgba(0,0,0,.5); }
      #ui-hint { position:fixed; right:14px; bottom:14px; z-index:16; color:#fff; font-size:12px;
        opacity:.7; text-shadow:0 0 3px #000; pointer-events:none; }

      @media (max-width:640px) {
        #ui-radar { width:96px; height:96px; }
        .ui-slot { width:42px; height:42px; }
        .ui-slot .sw, .ui-slot .ic { width:20px; height:20px; }
        .uiv-panel { padding:14px; }
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

    // ② インベントリ／クラフト画面（pointer-events を持つので body 直下）
    const inv = el('div', '', document.body); inv.id = 'ui-inv';
    const panel = el('div', '', inv); panel.className = 'uiv-panel';
    inv.addEventListener('click', (e) => { if (e.target === inv) closeInv(); }); // 背景クリックで閉じる
    const tip = el('div', '', document.body); tip.id = 'ui-tip';
    const hint = el('div', 'display:none;', document.body); hint.id = 'ui-hint';
    hint.textContent = 'E：インベントリ';

    dom = {
      root, breathRow, breathSegs, foodSegs, foodNum, hpSegs, hpNum,
      selName, hotbar, radar, rctx: radar.getContext('2d'), info, hurt, heal,
      fxCanvas, fxctx: fxCanvas.getContext('2d'), fxLayer,
      inv, panel, tip, hint,
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
      const ic = el('img', 'display:none;', slot); ic.className = 'ic'; ic.alt = '';
      ic.addEventListener('error', () => { ic.style.display = 'none'; sw.style.display = ''; }); // 取得失敗はスウォッチに退避
      const cnt = el('div', '', slot); cnt.className = 'cnt';
      dom.slotEls.push({ slot, key, sw, ic, cnt });
    }
    for (let i = 0; i < dom.slotEls.length; i++) {
      const ui = dom.slotEls[i], h = hotbar[i];
      if (!h) { ui.slot.style.display = 'none'; continue; }
      ui.slot.style.display = '';
      ui.slot.className = 'ui-slot' + (h.active ? ' active' : '');
      ui.key.textContent = (i + 1 <= 9) ? (i + 1) : '';
      const url = iconUrl(h);
      if (url) { if (ui.ic.getAttribute('src') !== url) ui.ic.src = url; ui.ic.style.display = ''; ui.sw.style.display = 'none'; }
      else { ui.ic.style.display = 'none'; ui.sw.style.display = ''; ui.sw.style.background = h.swatch || '#888'; }
      ui.cnt.textContent = h.count;
      ui.cnt.className = 'cnt' + (h.count > 0 ? '' : ' zero');
      ui.slot.title = h.name || '';
    }
  }

  // =====================================================================
  // ② インベントリ／クラフト画面（方針A：コア改修不要・クリック選択＋クラフト）
  //   ・状態は state() から読む。選択/クラフトは VoxelGame.selectBlock/craft 経由。
  //   ・Eキーでの開閉は「コア統合済み(state()有)」のときだけ有効化し、
  //     コア内蔵インベントリとの二重オープンを避ける（dormant-safe）。
  // =====================================================================
  let invOpen = false, invSig = '';
  function buildTip(html) {
    dom.tip.innerHTML = html; dom.tip.style.display = 'block';
  }
  function moveTip(ev) {
    if (dom.tip.style.display !== 'block') return;
    const pad = 14, w = dom.tip.offsetWidth, h = dom.tip.offsetHeight;
    let x = ev.clientX + pad, y = ev.clientY + pad;
    if (x + w > innerWidth) x = ev.clientX - w - pad;
    if (y + h > innerHeight) y = ev.clientY - h - pad;
    dom.tip.style.left = Math.max(0, x) + 'px'; dom.tip.style.top = Math.max(0, y) + 'px';
  }
  function hideTip() { dom.tip.style.display = 'none'; }

  // セル/レシピ要素を作る共通部品（アイコン or スウォッチ）
  function fillIcon(holder, entry) {
    const url = iconUrl(entry);
    if (url) {
      const img = el('img', '', holder); img.className = 'ic'; img.src = url; img.alt = '';
      img.addEventListener('error', () => { img.replaceWith(swatchEl(entry)); });
    } else holder.appendChild(swatchEl(entry));
  }
  function swatchEl(entry) {
    const d = document.createElement('div'); d.className = 'sw';
    d.style.background = (entry && entry.swatch) || '#888'; return d;
  }

  function renderInventory(st) {
    // 差分が無ければ作り直さない（開いている間だけ更新）
    const sig = JSON.stringify({
      h: (st.hotbar || []).map(x => [x.block, x.count, x.active ? 1 : 0]),
      it: (st.items || []).map(x => [x.key, x.count]),
      r: (st.recipes || []).map(x => x.canCraft ? 1 : 0),
    });
    if (sig === invSig) return;
    invSig = sig;
    const p = dom.panel; p.innerHTML = '';

    const head = el('div', '', p); head.className = 'uiv-head';
    const title = el('div', '', head); title.className = 'uiv-title'; title.textContent = '🎒 インベントリ ／ クラフト';
    const x = el('div', '', head); x.className = 'uiv-x'; x.textContent = '✕ 閉じる（E / Esc）';
    x.addEventListener('click', closeInv);

    // ブロック（クリックで選択）
    el('div', '', p).className = 'uiv-sec';
    p.lastChild.textContent = 'ブロック（クリックで選択）';
    const grid = el('div', '', p); grid.className = 'uiv-grid';
    (st.hotbar || []).forEach((h, i) => {
      const cell = el('div', '', grid);
      cell.className = 'uiv-cell' + (h.active ? ' active' : '') + (h.count > 0 ? '' : ' empty');
      fillIcon(cell, h);
      const nm = el('div', '', cell); nm.className = 'nm'; nm.textContent = h.name;
      const ct = el('div', '', cell); ct.className = 'ct'; ct.textContent = h.count;
      cell.addEventListener('mouseenter', () => buildTip(`<b>${h.name}</b><br>所持 ${clampN(h.count)}　/　数字キー ${i + 1 <= 9 ? i + 1 : '-'}<br><span style="opacity:.7">クリックで選択</span>`));
      cell.addEventListener('mousemove', moveTip);
      cell.addEventListener('mouseleave', hideTip);
      cell.addEventListener('click', () => {
        if (callSelect(h.block)) { window.playSFX && window.playSFX('place'); }
        invSig = ''; // 即時に選択枠を反映
      });
    });

    // アイテム（ドロップ品・表示のみ）
    el('div', '', p).className = 'uiv-sec';
    p.lastChild.textContent = 'アイテム（モブのドロップ品）';
    const igrid = el('div', '', p); igrid.className = 'uiv-grid';
    (st.items || []).forEach((it) => {
      const cell = el('div', '', igrid);
      cell.className = 'uiv-cell' + (it.count > 0 ? '' : ' empty');
      cell.style.cursor = 'default';
      fillIcon(cell, { name: it.name, icon: ('item_' + it.key) });
      const nm = el('div', '', cell); nm.className = 'nm'; nm.textContent = it.name;
      const ct = el('div', '', cell); ct.className = 'ct'; ct.textContent = it.count;
      cell.addEventListener('mouseenter', () => buildTip(`<b>${it.name}</b><br>所持 ${clampN(it.count)}`));
      cell.addEventListener('mousemove', moveTip);
      cell.addEventListener('mouseleave', hideTip);
    });

    // クラフト（資源変換）
    el('div', '', p).className = 'uiv-sec';
    p.lastChild.textContent = 'クラフト（資源を変換・クリックで作成）';
    const cgrid = el('div', '', p); cgrid.className = 'uiv-craft';
    (st.recipes || []).forEach((r, i) => {
      const btn = el('button', '', cgrid); btn.className = 'uiv-recipe'; btn.disabled = !r.canCraft;
      fillIcon(btn, { name: r.outName, icon: r.outIcon });
      const rt = el('div', '', btn); rt.className = 'rt';
      rt.innerHTML = `<b>${r.outName} ×${r.n}</b><br><span style="opacity:.8">${r.inName} ×${r.cost} → 作る</span>`;
      btn.addEventListener('mouseenter', () => buildTip(r.canCraft ? `<b>${r.outName}</b> を作成<br>${r.inName} ×${r.cost} を消費` : `素材不足：${r.inName} ×${r.cost} が必要`));
      btn.addEventListener('mousemove', moveTip);
      btn.addEventListener('mouseleave', hideTip);
      btn.addEventListener('click', () => { if (!btn.disabled) { callCraft(i); invSig = ''; } });
    });
  }

  function openInv() {
    if (invOpen) return;
    invOpen = true; invSig = '';
    dom.inv.classList.add('open');
    if (document.pointerLockElement) document.exitPointerLock(); // マウス操作のためロック解除
  }
  function closeInv() {
    if (!invOpen) return;
    invOpen = false; hideTip();
    dom.inv.classList.remove('open');
  }
  function toggleInv() { invOpen ? closeInv() : openInv(); }

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

    // --- ② インベントリ（開いている間だけ内容を更新）＋ 操作ヒント ---
    if (invOpen) renderInventory(st);
    dom.hint.style.display = (coreIntegrated() && !invOpen) ? '' : 'none';
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

    // UI操作口（1号機はEキー処理から window.UI.toggle('inventory') を呼ぶ＝委譲）
    window.UI = window.UI || {};
    window.UI.open = (which) => { window.UI._routed = true; if (!which || which === 'inventory') openInv(); };
    window.UI.close = () => { closeInv(); };
    window.UI.toggle = (which) => { window.UI._routed = true; if (!which || which === 'inventory') toggleInv(); };
    window.UI.spawnDamagePopup = spawnDamagePopup;
    window.UI.spawnHitEffect = spawnHitEffect;

    // フォールバックのEキー（コアが委譲し始めたら _routed=true で自動停止＝二重起動回避）
    window.addEventListener('keydown', (e) => {
      if (e.code === 'Escape' && invOpen) { closeInv(); return; }
      if (e.code === 'KeyE') {
        if (window.UI._routed) return;     // コアがEを委譲済み → ui.js側は触らない
        if (!coreIntegrated()) return;     // 統合前はコア内蔵インベントリに任せる
        toggleInv();
      }
    });

    console.info('[ui] HUD＋FX＋インベントリ起動（3号機）。state()=HUD / spawnDamagePopup()=戦闘演出 / UI.toggle("inventory")。');
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
