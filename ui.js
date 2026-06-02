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
    '葉':'block_leaves', '砂':'block_sand', '雪':'block_snow',
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

      /* ③ メニュー／設定／セーブスロット */
      #ui-menu { position:fixed; inset:0; z-index:31; display:none; pointer-events:auto;
        align-items:center; justify-content:center; background:rgba(8,14,26,.86); backdrop-filter:blur(3px); }
      #ui-menu.open { display:flex; }
      .uim-panel { width:min(560px,92vw); max-height:90vh; overflow:auto; color:#fff;
        background:linear-gradient(180deg, rgba(28,38,58,.97), rgba(16,24,40,.97));
        border:1px solid rgba(255,255,255,.14); border-radius:16px; padding:22px 24px;
        box-shadow:0 20px 70px rgba(0,0,0,.55); }
      .uim-title { font-size:22px; font-weight:800; letter-spacing:2px; text-align:center; margin-bottom:4px; }
      .uim-sub { font-size:12px; opacity:.7; text-align:center; margin-bottom:18px; }
      .uim-btns { display:flex; flex-direction:column; gap:10px; }
      .uim-btn { pointer-events:auto; cursor:pointer; text-align:center; color:#fff; font-size:15px;
        border:1px solid rgba(255,255,255,.22); border-radius:10px; padding:12px; background:rgba(255,255,255,.05);
        transition:.12s; }
      .uim-btn:hover { background:rgba(255,255,255,.13); border-color:rgba(255,255,255,.5); transform:translateY(-1px); }
      .uim-btn.primary { background:linear-gradient(180deg,#3a7bd5,#2c5fb0); border-color:#5a9bff; }
      .uim-btn.danger:hover { background:rgba(190,40,40,.35); border-color:#ff7a7a; }
      .uim-row { display:flex; align-items:center; gap:12px; margin:14px 0; }
      .uim-row label { flex:0 0 96px; font-size:13px; opacity:.9; }
      .uim-row input[type=range] { flex:1; accent-color:#ffd54a; }
      .uim-row .val { flex:0 0 44px; text-align:right; font-size:12px; opacity:.85; font-variant-numeric:tabular-nums; }
      .uim-row select { flex:1; background:rgba(0,0,0,.35); color:#fff; border:1px solid rgba(255,255,255,.25);
        border-radius:8px; padding:6px; }
      .uim-back { margin-top:18px; text-align:center; }
      .uim-slot { border:1px solid rgba(255,255,255,.16); border-radius:12px; padding:12px 14px; margin-bottom:10px;
        background:rgba(255,255,255,.04); }
      .uim-slot.cur { border-color:#ffd54a; box-shadow:0 0 10px rgba(255,213,74,.35); }
      .uim-slot .sh { display:flex; align-items:center; justify-content:space-between; }
      .uim-slot .sn { font-size:15px; font-weight:700; }
      .uim-slot .sm { font-size:11px; opacity:.75; margin-top:3px; line-height:1.5; }
      .uim-slot .sa { display:flex; gap:6px; margin-top:8px; }
      .uim-slot .sa button { pointer-events:auto; cursor:pointer; font-size:12px; color:#fff;
        border:1px solid rgba(255,255,255,.25); border-radius:7px; padding:5px 10px; background:rgba(0,0,0,.25); transition:.1s; }
      .uim-slot .sa button:hover { background:rgba(255,255,255,.12); }
      .uim-slot .sa button.danger:hover { background:rgba(190,40,40,.4); border-color:#ff7a7a; }
      .uim-mute { display:flex; align-items:center; gap:8px; font-size:13px; margin:6px 0 2px; cursor:pointer; }

      /* ④ スマホ向けタッチUI（タッチ端末のみ表示） */
      #ui-touch { position:fixed; inset:0; z-index:17; pointer-events:none; display:none; touch-action:none; }
      #ui-touch.on { display:block; }
      #ui-look { position:fixed; inset:0; z-index:14; pointer-events:auto; touch-action:none; } /* 視点ドラッグ捕捉（最下層） */
      #ui-stick { position:fixed; left:22px; bottom:22px; width:128px; height:128px; border-radius:50%;
        background:radial-gradient(circle, rgba(255,255,255,.10), rgba(0,0,0,.22)); border:2px solid rgba(255,255,255,.22);
        pointer-events:auto; touch-action:none; }
      #ui-knob { position:absolute; left:50%; top:50%; width:54px; height:54px; margin:-27px 0 0 -27px; border-radius:50%;
        background:radial-gradient(circle at 40% 35%, #fff, #c9d4e2); box-shadow:0 2px 8px rgba(0,0,0,.5); }
      .ui-tbtns { position:fixed; right:20px; bottom:24px; display:grid; gap:12px; pointer-events:none;
        grid-template-columns:repeat(2,72px); grid-template-areas:'place jump' 'attack jump'; }
      .ui-tbtn { pointer-events:auto; touch-action:none; user-select:none; -webkit-user-select:none;
        width:72px; height:72px; border-radius:50%; border:2px solid rgba(255,255,255,.3);
        background:rgba(20,30,48,.5); color:#fff; font-size:12px; font-weight:700; display:flex;
        flex-direction:column; align-items:center; justify-content:center; gap:2px; backdrop-filter:blur(2px); }
      .ui-tbtn .e { font-size:22px; line-height:1; }
      .ui-tbtn.press { transform:scale(.92); background:rgba(70,110,170,.6); border-color:#9bc1ff; }
      .ui-tbtn.jump { grid-area:jump; width:84px; height:84px; }
      .ui-tbtn.attack { grid-area:attack; }
      .ui-tbtn.place { grid-area:place; }
      .ui-ttop { position:fixed; left:14px; top:14px; display:flex; gap:10px; pointer-events:none; } /* 右上はレーダーのため左上へ */
      .ui-ttop .ui-tbtn { width:50px; height:50px; }
      .ui-ttop .ui-tbtn .e { font-size:20px; }
      .ui-tdash { position:fixed; left:26px; bottom:160px; }
      .ui-tdash .ui-tbtn { width:56px; height:56px; }
      .ui-tdash .ui-tbtn.on { background:rgba(255,170,40,.55); border-color:#ffd54a; }

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

    // ③ メニュー／設定／スロット
    const menu = el('div', '', document.body); menu.id = 'ui-menu';
    const menuPanel = el('div', '', menu); menuPanel.className = 'uim-panel';
    menu.addEventListener('click', (e) => { if (e.target === menu) closeMenu(); });

    dom = {
      root, breathRow, breathSegs, foodSegs, foodNum, hpSegs, hpNum,
      selName, hotbar, radar, rctx: radar.getContext('2d'), info, hurt, heal,
      fxCanvas, fxctx: fxCanvas.getContext('2d'), fxLayer,
      inv, panel, tip, hint, menu, menuPanel,
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
  // ③ メニュー／設定／セーブスロット
  //   ・音量 = 2号機 window.setMasterVolume 他（SoundSettings）に配線
  //   ・スロット = 1号機 window.VoxelGame.list/switchSlot/newWorld/deleteSlot に配線
  //   ・感度/画質 = localStorage 永続＋ window.UI_SETTINGS 公開（コアが読めば反映）
  // =====================================================================
  let menuOpen = false, menuScreen = 'menu';
  const SETTINGS_KEY = 'voxel_ui_settings_v1';
  function loadUiSettings() { try { return JSON.parse(localStorage.getItem(SETTINGS_KEY)) || {}; } catch (e) { return {}; } }
  const uiSettings = Object.assign({ sensitivity: 1.0, quality: 'high' }, loadUiSettings());
  function publishSettings() {
    window.UI_SETTINGS = uiSettings;
    try { localStorage.setItem(SETTINGS_KEY, JSON.stringify(uiSettings)); } catch (e) {}
    try { window.dispatchEvent(new CustomEvent('uisettingschange', { detail: uiSettings })); } catch (e) {}
  }

  const hasAudio = () => typeof window.setMasterVolume === 'function';
  const hasSlots = () => !!(window.VoxelGame && typeof window.VoxelGame.list === 'function');

  // スライダー行（0..1 を %表示）。oninput で即反映＋値表示
  function sliderRow(parent, label, get, set) {
    const row = el('div', '', parent); row.className = 'uim-row';
    const lb = el('label', '', row); lb.textContent = label;
    const inp = el('input', '', row); inp.type = 'range'; inp.min = '0'; inp.max = '100'; inp.step = '1';
    const val = el('div', '', row); val.className = 'val';
    const v = clamp01(get()); inp.value = String(Math.round(v * 100)); val.textContent = Math.round(v * 100) + '%';
    inp.addEventListener('input', () => { const f = clampN(inp.value) / 100; val.textContent = Math.round(f * 100) + '%'; try { set(f); } catch (e) {} });
    return inp;
  }

  function renderSettings(p) {
    el('div', '', p).className = 'uim-title'; p.lastChild.textContent = '⚙ 設定';
    el('div', '', p).className = 'uim-sub'; p.lastChild.textContent = '音量は即時反映・感度/画質は保存されます';

    // --- 音量（2号機 SoundSettings へ配線）---
    el('div', '', p).className = 'uiv-sec'; p.lastChild.textContent = '音量';
    if (hasAudio()) {
      sliderRow(p, 'マスター', () => window.getMasterVolume ? window.getMasterVolume() : 1, (v) => window.setMasterVolume(v));
      if (window.setSfxVolume) sliderRow(p, '効果音', () => window.getSfxVolume ? window.getSfxVolume() : 1, (v) => window.setSfxVolume(v));
      if (window.setBgmVolume) sliderRow(p, 'BGM', () => window.getBgmVolume ? window.getBgmVolume() : 0.6, (v) => window.setBgmVolume(v));
      const mute = el('label', '', p); mute.className = 'uim-mute';
      const cb = el('input', '', mute); cb.type = 'checkbox';
      try { cb.checked = !!(window.SoundSettings && window.SoundSettings.get().muted); } catch (e) {}
      mute.appendChild(document.createTextNode(' ミュート'));
      cb.addEventListener('change', () => { if (window.setMuted) window.setMuted(cb.checked); });
    } else {
      const n = el('div', 'font-size:12px;opacity:.7;', p); n.textContent = '※ 音声システム未読込（sound.js 読込後に有効）';
    }

    // --- 操作・表示（感度/画質：localStorage＋UI_SETTINGS）---
    el('div', '', p).className = 'uiv-sec'; p.lastChild.textContent = '操作・表示';
    const sr = el('div', '', p); sr.className = 'uim-row';
    el('label', '', sr).textContent = 'マウス感度';
    const si = el('input', '', sr); si.type = 'range'; si.min = '30'; si.max = '250'; si.step = '5';
    si.value = String(Math.round(uiSettings.sensitivity * 100));
    const sv = el('div', '', sr); sv.className = 'val'; sv.textContent = (uiSettings.sensitivity).toFixed(2) + '×';
    si.addEventListener('input', () => { uiSettings.sensitivity = clampN(si.value) / 100; sv.textContent = uiSettings.sensitivity.toFixed(2) + '×'; publishSettings(); });

    const qr = el('div', '', p); qr.className = 'uim-row';
    el('label', '', qr).textContent = '画質';
    const qs = el('select', '', qr);
    [['high', '高（標準）'], ['low', '軽量（スマホ向け）']].forEach(([v, t]) => { const o = el('option', '', qs); o.value = v; o.textContent = t; });
    qs.value = uiSettings.quality;
    qs.addEventListener('change', () => { uiSettings.quality = qs.value; publishSettings(); });

    const back = el('div', '', p); back.className = 'uim-back';
    const b = el('div', '', back); b.className = 'uim-btn'; b.textContent = '← 戻る'; b.addEventListener('click', () => renderMenu('menu'));
  }

  // 破壊的操作の二段確認（確定/取消に化ける）
  function confirmBtn(holder, label, danger, onYes) {
    const b = el('button', '', holder); b.textContent = label; if (danger) b.className = 'danger';
    b.addEventListener('click', () => {
      b.textContent = '確定?'; b.className = danger ? 'danger' : '';
      const cancel = el('button', '', holder); cancel.textContent = '取消';
      const t = setTimeout(() => { b.textContent = label; cancel.remove(); }, 2600);
      const yes = () => { clearTimeout(t); onYes(); };
      b.onclick = yes;
      cancel.addEventListener('click', () => { clearTimeout(t); b.textContent = label; b.onclick = null; cancel.remove(); });
    }, { once: true });
  }

  function renderSlots(p) {
    el('div', '', p).className = 'uim-title'; p.lastChild.textContent = '💾 セーブ＆ロード';
    el('div', '', p).className = 'uim-sub'; p.lastChild.textContent = '切替・新規・削除はページが再読込されます';
    if (!hasSlots()) { const n = el('div', 'font-size:13px;opacity:.7;', p); n.textContent = '※ セーブ口未読込（VoxelGame 統合後に有効）'; }
    else {
      let list = []; try { list = window.VoxelGame.list() || []; } catch (e) {}
      const cur = (() => { try { return window.VoxelGame.current(); } catch (e) { return 1; } })();
      list.forEach((s) => {
        const card = el('div', '', p); card.className = 'uim-slot' + (s.current || s.slot === cur ? ' cur' : '');
        const head = el('div', '', card); head.className = 'sh';
        const nm = el('div', '', head); nm.className = 'sn';
        nm.textContent = `スロット ${s.slot}` + ((s.current || s.slot === cur) ? '（使用中）' : '');
        const meta = el('div', '', card); meta.className = 'sm';
        if (s.exists) {
          const when = s.ts ? new Date(s.ts).toLocaleString('ja-JP') : '—';
          const hh = (typeof s.dayTime === 'number') ? String(Math.floor(((s.dayTime + 0.5) % 1) * 24)).padStart(2, '0') + '時' : '—';
          meta.textContent = `更新 ${when} ／ 改変 ${clampN(s.editCount)} ・ モブ ${clampN(s.mobCount)} ・ HP ${s.hp != null ? s.hp : '—'} ・ ${hh}`;
        } else meta.textContent = '（空きスロット）';
        const act = el('div', '', card); act.className = 'sa';
        if (!(s.current || s.slot === cur)) confirmBtn(act, s.exists ? '▶ このデータで開始' : '＋ 新規作成', false, () => {
          try { s.exists ? window.VoxelGame.switchSlot(s.slot) : window.VoxelGame.newWorld(s.slot); } catch (e) {}
        });
        if (s.exists) confirmBtn(act, '🗑 削除', true, () => { try { window.VoxelGame.deleteSlot(s.slot); } catch (e) {} renderMenu('slots'); });
      });
    }
    const back = el('div', '', p); back.className = 'uim-back';
    const b = el('div', '', back); b.className = 'uim-btn'; b.textContent = '← 戻る'; b.addEventListener('click', () => renderMenu('menu'));
  }

  function renderMenuRoot(p) {
    el('div', '', p).className = 'uim-title'; p.lastChild.textContent = '⏸ メニュー';
    el('div', '', p).className = 'uim-sub'; p.lastChild.textContent = 'VOXEL WORLD';
    const btns = el('div', '', p); btns.className = 'uim-btns';
    const mk = (label, cls, fn) => { const b = el('div', '', btns); b.className = 'uim-btn' + (cls ? ' ' + cls : ''); b.textContent = label; b.addEventListener('click', fn); };
    mk('▶ ゲームに戻る', 'primary', closeMenu);
    mk('⚙ 設定', '', () => renderMenu('settings'));
    mk('💾 セーブ＆ロード', '', () => renderMenu('slots'));
    mk('💾 今すぐ保存', '', () => { try { window.VoxelGame && window.VoxelGame.save && window.VoxelGame.save(); } catch (e) {} const b = btns.lastChild; b.textContent = '✓ 保存しました'; setTimeout(() => { b.textContent = '💾 今すぐ保存'; }, 1200); });
  }

  function renderMenu(screen) {
    menuScreen = screen;
    const p = dom.menuPanel; p.innerHTML = '';
    if (screen === 'settings') renderSettings(p);
    else if (screen === 'slots') renderSlots(p);
    else renderMenuRoot(p);
  }
  function openMenu(screen) {
    menuOpen = true; renderMenu(screen || 'menu');
    dom.menu.classList.add('open');
    if (document.pointerLockElement) document.exitPointerLock();
  }
  function closeMenu() { menuOpen = false; dom.menu.classList.remove('open'); }

  // =====================================================================
  // ④ スマホ向けタッチUI（タッチ端末のみ表示・PC操作は不変）
  //   ・移動/ジャンプ/ダッシュ … 合成キー(WASD/Space/Shift)で即動作（コア改修不要）
  //   ・視点/破壊(攻撃)/設置 … window.VoxelGame.input.{look,primary,secondary} に配線
  //     （ポインタロックが使えないスマホでは合成マウス不可のため。未提供なら安全に無効）
  // =====================================================================
  let touchOn = false, stickId = null, lookId = null, lookLast = null, dashOn = false;
  const stickVec = { x: 0, z: 0 };
  const heldKeys = new Set();
  function isTouchDevice() { return ('ontouchstart' in window) || (navigator.maxTouchPoints > 0); }
  function synth(code, down) { try { document.dispatchEvent(new KeyboardEvent(down ? 'keydown' : 'keyup', { code, bubbles: true })); } catch (e) {} }
  function setKey(code, down) {
    if (down) { if (!heldKeys.has(code)) { heldKeys.add(code); synth(code, true); } }
    else { if (heldKeys.has(code)) { heldKeys.delete(code); synth(code, false); } }
  }
  const coreInput = () => (window.VoxelGame && window.VoxelGame.input) || null;
  function inputAct(name, arg) { const i = coreInput(); if (i && typeof i[name] === 'function') { try { i[name](arg); return true; } catch (e) {} } return false; }

  function applyStick() {
    const i = coreInput();
    if (i && typeof i.move === 'function') { try { i.move(stickVec.x, stickVec.z); } catch (e) {} return; }
    setKey('KeyW', stickVec.z < -0.35); setKey('KeyS', stickVec.z > 0.35);
    setKey('KeyA', stickVec.x < -0.35); setKey('KeyD', stickVec.x > 0.35);
  }

  function buildTouch() {
    // 視点ドラッグ捕捉層（最下層・タッチ時のみ表示）。PCでは display:none でクリックを邪魔しない
    const look = el('div', 'display:none;', document.body); look.id = 'ui-look';
    const cont = el('div', '', document.body); cont.id = 'ui-touch';
    const stick = el('div', '', cont); stick.id = 'ui-stick';
    const knob = el('div', '', stick); knob.id = 'ui-knob';
    const tbtns = el('div', '', cont); tbtns.className = 'ui-tbtns';
    const mkBtn = (parent, cls, emoji, label) => {
      const b = el('div', '', parent); b.className = 'ui-tbtn ' + cls;
      const e = el('div', '', b); e.className = 'e'; e.textContent = emoji;
      if (label) { const t = el('div', '', b); t.textContent = label; }
      return b;
    };
    const jump = mkBtn(tbtns, 'jump', '⬆', 'ジャンプ');
    const attack = mkBtn(tbtns, 'attack', '⚔', '攻撃/破壊');
    const place = mkBtn(tbtns, 'place', '⛏', '設置');
    const dashWrap = el('div', '', cont); dashWrap.className = 'ui-tdash';
    const dash = mkBtn(dashWrap, '', '🏃', 'ダッシュ');
    const top = el('div', '', cont); top.className = 'ui-ttop';
    const invBtn = mkBtn(top, '', '🎒');
    const menuBtn = mkBtn(top, '', '⏸');
    dom.touch = cont; dom.look = look; dom.stick = stick; dom.knob = knob;

    // --- ジョイスティック ---
    function moveKnob(e) {
      const r = stick.getBoundingClientRect();
      let dx = e.clientX - (r.left + r.width / 2), dy = e.clientY - (r.top + r.height / 2);
      const max = r.width / 2, d = Math.hypot(dx, dy) || 1, cl = Math.min(d, max);
      dx = dx / d * cl; dy = dy / d * cl;
      knob.style.transform = `translate(${dx}px,${dy}px)`;
      stickVec.x = dx / max; stickVec.z = dy / max; applyStick();
    }
    stick.addEventListener('pointerdown', (e) => { e.preventDefault(); stickId = e.pointerId; try { stick.setPointerCapture(e.pointerId); } catch (x) {} moveKnob(e); });
    stick.addEventListener('pointermove', (e) => { if (e.pointerId === stickId) moveKnob(e); });
    const endStick = (e) => { if (e.pointerId === stickId) { stickId = null; stickVec.x = 0; stickVec.z = 0; knob.style.transform = 'translate(0,0)'; setKey('KeyW', false); setKey('KeyS', false); setKey('KeyA', false); setKey('KeyD', false); applyStick(); } };
    stick.addEventListener('pointerup', endStick); stick.addEventListener('pointercancel', endStick);

    // --- 視点ドラッグ ---
    look.addEventListener('pointerdown', (e) => { lookId = e.pointerId; lookLast = { x: e.clientX, y: e.clientY }; });
    look.addEventListener('pointermove', (e) => {
      if (e.pointerId !== lookId || !lookLast) return;
      const dx = e.clientX - lookLast.x, dy = e.clientY - lookLast.y; lookLast = { x: e.clientX, y: e.clientY };
      inputAct('look', dx); // 1引数版を試しつつ…
      const i = coreInput(); if (i && typeof i.look === 'function') { try { i.look(dx, dy); } catch (x) {} }
    });
    const endLook = (e) => { if (e.pointerId === lookId) { lookId = null; lookLast = null; } };
    look.addEventListener('pointerup', endLook); look.addEventListener('pointercancel', endLook);

    // --- アクションボタン ---
    function holdBtn(elm, onDown, onUp) {
      const d = (e) => { e.preventDefault(); elm.classList.add('press'); onDown && onDown(); };
      const u = (e) => { e.preventDefault(); elm.classList.remove('press'); onUp && onUp(); };
      elm.addEventListener('pointerdown', d); elm.addEventListener('pointerup', u);
      elm.addEventListener('pointercancel', u); elm.addEventListener('pointerleave', u);
    }
    function tapBtn(elm, fn) { elm.addEventListener('pointerdown', (e) => { e.preventDefault(); elm.classList.add('press'); }); elm.addEventListener('pointerup', (e) => { e.preventDefault(); elm.classList.remove('press'); fn(); }); }
    holdBtn(jump, () => setKey('Space', true), () => setKey('Space', false));
    holdBtn(attack, () => inputAct('primary', true), () => inputAct('primary', false));
    holdBtn(place, () => inputAct('secondary', true), () => inputAct('secondary', false));
    tapBtn(dash, () => { dashOn = !dashOn; dash.classList.toggle('on', dashOn); setKey('ShiftLeft', dashOn); });
    tapBtn(invBtn, () => { window.UI._routed = true; toggleInv(); });
    tapBtn(menuBtn, () => { window.UI._routed = true; menuOpen ? closeMenu() : openMenu('menu'); });
  }

  function setTouchMode(on) {
    touchOn = on;
    if (!dom.touch) return;
    dom.touch.classList.toggle('on', on);
    dom.look.style.display = on ? 'block' : 'none';
    if (on) dom.hint.style.display = 'none'; // スマホではキーヒントを出さない
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

    // --- ② インベントリ（開いている間だけ内容を更新）＋ 操作ヒント ---
    if (invOpen) renderInventory(st);
    dom.hint.style.display = (coreIntegrated() && !invOpen && !touchOn) ? '' : 'none';

    // --- ④ input.move 提供時は傾けっぱなしでも毎フレーム移動を送る ---
    if (touchOn && stickId !== null) { const i = coreInput(); if (i && typeof i.move === 'function') applyStick(); }
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

    publishSettings(); // window.UI_SETTINGS を起動時に公開（コアが感度/画質を読めるように）

    // UI操作口（1号機はEキー処理から window.UI.toggle('inventory')、Escから open('menu') を呼ぶ＝委譲）
    window.UI = window.UI || {};
    window.UI.open = (which) => {
      window.UI._routed = true;
      if (which === 'menu' || which === 'settings' || which === 'slots') openMenu(which === 'menu' ? 'menu' : which);
      else openInv();
    };
    window.UI.close = () => { closeInv(); closeMenu(); };
    window.UI.toggle = (which) => {
      window.UI._routed = true;
      if (which === 'menu') { menuOpen ? closeMenu() : openMenu('menu'); }
      else toggleInv();
    };
    window.UI.spawnDamagePopup = spawnDamagePopup;
    window.UI.spawnHitEffect = spawnHitEffect;
    window.UI.settings = () => uiSettings;
    window.UI.setTouch = (b) => setTouchMode(!!b);

    // タッチUIの構築＋端末判定（PCは非表示・操作不変）
    buildTouch();
    setTouchMode(isTouchDevice());
    // 初回タッチで未判定端末でも有効化（ハイブリッド端末対策）
    window.addEventListener('touchstart', function onFirstTouch() {
      if (!touchOn) setTouchMode(true);
      window.removeEventListener('touchstart', onFirstTouch);
    }, { passive: true });

    // フォールバックのEキー（コアが委譲し始めたら _routed=true で自動停止＝二重起動回避）
    window.addEventListener('keydown', (e) => {
      if (e.code === 'Escape') {
        if (menuOpen) { closeMenu(); return; }
        if (invOpen) { closeInv(); return; }
      }
      if (e.code === 'KeyE') {
        if (window.UI._routed) return;     // コアがEを委譲済み → ui.js側は触らない
        if (!coreIntegrated()) return;     // 統合前はコア内蔵インベントリに任せる
        if (menuOpen) return;
        toggleInv();
      }
    });

    console.info('[ui] HUD＋FX＋インベントリ起動（3号機）。state()=HUD / spawnDamagePopup()=戦闘演出 / UI.toggle("inventory")。');
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
