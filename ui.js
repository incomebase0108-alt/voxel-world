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
    'ひまわりの種':'item_himawari',
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
        font-family: system-ui, -apple-system, "Segoe UI", sans-serif; color:#fff; user-select:none;
        -webkit-font-smoothing:antialiased; }
      #ui-root .panel { text-shadow:0 0 3px #000, 0 0 3px #000; }
      /* オーバーレイ共通：フェード＋パネルのスケール（開閉トランジション） */
      #ui-inv, #ui-menu { -webkit-font-smoothing:antialiased; }
      #ui-inv, #ui-menu { opacity:0; visibility:hidden; pointer-events:none;
        transition:opacity .18s ease, visibility .18s ease; }
      #ui-inv.open, #ui-menu.open { opacity:1; visibility:visible; pointer-events:auto; }
      .uiv-panel, .uim-panel { transform:scale(.94) translateY(8px); opacity:.6;
        transition:transform .22s cubic-bezier(.2,.9,.25,1), opacity .22s ease; }
      #ui-inv.open .uiv-panel, #ui-menu.open .uim-panel { transform:scale(1) translateY(0); opacity:1; }

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
      .ui-pop.crit { color:#ffec5c; font-size:40px; letter-spacing:1px;
        text-shadow:0 0 10px #ff7a00, 0 0 18px #ff5a00, 0 2px 3px #000; }
      .ui-pop.heal { color:#7cff9b; font-size:18px; }
      .ui-pop.self { color:#ff6b6b; font-size:22px; }

      /* Lv/EXP バー（ホットバーの上） */
      .ui-exp { display:flex; align-items:center; gap:7px; }
      .ui-explv { font-size:12px; font-weight:800; color:#d8ffb0; min-width:44px; text-align:right; }
      .ui-expbar { position:relative; width:240px; height:9px; border-radius:6px; overflow:hidden;
        background:rgba(0,0,0,.4); border:1px solid rgba(255,255,255,.18); }
      .ui-expfill { position:absolute; inset:0 auto 0 0; width:0%; transition:width .2s ease-out;
        background:linear-gradient(90deg,#5ec24a,#b6f36a); box-shadow:0 0 6px rgba(140,240,90,.5); }
      .ui-expnum { font-size:10px; opacity:.7; min-width:54px; }

      /* レベルアップ祝祭バナー */
      #ui-levelup { position:fixed; left:50%; top:36%; transform:translate(-50%,-50%) scale(.6);
        z-index:28; pointer-events:none; text-align:center; opacity:0; }
      #ui-levelup .lu1 { font-size:42px; font-weight:900; letter-spacing:3px; color:#ffe24a;
        text-shadow:0 0 14px #ff9d00, 0 2px 5px #000; }
      #ui-levelup .lu2 { font-size:24px; font-weight:800; color:#fff; text-shadow:0 0 8px #000; margin-top:6px; }

      /* 必殺技：装備スキルボタン＋必殺ゲージ */
      #ui-skills { position:fixed; right:14px; bottom:92px; display:flex; gap:8px; z-index:16; pointer-events:auto; }
      .ui-skill { position:relative; width:54px; height:54px; border-radius:13px; overflow:hidden; cursor:pointer;
        border:2px solid rgba(150,190,255,.45); background:rgba(18,28,52,.55); display:flex; align-items:center; justify-content:center;
        box-shadow:0 0 10px rgba(80,140,255,.2); transition:transform .12s, box-shadow .12s; }
      .ui-skill.ready { border-color:#7fd0ff; box-shadow:0 0 16px rgba(120,200,255,.6); }
      .ui-skill.ready:hover { transform:translateY(-3px); }
      .ui-skill:not(.ready) { filter:grayscale(.55) brightness(.66); cursor:default; }
      .ui-skill .ic, .ui-skill .sw { width:34px; height:34px; }
      .ui-skill .cd { position:absolute; left:0; right:0; bottom:0; background:rgba(0,0,0,.62); pointer-events:none; }
      .ui-skill .key { position:absolute; left:4px; top:2px; font-size:10px; color:#cfe6ff; text-shadow:0 0 2px #000; font-weight:700; }
      #ui-ult { position:fixed; right:14px; bottom:78px; width:178px; height:7px; border-radius:5px; overflow:hidden;
        background:rgba(0,0,0,.42); border:1px solid rgba(255,255,255,.2); z-index:16; display:none; }
      #ui-ultfill { position:absolute; inset:0 auto 0 0; width:0%; transition:width .18s ease-out;
        background:linear-gradient(90deg,#5a9bff,#b58cff,#ff7ad0); }
      #ui-ult.full #ui-ultfill { animation:ui-ultglow 1s ease-in-out infinite; }
      @keyframes ui-ultglow { 0%,100%{ filter:brightness(1) } 50%{ filter:brightness(1.7) } }

      /* スキル名／習得バナー */
      #ui-skillname { position:fixed; left:50%; top:30%; transform:translate(-50%,-50%) scale(.7);
        z-index:29; pointer-events:none; text-align:center; opacity:0; }
      #ui-skillname .s1 { font-size:48px; font-weight:900; letter-spacing:5px; text-shadow:0 0 20px currentColor, 0 3px 7px #000; }
      #ui-skillname .s2 { font-size:18px; font-weight:800; color:#fff; text-shadow:0 0 8px #000; margin-top:5px; letter-spacing:2px; }

      /* ボスHPバー（画面上部中央・通常モブと別格） */
      #ui-boss { position:fixed; left:50%; top:18px; transform:translateX(-50%);
        width:min(680px,72vw); z-index:23; pointer-events:none; display:none;
        flex-direction:column; align-items:center; gap:4px; text-align:center; }
      #ui-boss .bn { font-size:20px; font-weight:900; letter-spacing:2px; color:#fff;
        text-shadow:0 0 10px #ff2a3e, 0 2px 4px #000; display:flex; align-items:center; gap:7px; }
      #ui-boss .bn::before { content:'☠'; font-size:18px; color:#ff5a6e; text-shadow:0 0 8px #ff2a3e; }
      #ui-boss-pips { display:flex; gap:4px; }
      #ui-boss-pips .pip { width:9px; height:9px; border-radius:50%; background:rgba(255,255,255,.18);
        border:1px solid rgba(0,0,0,.5); }
      #ui-boss-pips .pip.on { background:#ffd54a; box-shadow:0 0 6px #ffb300; }
      #ui-boss-track { position:relative; width:100%; height:16px; border-radius:9px; overflow:hidden;
        background:rgba(0,0,0,.55); border:2px solid rgba(255,255,255,.28);
        box-shadow:0 2px 12px rgba(0,0,0,.55), 0 0 10px rgba(255,30,50,.28); }
      #ui-boss-fill { position:absolute; inset:0 auto 0 0; width:100%;
        background:linear-gradient(90deg,#7a0010,#ff2a3e 70%,#ff6a78);
        transition:width .25s cubic-bezier(.3,.9,.4,1); }
      #ui-boss-track::after { content:''; position:absolute; inset:0; pointer-events:none;
        background:repeating-linear-gradient(90deg,transparent 0 calc(10% - 1px),rgba(0,0,0,.32) calc(10% - 1px) 10%); }
      #ui-boss-num { position:absolute; inset:0; display:flex; align-items:center; justify-content:center;
        font-size:11px; font-weight:800; color:#fff; text-shadow:0 0 3px #000,0 1px 2px #000; }
      #ui-boss.low #ui-boss-track { animation:ui-boss-pulse .6s ease-in-out infinite; }
      @keyframes ui-boss-pulse { 0%,100%{ box-shadow:0 2px 12px rgba(0,0,0,.55),0 0 8px rgba(255,30,50,.4) }
        50%{ box-shadow:0 2px 12px rgba(0,0,0,.55),0 0 22px rgba(255,30,50,.95) } }
      /* ボス出現/撃破バナー */
      #ui-boss-banner { position:fixed; left:50%; top:24%; transform:translate(-50%,-50%) scale(.7);
        z-index:29; pointer-events:none; opacity:0; font-size:40px; font-weight:900; letter-spacing:4px;
        color:#ff5a6e; text-shadow:0 0 20px currentColor, 0 3px 7px #000; white-space:nowrap; }

      /* 構造物 発見トースト（上部中央・ボスバーの下に積む） */
      #ui-toast-wrap { position:fixed; left:50%; top:64px; transform:translateX(-50%);
        z-index:22; pointer-events:none; display:flex; flex-direction:column; align-items:center; gap:7px; }
      .ui-toast { display:flex; align-items:center; gap:9px; padding:8px 16px; border-radius:11px;
        background:rgba(10,16,28,.78); backdrop-filter:blur(3px); border:2px solid #fff;
        font-size:15px; font-weight:800; color:#fff; text-shadow:0 1px 2px #000; white-space:nowrap;
        will-change:transform,opacity; }
      .ui-toast .tg { font-size:19px; line-height:1; }
      .ui-toast .tl { font-size:10px; opacity:.7; font-weight:700; margin-left:2px; }

      /* 照準（クロスヘア）— ui.js が確実に最前面・高コントラストで出す。
         一人称/三人称どちらでもプレイ中は常に画面中央に表示。 */
      /* body 直下に出すので z-index はグローバル。FX層(#ui-fx-canvas:26 / #ui-fx:27) より上に。
         inv(30)/menu(31)/tip(32) より下だが、それらが開く間は gameActive()=false で照準を消すので競合しない。 */
      #ui-cross { position:fixed; left:50%; top:50%; transform:translate(-50%,-50%);
        width:26px; height:26px; z-index:29; pointer-events:none; opacity:0; transition:opacity .1s; }
      #ui-cross.on { opacity:.95; }
      #ui-cross i { position:absolute; background:#fff; border-radius:1px;
        box-shadow:0 0 0 1px rgba(0,0,0,.9), 0 0 4px rgba(0,0,0,.85); }
      #ui-cross .v { width:2px; height:8px; left:50%; transform:translateX(-50%); }
      #ui-cross .vt { top:0; } #ui-cross .vb { bottom:0; }
      #ui-cross .h { height:2px; width:8px; top:50%; transform:translateY(-50%); }
      #ui-cross .hl { left:0; } #ui-cross .hr { right:0; }
      #ui-cross .dot { width:2px; height:2px; left:50%; top:50%;
        transform:translate(-50%,-50%); border-radius:50%; }

      /* スキル選択カード */
      .uik-card { display:flex; align-items:center; gap:12px; border:2px solid rgba(255,255,255,.16); border-radius:12px;
        padding:10px 12px; margin-bottom:8px; background:rgba(0,0,0,.22); cursor:pointer; transition:.12s; }
      .uik-card.eq { border-color:#7fd0ff; box-shadow:0 0 12px rgba(120,200,255,.35); background:rgba(40,70,120,.3); }
      .uik-card:hover { background:rgba(255,255,255,.06); }
      .uik-card .ic, .uik-card .sw { width:42px; height:42px; border-radius:10px; flex:0 0 auto; }
      .uik-card .info { flex:1; }
      .uik-card .nm { font-size:15px; font-weight:800; }
      .uik-card .ds { font-size:11px; opacity:.75; margin-top:2px; }
      .uik-card .eqtag { font-size:11px; color:#7fd0ff; font-weight:800; flex:0 0 auto; }

      /* スロット内アイコン（4号機 128px PNG） */
      .ui-slot .ic { width:30px; height:30px; image-rendering:auto;
        filter:drop-shadow(0 1px 1px rgba(0,0,0,.5)); pointer-events:none; }

      /* ② インベントリ／クラフト画面 */
      #ui-inv { position:fixed; inset:0; z-index:30; display:flex;
        align-items:center; justify-content:center; background:rgba(8,14,26,.82);
        backdrop-filter:blur(3px); }
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
      #ui-tip .tip-eff { display:block; margin-top:3px; color:#bfe6ff; font-weight:600; } /* ① アイテム効果の強調行 */
      #ui-hint { position:fixed; right:14px; bottom:14px; z-index:16; color:#fff; font-size:12px;
        opacity:.7; text-shadow:0 0 3px #000; pointer-events:none; }

      /* equip デバッグ表示（剣のworld向き・盾のworld Y を一目で）。getEquipDebug() があれば自動点灯 */
      #ui-equipdbg { position:fixed; left:12px; top:12px; z-index:16; pointer-events:none; display:none;
        font-family: ui-monospace, "SFMono-Regular", Menlo, Consolas, monospace; font-size:11px; line-height:1.55;
        color:#cfe6ff; background:rgba(8,14,26,.62); border:1px solid rgba(120,180,255,.32);
        border-radius:8px; padding:6px 9px; text-shadow:0 0 3px #000, 0 0 3px #000; white-space:nowrap; }
      #ui-equipdbg .t { font-weight:700; color:#9bd1ff; letter-spacing:.5px; }
      #ui-equipdbg .k { opacity:.72; }
      #ui-equipdbg .dim { opacity:.42; }
      #ui-equipdbg .ok { color:#9be86a; }
      #ui-equipdbg .ng { color:#ff8a8a; }

      /* ③ メニュー／設定／セーブスロット */
      #ui-menu { position:fixed; inset:0; z-index:31; display:flex;
        align-items:center; justify-content:center; background:rgba(8,14,26,.86); backdrop-filter:blur(3px); }
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
      /* 視点スワイプは画面右半分のみ捕捉（左半分は移動パッド／誤操作回避のため空ける）。最下層 */
      #ui-look { position:fixed; left:40%; right:0; top:0; bottom:0; z-index:14; pointer-events:auto; touch-action:none; }
      #ui-stick { position:fixed; left:22px; bottom:22px; width:128px; height:128px; border-radius:50%;
        background:radial-gradient(circle, rgba(255,255,255,.10), rgba(0,0,0,.22)); border:2px solid rgba(255,255,255,.22);
        pointer-events:auto; touch-action:none; }
      #ui-knob { position:absolute; left:50%; top:50%; width:54px; height:54px; margin:-27px 0 0 -27px; border-radius:50%;
        background:radial-gradient(circle at 40% 35%, #fff, #c9d4e2); box-shadow:0 2px 8px rgba(0,0,0,.5); }
      /* 右下：攻撃を主役（大）に、ジャンプ/設置を左へ小さく配置 */
      .ui-tbtns { position:fixed; right:18px; bottom:22px; display:grid; gap:10px; align-items:end; pointer-events:none;
        grid-template-columns:auto auto; grid-template-areas:'place attack' 'jump attack'; }
      .ui-tbtn { position:relative; pointer-events:auto; touch-action:none; user-select:none; -webkit-user-select:none;
        width:64px; height:64px; border-radius:50%; border:2px solid rgba(255,255,255,.3);
        background:rgba(20,30,48,.5); color:#fff; font-size:11px; font-weight:700; display:flex;
        flex-direction:column; align-items:center; justify-content:center; gap:2px; backdrop-filter:blur(2px); }
      .ui-tbtn .e { font-size:21px; line-height:1; }
      .ui-tbtn.press { transform:scale(.92); background:rgba(70,110,170,.6); border-color:#9bc1ff; }
      .ui-tbtn.jump { grid-area:jump; width:72px; height:72px; }
      .ui-tbtn.place { grid-area:place; }
      .ui-tbtn.attack { grid-area:attack; align-self:end; width:96px; height:96px;
        background:rgba(150,40,52,.5); border-color:rgba(255,160,170,.5); }
      .ui-tbtn.attack .e { font-size:32px; }
      .ui-tbtn.attack.press { background:rgba(200,60,72,.62); border-color:#ff9aa6; }
      /* 弓溜め（長押し）の充填リング。攻撃ボタンを押し続けると放射する */
      .ui-tbtn.attack .chg { position:absolute; inset:-5px; border-radius:50%; border:3px solid #ffd54a;
        opacity:0; transform:scale(.78); pointer-events:none; }
      .ui-tbtn.attack.charging .chg { animation:ui-bowchg .8s ease-out infinite; }
      @keyframes ui-bowchg { 0%{ opacity:0; transform:scale(.78) } 35%{ opacity:.95 } 100%{ opacity:0; transform:scale(1.28) } }
      .ui-ttop { position:fixed; left:14px; top:14px; display:flex; gap:10px; pointer-events:none; } /* 右上はレーダーのため左上へ */
      .ui-ttop .ui-tbtn { width:50px; height:50px; }
      .ui-ttop .ui-tbtn .e { font-size:20px; }
      .ui-tdash { position:fixed; left:26px; bottom:160px; }
      .ui-tdash .ui-tbtn { width:56px; height:56px; }
      .ui-tdash .ui-tbtn.on { background:rgba(255,170,40,.55); border-color:#ffd54a; }

      /* ① 仲間ステータス（左中央・最大3人・state().companions が来たら自動点灯） */
      #ui-companions { position:fixed; left:12px; top:84px; z-index:16; display:none;
        flex-direction:column; gap:8px; width:188px; pointer-events:none; }
      #ui-companions.on { display:flex; }
      .ui-comp { pointer-events:auto; background:rgba(8,14,26,.46); border:2px solid rgba(255,255,255,.18);
        border-radius:10px; padding:6px 8px 7px; backdrop-filter:blur(2px); box-shadow:0 2px 8px rgba(0,0,0,.35);
        transition:opacity .2s, transform .2s; }
      .ui-comp.dead { opacity:.5; filter:grayscale(.7); }
      .ui-comp-top { display:flex; align-items:center; gap:7px; }
      .ui-comp-ava { width:30px; height:30px; flex:0 0 auto; border-radius:7px; background:rgba(255,255,255,.1);
        border:1px solid rgba(0,0,0,.35); display:flex; align-items:center; justify-content:center;
        font-size:18px; background-size:cover; background-position:center; }
      .ui-comp-mid { flex:1 1 auto; min-width:0; }
      .ui-comp-name { font-size:13px; font-weight:800; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
        text-shadow:0 0 3px #000,0 0 3px #000; }
      .ui-comp-hpbar { height:7px; border-radius:4px; margin-top:3px; background:rgba(255,255,255,.14);
        overflow:hidden; box-shadow:0 0 2px rgba(0,0,0,.6) inset; }
      .ui-comp-hpfill { height:100%; width:100%; border-radius:4px; background:#46d36a; transition:width .18s, background .18s; }
      .ui-comp-hpfill.mid { background:#f3c23a; } .ui-comp-hpfill.low { background:#ff4d5e; }
      .ui-comp-hpnum { font-size:10px; opacity:.8; margin-top:1px; }
      .ui-comp-cmds { display:flex; gap:4px; margin-top:6px; }
      .ui-comp-cmd { pointer-events:auto; cursor:pointer; flex:1 1 0; text-align:center; font-size:11px; font-weight:700;
        padding:3px 0; border-radius:6px; border:1px solid rgba(255,255,255,.2); background:rgba(255,255,255,.06);
        transition:background .12s, border-color .12s; }
      .ui-comp-cmd:hover { background:rgba(255,255,255,.14); }
      .ui-comp-cmd.on { background:rgba(70,150,255,.5); border-color:#9bc1ff; color:#fff; box-shadow:0 0 8px rgba(80,150,255,.5); }
      .ui-comp-cmd .cg { font-size:12px; }

      /* NPC会話／取引 */
      .uit-npc { display:flex; align-items:center; gap:10px; margin-bottom:4px; }
      .uit-ava { width:40px; height:40px; border-radius:50%; background:rgba(255,255,255,.12);
        display:flex; align-items:center; justify-content:center; font-size:22px; flex:0 0 auto; }
      .uit-name { font-size:17px; font-weight:800; }
      .uit-job { font-size:11px; opacity:.7; }
      .uit-say { background:rgba(0,0,0,.28); border-left:3px solid #ffd54a; border-radius:6px;
        padding:9px 12px; font-size:13px; line-height:1.5; margin:8px 0 4px; }
      .uit-offer { pointer-events:auto; cursor:pointer; display:flex; align-items:center; gap:10px;
        border:2px solid rgba(255,255,255,.16); border-radius:10px; padding:9px 12px; margin-bottom:8px;
        background:rgba(0,0,0,.22); transition:.12s; width:100%; color:#fff; text-align:left; }
      .uit-offer:hover:not(:disabled) { border-color:#9be86a; background:rgba(60,120,40,.28); transform:translateY(-1px); }
      .uit-offer:disabled { opacity:.42; cursor:not-allowed; }
      .uit-side { display:flex; align-items:center; gap:6px; min-width:78px; }
      .uit-side .ic, .uit-side .sw { width:30px; height:30px; border-radius:6px; flex:0 0 auto; }
      .uit-side .q { font-size:13px; font-weight:700; }
      .uit-arrow { font-size:18px; opacity:.8; flex:0 0 auto; }
      .uit-get { flex:1; justify-content:flex-end; }
      .uit-none { font-size:13px; opacity:.7; padding:8px 0; }
      .uit-offer { flex-wrap:wrap; } /* ② 効果キャプションを2行目に回す */
      .uit-eff { flex-basis:100%; font-size:11px; color:#bfe6ff; opacity:.92; margin-top:3px; font-weight:600; text-align:left; }
      /* ④ ステータス画面 */
      .uist { display:flex; flex-direction:column; gap:6px; margin:8px 0; }
      .uist-row { display:flex; justify-content:space-between; align-items:center; gap:12px; padding:7px 11px;
        background:rgba(255,255,255,.06); border:1px solid rgba(255,255,255,.1); border-radius:8px; }
      .uist-row .k { font-size:13px; opacity:.85; } .uist-row .v { font-size:14px; font-weight:800; }
      /* ③ ゲームオーバー画面（dormant：core が window.onPlayerDeath を呼ぶと表示） */
      #ui-gameover { position:fixed; inset:0; z-index:40; display:none; flex-direction:column; align-items:center;
        justify-content:center; gap:12px; text-align:center; color:#fff;
        background:radial-gradient(circle at 50% 38%, rgba(70,0,0,.74), rgba(0,0,0,.93)); }
      #ui-gameover.show { display:flex; }
      #ui-gameover .got { font-size:46px; font-weight:900; letter-spacing:4px; color:#ff5a5a; text-shadow:0 0 22px rgba(255,40,40,.6); }
      #ui-gameover .gosub { font-size:14px; opacity:.85; }
      #ui-gameover .gostats { display:flex; flex-direction:column; gap:5px; margin:6px 0; font-size:15px; }
      #ui-gameover .gobtn { pointer-events:auto; cursor:pointer; margin-top:10px; padding:13px 32px; font-size:17px;
        font-weight:800; border-radius:12px; border:2px solid rgba(150,220,150,.6); background:rgba(50,130,60,.55); color:#fff; }
      #ui-gameover .gobtn:hover { background:rgba(70,160,75,.65); transform:translateY(-1px); }
      /* ③ 会話中の「仲間にする」ボタン（trade パネル内・PC/スマホ共通） */
      .uit-recruit { pointer-events:auto; cursor:pointer; width:100%; margin-top:10px; padding:11px 12px;
        display:flex; align-items:center; justify-content:center; gap:8px; font-size:14px; font-weight:800;
        border-radius:10px; border:2px solid rgba(120,230,120,.5); background:rgba(50,120,50,.32); color:#fff; }
      .uit-recruit:hover:not(:disabled) { border-color:#9be86a; background:rgba(70,150,60,.42); transform:translateY(-1px); }
      .uit-recruit:disabled { opacity:.5; cursor:not-allowed; border-color:rgba(255,255,255,.2); background:rgba(255,255,255,.08); }
      .uit-recruit .e { font-size:18px; line-height:1; }
      .uit-recruit .sub { font-size:11px; font-weight:600; opacity:.85; }
      /* ② スマホ：NPC接近時に出る「話す」ボタン（左サム圏・スティック上） */
      .ui-ttalk { position:fixed; left:26px; bottom:230px; display:none; }
      .ui-ttalk.show { display:block; }
      .ui-ttalk .ui-tbtn { width:64px; height:64px; background:rgba(40,90,150,.55); border-color:rgba(150,200,255,.6); }
      .ui-ttalk .ui-tbtn .e { font-size:24px; }

      @media (max-width:640px) {
        #ui-radar { width:96px; height:96px; }
        .ui-slot { width:42px; height:42px; }
        .ui-slot .sw, .ui-slot .ic { width:20px; height:20px; }
        .uiv-panel { padding:14px; }
        #ui-boss { width:88vw; top:10px; }
        #ui-boss .bn { font-size:16px; }
        #ui-boss-banner { font-size:28px; }
        #ui-toast-wrap { top:54px; }
        .ui-toast { font-size:13px; padding:6px 12px; }
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
    // Lv/EXP バー（state().level がある時だけ表示）
    const expRow = el('div', 'display:none;', bottom); expRow.className = 'ui-exp panel';
    const explv = el('div', '', expRow); explv.className = 'ui-explv';
    const expbar = el('div', '', expRow); expbar.className = 'ui-expbar';
    const expfill = el('div', '', expbar); expfill.className = 'ui-expfill';
    const expnum = el('div', '', expRow); expnum.className = 'ui-expnum';
    const hotbar = el('div', '', bottom); hotbar.id = 'ui-hotbar';

    // 右上：レーダー＋情報
    const radarWrap = el('div', '', root); radarWrap.id = 'ui-radar-wrap';
    const radar = el('canvas', '', radarWrap); radar.id = 'ui-radar';
    radar.width = 128; radar.height = 128;
    const info = el('div', '', radarWrap); info.id = 'ui-info'; info.className = 'panel';

    // equip デバッグ表示（剣のworld向き・盾のworld Y）。getEquipDebug() があれば自動点灯
    const equipdbg = el('div', '', root); equipdbg.id = 'ui-equipdbg';

    // 全画面ヴィネット
    const hurt = el('div', '', root); hurt.id = 'ui-hurt';
    const heal = el('div', '', root); heal.id = 'ui-heal';

    // レベルアップ祝祭バナー
    const levelup = el('div', '', root); levelup.id = 'ui-levelup';
    const lu1 = el('div', '', levelup); lu1.className = 'lu1'; lu1.textContent = '⭐ LEVEL UP!';
    const lu2 = el('div', '', levelup); lu2.className = 'lu2';

    // 必殺技：装備スキルボタン＋必殺ゲージ＋発動/習得バナー
    const skills = el('div', '', root); skills.id = 'ui-skills';
    const ult = el('div', '', root); ult.id = 'ui-ult';
    const ultfill = el('div', '', ult); ultfill.id = 'ui-ultfill';
    const skillname = el('div', '', root); skillname.id = 'ui-skillname';
    const sk1 = el('div', '', skillname); sk1.className = 's1';
    const sk2 = el('div', '', skillname); sk2.className = 's2';

    // ボスHPバー（画面上部中央・通常モブと別格）＋出現/撃破バナー
    const boss = el('div', '', root); boss.id = 'ui-boss';
    const bossName = el('div', '', boss); bossName.className = 'bn';
    const bossPips = el('div', '', boss); bossPips.id = 'ui-boss-pips';
    const bossTrack = el('div', '', boss); bossTrack.id = 'ui-boss-track';
    const bossFill = el('div', '', bossTrack); bossFill.id = 'ui-boss-fill';
    const bossNum = el('div', '', bossTrack); bossNum.id = 'ui-boss-num';
    const bossBan = el('div', '', root); bossBan.id = 'ui-boss-banner';

    // 構造物 発見トースト（上部中央スタック）
    const toastWrap = el('div', '', root); toastWrap.id = 'ui-toast-wrap';

    // ① 仲間ステータス（左中央・最大3人）。state().companions が来たら自動点灯
    const companions = el('div', '', root); companions.id = 'ui-companions';

    // 照準（クロスヘア）— 4本の腕＋中央ドット。プレイ中は常に最前面・中央。
    // ※ body 直下に置く。root(z-15) はスタッキングコンテキストを作るため、root の子だと
    //   どんな z-index でも実効的に z-15 へ閉じ込められ、body 直下の FX 層(z-26/27) に覆われて
    //   照準が見えなくなる（前回の「照準が出ない」不具合の根因）。body 直下なら z-index が素直に効く。
    const cross = el('div', '', document.body); cross.id = 'ui-cross';
    el('i', '', cross).className = 'v vt'; el('i', '', cross).className = 'v vb';
    el('i', '', cross).className = 'h hl'; el('i', '', cross).className = 'h hr';
    el('i', '', cross).className = 'dot';

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
      inv, panel, tip, hint, menu, menuPanel, equipdbg,
      expRow, explv, expfill, expnum, levelup, lu2,
      boss, bossName, bossPips, bossTrack, bossFill, bossNum, bossBan, bossPipN: -1,
      toastWrap, cross, companions, compCards: [],
      skills, ult, ultfill, skillname, sk1, sk2, skillEls: [],
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
  // 必殺技 HUD（装備スキルボタン＋必殺ゲージ）。state().skills がある時だけ表示
  //   skills = { energy?:0..1, equipped?:[id], list:[{id,name,icon,kind,desc,ready,cooldown}] }
  //   cooldown は「残り割合 0..1」（1=出来たて, 0=使用可）。ready 優先。
  // =====================================================================
  const SKILL_KEYS = ['Z', 'X', 'C', 'V'];
  let skillSig = '';
  function paintSkills(sk) {
    sk = sk || {};
    const byId = {}; (sk.list || []).forEach(s => byId[s.id] = s);
    const ids = (Array.isArray(sk.equipped) && sk.equipped.length) ? sk.equipped
              : (sk.list || []).map(s => s.id);
    const shown = ids.map(id => byId[id]).filter(Boolean).slice(0, 4);
    dom.skills.style.display = shown.length ? 'flex' : 'none';

    const sig = shown.map(s => s.id).join('|');
    if (sig !== skillSig) { // 構成が変わった時だけ作り直す
      skillSig = sig;
      while (dom.skillEls.length < shown.length) {
        const b = el('div', '', dom.skills); b.className = 'ui-skill';
        const key = el('div', '', b); key.className = 'key';
        const ic = el('img', 'display:none;', b); ic.className = 'ic'; ic.alt = '';
        ic.addEventListener('error', () => { ic.style.display = 'none'; });
        const sw = el('div', '', b); sw.className = 'sw';
        const cd = el('div', '', b); cd.className = 'cd';
        dom.skillEls.push({ b, key, ic, sw, cd, id: null });
      }
      for (let i = 0; i < dom.skillEls.length; i++) {
        const ui = dom.skillEls[i], s = shown[i];
        ui.b.style.display = s ? '' : 'none';
        if (!s) continue;
        ui.id = s.id; ui.key.textContent = SKILL_KEYS[i] || '';
        const url = iconUrl({ name: s.name, icon: s.icon });
        if (url) { if (ui.ic.getAttribute('src') !== url) ui.ic.src = url; ui.ic.style.display = ''; ui.sw.style.display = 'none'; }
        else { ui.ic.style.display = 'none'; ui.sw.style.display = ''; ui.sw.style.background = s.color || '#6a8cff'; }
        ui.b.title = s.name + (s.desc ? ' — ' + s.desc : '');
        ui.b.onclick = () => {
          const ready = !!byIdReady(ui.id);
          if (!ready) return;
          try { const vg = window.VoxelGame; if (vg && typeof vg.useSkill === 'function') vg.useSkill(ui.id); } catch (e) {}
        };
      }
    }
    // 毎フレーム：ready/cooldown を反映
    for (let i = 0; i < dom.skillEls.length; i++) {
      const ui = dom.skillEls[i], s = shown[i]; if (!s) continue;
      const ready = s.ready != null ? !!s.ready : (clamp01(s.cooldown) <= 0.001);
      ui.b.classList.toggle('ready', ready);
      const rem = ready ? 0 : clamp01(s.cooldown);
      ui.cd.style.height = (rem * 100).toFixed(0) + '%';
    }
    // 必殺ゲージ
    if (typeof sk.energy === 'number') {
      dom.ult.style.display = 'block';
      const e = clamp01(sk.energy);
      dom.ultfill.style.width = (e * 100).toFixed(1) + '%';
      dom.ult.classList.toggle('full', e >= 0.999);
    } else dom.ult.style.display = 'none';
    skillStateRef = sk; // クリック時の最新ready参照用
  }
  let skillStateRef = null;
  function byIdReady(id) {
    if (!skillStateRef || !skillStateRef.list) return true;
    const s = skillStateRef.list.find(x => x.id === id);
    if (!s) return true;
    return s.ready != null ? !!s.ready : (clamp01(s.cooldown) <= 0.001);
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

  // ① アイテム/装備の「効果」説明（恩恵を伝えるツールチップ用）。core値に追従（WEAPONS.dmg / P.food / 防御%）。
  const ITEM_INFO = {
    meat:  '🍖 食料：食べる→空腹+9。HP自然回復の前提になる',
    apple: '🍎 食料：食べる→空腹+6',
    egg:   '🥚 取引品：商人・農民に売ってコインに換えられる',
    coin:  '🪙 通貨：NPC取引・仲間の雇用（5コイン）に使う',
    coal:  '⚫ 採掘素材：燃料・素材として貯めておくと役立つ',
    iron:  '⛓️ 装備素材：剣・斧・盾・防具クラフトに必須の鉱石',
    gold:  '🏅 貴重な素材：ボス討伐の報酬。価値が高い',
  };
  const itemEffect = (key) => ITEM_INFO[key] || '素材・アイテム';
  // 武器の攻撃力（core WEAPONS.dmg 準拠）／装備クラフト種別の効果（EQUIP_RECIPES・防御値 準拠）
  const WEAPON_INFO = { fist:'素手：攻撃力3・素早いが弱い', sword:'剣：攻撃力5・範囲広め', axe:'斧：攻撃力9・重い大振り（最大火力）', pickaxe:'ピッケル：攻撃力4・採掘が速い', bow:'弓：攻撃力7・遠距離＆溜め撃ち' };
  const EQUIP_KIND_INFO = { pickaxe:'採掘が速くなる（攻撃力4）', sword:'攻撃力5・近接の主力', axe:'攻撃力9・最大火力の大振り', bow:'遠距離攻撃（攻撃力7・溜め可）', shield:'被ダメージ-10%（構えて防御）', armor:'被ダメージ-12%/枚（頭・胴・脚で最大3枚）' };
  const WEAPON_DMG = { fist:3, sword:5, axe:9, pickaxe:4, bow:7 }; // ④ ステータス画面の攻撃力表示（core WEAPONS.dmg 準拠）

  // PC=ホバー / スマホ=長押し でツールチップ表示。getHtml は表示時評価＝最新の在庫/効果を反映。
  function bindTip(elm, getHtml) {
    const html = () => (typeof getHtml === 'function' ? getHtml() : getHtml);
    elm.addEventListener('mouseenter', () => buildTip(html()));
    elm.addEventListener('mousemove', moveTip);
    elm.addEventListener('mouseleave', hideTip);
    let lpTimer = null, hideTimer = null, sx = 0, sy = 0;
    const clearLp = () => { if (lpTimer) { clearTimeout(lpTimer); lpTimer = null; } };
    elm.addEventListener('pointerdown', (e) => {
      if (e.pointerType !== 'touch') return;
      sx = e.clientX; sy = e.clientY;
      if (hideTimer) { clearTimeout(hideTimer); hideTimer = null; }
      clearLp();
      lpTimer = setTimeout(() => { buildTip(html()); moveTip({ clientX: sx, clientY: sy }); try { navigator.vibrate && navigator.vibrate(12); } catch (x) {} }, 340);
    });
    elm.addEventListener('pointermove', (e) => {
      if (e.pointerType !== 'touch' || !lpTimer) return;
      if (Math.abs(e.clientX - sx) > 12 || Math.abs(e.clientY - sy) > 12) clearLp(); // スクロール/ドラッグはキャンセル
    });
    const endTouch = (e) => {
      if (e.pointerType !== 'touch') return;
      clearLp();
      if (dom.tip.style.display === 'block') { if (hideTimer) clearTimeout(hideTimer); hideTimer = setTimeout(hideTip, 1800); } // 指を離して読めるよう少し残す
    };
    elm.addEventListener('pointerup', endTouch);
    elm.addEventListener('pointercancel', endTouch);
  }

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
    const eqS = st.equipment || {};
    const sig = JSON.stringify({
      h: (st.hotbar || []).map(x => [x.block, x.count, x.active ? 1 : 0]),
      it: (st.items || []).map(x => [x.key, x.count]),
      r: (st.recipes || []).map(x => x.canCraft ? 1 : 0),
      eq: [eqS.weapon, (eqS.weapons || []).map(w => [w.id, w.active ? 1 : 0]),
           eqS.armor && [eqS.armor.head, eqS.armor.body, eqS.armor.legs],
           eqS.shield ? 1 : 0, eqS.ownedShield ? 1 : 0, eqS.defense],
      er: (st.equipRecipes || []).map(x => x.canCraft ? 1 : 0),
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
      bindTip(cell, () => `<b>${h.name}</b><br>所持 ${clampN(h.count)}　/　数字キー ${i + 1 <= 9 ? i + 1 : '-'}<br><span class="tip-eff">建築ブロック：タップで選択→設置できる</span>`);
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
      bindTip(cell, () => `<b>${it.name}</b>　所持 ${clampN(it.count)}<br><span class="tip-eff">${itemEffect(it.key)}</span>`);
    });

    // 装備（武器・防具・盾）
    renderEquip(p, st.equipment || {});

    // 装備クラフト（採掘素材→装備）
    if ((st.equipRecipes || []).length) {
      el('div', '', p).className = 'uiv-sec';
      p.lastChild.textContent = '装備クラフト（素材から武器・防具を作成）';
      const eg = el('div', '', p); eg.className = 'uiv-craft';
      (st.equipRecipes || []).forEach((r) => {
        const btn = el('button', '', eg); btn.className = 'uiv-recipe'; btn.disabled = !r.canCraft;
        fillIcon(btn, { name: r.name, icon: ('item_' + r.kind) });
        const rt = el('div', '', btn); rt.className = 'rt';
        const eff = EQUIP_KIND_INFO[r.kind] || '';
        rt.innerHTML = `<b>${r.name}</b>${eff ? `<br><span style="opacity:.95;color:#bfe6ff">${eff}</span>` : ''}<br><span style="opacity:.8">${r.cost} → 作る</span>`;
        bindTip(btn, () => `<b>${r.name}</b>${eff ? `<br><span class="tip-eff">${eff}</span>` : ''}<br>` + (r.canCraft ? `${r.cost} を消費して作成` : `素材不足／既に所持：${r.cost}`));
        btn.addEventListener('click', () => {
          if (btn.disabled) return;
          try { const vg = window.VoxelGame; if (vg && typeof vg.craftEquip === 'function') vg.craftEquip(r.id); } catch (e) {}
          // クラフト音はコア craftEquip 側で再生されるため二重に鳴らさない
          invSig = ''; // 装備・在庫の変化を即時反映
        });
      });
    }

    // クラフト（資源変換）
    el('div', '', p).className = 'uiv-sec';
    p.lastChild.textContent = 'クラフト（資源を変換・クリックで作成）';
    const cgrid = el('div', '', p); cgrid.className = 'uiv-craft';
    (st.recipes || []).forEach((r, i) => {
      const btn = el('button', '', cgrid); btn.className = 'uiv-recipe'; btn.disabled = !r.canCraft;
      fillIcon(btn, { name: r.outName, icon: r.outIcon });
      const rt = el('div', '', btn); rt.className = 'rt';
      rt.innerHTML = `<b>${r.outName} ×${r.n}</b><br><span style="opacity:.8">${r.inName} ×${r.cost} → 作る</span>`;
      bindTip(btn, () => r.canCraft ? `<b>${r.outName}</b> を作成<br>${r.inName} ×${r.cost} を消費` : `素材不足：${r.inName} ×${r.cost} が必要`);
      btn.addEventListener('click', () => { if (!btn.disabled) { callCraft(i); invSig = ''; } });
    });
  }

  // 装備パネル（1号機の口に配線：equipWeapon / toggleShield / unequipArmor）
  const ARMOR_SLOTS = [['head', '頭'], ['body', '胴'], ['legs', '脚']];
  function equipCell(grid, { icon, name, active, owned, badge, tip, onClick }) {
    const cell = el('div', '', grid);
    cell.className = 'uiv-cell' + (active ? ' active' : '') + (owned ? '' : ' empty');
    if (!onClick) cell.style.cursor = 'default';
    fillIcon(cell, { name, icon });
    const nm = el('div', '', cell); nm.className = 'nm'; nm.textContent = name;
    if (badge) { const b = el('div', '', cell); b.className = 'ct'; b.textContent = badge; }
    bindTip(cell, tip);
    if (onClick) cell.addEventListener('click', () => { onClick(); invSig = ''; });
    return cell;
  }
  function renderEquip(p, eq) {
    el('div', '', p).className = 'uiv-sec';
    p.lastChild.textContent = '装備（クリックで装備／解除）';

    // --- 武器（所持武器を持ち替え）---
    const wlab = el('div', 'font-size:12px;opacity:.7;margin:2px 0 6px;', p);
    wlab.textContent = `武器：${eq.weaponName || '素手'} を装備中`;
    const wgrid = el('div', '', p); wgrid.className = 'uiv-grid';
    (eq.weapons || []).forEach((w) => {
      equipCell(wgrid, {
        icon: w.id === 'fist' ? null : ('item_' + w.id),
        name: w.name, active: w.active, owned: true,
        badge: w.active ? '✓' : '',
        tip: `<b>${w.name}</b>${WEAPON_INFO[w.id] ? `<br><span class="tip-eff">${WEAPON_INFO[w.id]}</span>` : ''}<br>` + (w.active ? '装備中' : '<span style="opacity:.7">タップで装備（C/Bでも切替）</span>'),
        onClick: w.active ? null : () => {
          try { window.equipWeapon && window.equipWeapon(w.id); } catch (e) {}
          try { window.playSFX && window.playSFX('pickup'); } catch (e) {}
        },
      });
    });

    // --- 防具・盾 ---
    const dlab = el('div', 'font-size:12px;opacity:.7;margin:12px 0 6px;', p);
    dlab.textContent = `防具・盾　防御 ${Math.round((eq.defense || 0) * 100)}% 軽減`;
    const dgrid = el('div', '', p); dgrid.className = 'uiv-grid';
    const armor = eq.armor || {};
    ARMOR_SLOTS.forEach(([slot, label]) => {
      const on = !!armor[slot];
      equipCell(dgrid, {
        icon: 'item_armor', name: label, active: on, owned: on,
        badge: on ? '○' : '-',
        tip: `<b>防具（${label}）</b><br><span class="tip-eff">${EQUIP_KIND_INFO.armor}</span><br>` + (on ? '<span style="opacity:.7">タップで外す</span>' : '<span style="opacity:.7">未装備：入手・装備クラフトで装着</span>'),
        onClick: on ? () => {
          try { window.unequipArmor && window.unequipArmor(slot); } catch (e) {}
          try { window.playSFX && window.playSFX('pickup'); } catch (e) {}
        } : null,
      });
    });
    // 盾
    equipCell(dgrid, {
      icon: 'item_shield', name: '盾', active: !!eq.shield, owned: !!eq.ownedShield,
      badge: eq.shield ? '○' : (eq.ownedShield ? '-' : ''),
      tip: `<b>盾</b><br><span class="tip-eff">${EQUIP_KIND_INFO.shield}</span><br>` + (!eq.ownedShield ? '<span style="opacity:.7">未入手：装備クラフトで使える</span>' : (eq.shield ? '<span style="opacity:.7">構え中：タップで下ろす</span>' : '<span style="opacity:.7">タップで構える</span>')),
      onClick: eq.ownedShield ? () => {
        try { window.toggleShield && window.toggleShield(); } catch (e) {}
        try { window.playSFX && window.playSFX('pickup'); } catch (e) {}
      } : null,
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
    mk('📊 ステータス', '', () => renderMenu('status'));
    mk('⚡ 必殺技', '', () => renderMenu('skills'));
    mk('⚙ 設定', '', () => renderMenu('settings'));
    mk('💾 セーブ＆ロード', '', () => renderMenu('slots'));
    mk('💾 今すぐ保存', '', () => { try { window.VoxelGame && window.VoxelGame.save && window.VoxelGame.save(); } catch (e) {} const b = btns.lastChild; b.textContent = '✓ 保存しました'; setTimeout(() => { b.textContent = '💾 今すぐ保存'; }, 1200); });
  }

  function renderMenu(screen) {
    menuScreen = screen;
    const p = dom.menuPanel; p.innerHTML = '';
    if (screen === 'settings') renderSettings(p);
    else if (screen === 'slots') renderSlots(p);
    else if (screen === 'trade') renderTrade(p);
    else if (screen === 'skills') renderSkillsScreen(p);
    else if (screen === 'status') renderStatusScreen(p);
    else renderMenuRoot(p);
  }

  // ④ ステータス画面：いまの強さ・装備・記録を一覧（state() から読む。Tab / 📊ボタンで開閉）
  function renderStatusScreen(p) {
    el('div', '', p).className = 'uim-title'; p.lastChild.textContent = '📊 ステータス';
    el('div', '', p).className = 'uim-sub'; p.lastChild.textContent = 'いまの強さ・装備・記録';
    let st = {};
    try { const vg = window.VoxelGame; if (vg && typeof vg.state === 'function') st = vg.state() || {}; } catch (e) {}
    const eq = st.equipment || {}, armor = eq.armor || {};
    const coin = (st.items || []).find(it => it.key === 'coin');
    const atk = (WEAPON_DMG[eq.weapon] != null) ? WEAPON_DMG[eq.weapon] : '—';
    const armorN = ['head', 'body', 'legs'].filter(k => armor[k]).length;
    const rows = [
      ['🏅 レベル', `Lv ${clampN(st.level)}　EXP ${clampN(st.exp)}/${st.expToNext || '-'}`],
      ['❤️ HP', `${clampN(st.hp)} / ${clampN(st.maxHp)}`],
      ['🍖 空腹', `${clampN(st.hunger)} / ${clampN(st.maxHunger)}`],
      ['⚔️ 攻撃力', `${atk}　（${eq.weaponName || '素手'}）`],
      ['🛡️ 防御', `${Math.round((eq.defense || 0) * 100)}% 軽減　（防具 ${armorN}/3・盾 ${eq.shield ? '○' : '-'}）`],
      ['🪙 所持金', `${coin ? clampN(coin.count) : 0} コイン`],
      ['🤝 仲間', `${(st.companions || []).length} / ${st.companionMax || 0} 人`],
    ];
    const tbl = el('div', '', p); tbl.className = 'uist';
    rows.forEach(([k, v]) => {
      const r = el('div', '', tbl); r.className = 'uist-row';
      el('div', '', r).className = 'k'; r.lastChild.textContent = k;
      el('div', '', r).className = 'v'; r.lastChild.textContent = v;
    });
    // 討伐記録（state().bossKills が来たら表示。未提供時は core 連携待ち）
    el('div', '', p).className = 'uim-sub'; p.lastChild.style.marginTop = '10px'; p.lastChild.textContent = '⚔️ 討伐記録';
    const kwrap = el('div', '', p); kwrap.className = 'uist';
    const bk = st.bossKills;
    if (bk && typeof bk === 'object') {
      const LBL = { dragon: 'ドラゴン', skeleton_king: 'スケルトンキング', demon: 'デーモン', golem: 'ゴーレム' };
      let any = false;
      Object.keys(LBL).forEach(k => {
        if (bk[k]) { any = true; const r = el('div', '', kwrap); r.className = 'uist-row';
          el('div', '', r).className = 'k'; r.lastChild.textContent = LBL[k];
          el('div', '', r).className = 'v'; r.lastChild.textContent = `${clampN(bk[k])} 体`; }
      });
      if (!any) { const n = el('div', 'font-size:13px;opacity:.7;padding:4px 2px;', kwrap); n.textContent = 'まだボスを倒していない。強敵を探して挑もう。'; }
    } else {
      const n = el('div', 'font-size:13px;opacity:.7;padding:4px 2px;', kwrap); n.textContent = '討伐記録は近日対応（コア state().bossKills 連携待ち）。';
    }
    const back = el('div', '', p); back.className = 'uim-back';
    const b = el('div', '', back); b.className = 'uim-btn'; b.textContent = '← 戻る'; b.addEventListener('click', () => renderMenu('menu'));
  }

  // ③ ゲームオーバー画面（dormant 受け皿）：core が window.onPlayerDeath(info) を呼ぶと表示。
  //   info = { cause?, level?, kills?, seconds? }。リスポーンは VoxelGame.respawn() があれば呼ぶ。
  //   ※現状 core は被弾で即 respawn() する実装。本画面を活かすには core 側で「即respawnを止め
  //     →onPlayerDeath(info) を呼ぶ→ボタンで VoxelGame.respawn()」への変更が必要（1号機へ要請）。
  let goEl = null;
  function fmtDuration(sec) { sec = Math.max(0, Math.floor(+sec || 0)); const m = Math.floor(sec / 60), s = sec % 60; return `${m}分${String(s).padStart(2, '0')}秒`; }
  function showGameOver(info) {
    info = info || {};
    if (!goEl) { goEl = el('div', '', document.body); goEl.id = 'ui-gameover'; }
    goEl.innerHTML = '';
    el('div', '', goEl).className = 'got'; goEl.lastChild.textContent = 'G A M E   O V E R';
    el('div', '', goEl).className = 'gosub'; goEl.lastChild.textContent = info.cause ? `死因: ${info.cause}` : 'あなたは力尽きた…';
    const stx = el('div', '', goEl); stx.className = 'gostats';
    const lv = (info.level != null) ? info.level : '—';
    const kills = (typeof info.kills === 'number') ? `${info.kills} 体` : '—';
    const tm = (typeof info.seconds === 'number') ? fmtDuration(info.seconds) : (info.timeText || '—');
    [['🏅 レベル', lv], ['⚔️ 討伐数', kills], ['⏱ プレイ時間', tm]].forEach(([k, v]) => {
      const r = el('div', '', stx); r.textContent = `${k}：${v}`;
    });
    const btn = el('div', '', goEl); btn.className = 'gobtn'; btn.textContent = '🔄 リスポーン';
    btn.addEventListener('click', () => {
      try { const vg = window.VoxelGame; if (vg && typeof vg.respawn === 'function') vg.respawn(); } catch (e) {}
      hideGameOver();
    });
    goEl.classList.add('show');
  }
  function hideGameOver() { if (goEl) goEl.classList.remove('show'); }

  // 必殺技の一覧／装備UI（覚えた技を最大4つ装備）
  function renderSkillsScreen(p) {
    el('div', '', p).className = 'uim-title'; p.lastChild.textContent = '⚡ 必殺技';
    el('div', '', p).className = 'uim-sub'; p.lastChild.textContent = 'クリックで装備／解除（最大4つ・Z X C V）';
    let sk = {};
    try { const vg = window.VoxelGame; if (vg && typeof vg.state === 'function') sk = vg.state().skills || {}; } catch (e) {}
    const list = Array.isArray(sk.list) ? sk.list : [];
    let equipped = Array.isArray(sk.equipped) ? sk.equipped.slice() : list.map(s => s.id).slice(0, 4);
    if (!list.length) { const n = el('div', 'font-size:13px;opacity:.7;', p); n.textContent = 'まだ必殺技を覚えていない。レベルを上げて習得しよう。'; }
    list.forEach((s) => {
      const card = el('div', '', p); card.className = 'uik-card' + (equipped.indexOf(s.id) >= 0 ? ' eq' : '');
      fillIcon(card, { name: s.name, icon: s.icon, swatch: s.color });
      const info = el('div', '', card); info.className = 'info';
      const nm = el('div', '', info); nm.className = 'nm'; nm.textContent = s.name;
      const ds = el('div', '', info); ds.className = 'ds'; ds.textContent = s.desc || (s.kind ? `タイプ: ${s.kind}` : '');
      const tag = el('div', '', card); tag.className = 'eqtag';
      const slot = equipped.indexOf(s.id);
      tag.textContent = slot >= 0 ? (SKILL_KEYS[slot] || '装備中') : '＋装備';
      card.addEventListener('click', () => {
        try {
          const vg = window.VoxelGame;
          if (vg && typeof vg.equipSkill === 'function') vg.equipSkill(s.id);
        } catch (e) {}
        renderMenu('skills'); // 反映
      });
    });
    const back = el('div', '', p); back.className = 'uim-back';
    const b = el('div', '', back); b.className = 'uim-btn'; b.textContent = '← 戻る'; b.addEventListener('click', () => renderMenu('menu'));
  }
  function openMenu(screen) {
    menuOpen = true; renderMenu(screen || 'menu');
    dom.menu.classList.add('open');
    if (document.pointerLockElement) document.exitPointerLock();
  }
  function closeMenu() { menuOpen = false; dom.menu.classList.remove('open'); }

  // =====================================================================
  // ★ NPC会話／取引UI（1号機のNPC会話実装と接続）
  //   ・core が話しかけ時に window.UI.openTrade(session) を呼ぶ（中身はUI側）
  //   ・取引成立は window.VoxelGame.trade(offerId) 経由（在庫増減はcore）
  //     → 戻り値に更新後 session/offers があれば即再描画
  //   ・口/データ不在でも安全（呼ばれなければ何も出ない）
  //   session = { npc, job, greeting, offers:[
  //     { id, giveName,giveIcon,giveCount, getName,getIcon,getCount, canAfford } ] }
  // =====================================================================
  let tradeSession = null;
  const JOB_EMOJI = { merchant:'🪙', blacksmith:'🔨', farmer:'🌾', guard:'🛡', child:'🧒', elder:'🧓', baker:'🥖', villager:'🧑' };
  // ② 話しかけ可能な住人 type（core JOB_LABEL 準拠）。state().mobs の type で近接判定→「話す」ボタン表示
  const TALKABLE_TYPES = new Set(['merchant','blacksmith','farmer','baker','guard','elder','child','woman','villager','soldier_spear','soldier_sword','soldier_captain']);
  const TALK_RANGE = 3.6; // core talkToNPC の探索半径(3.5)に合わせる（わずかに広め）

  function offerSide(holder, name, icon, count, cls) {
    const side = el('div', '', holder); side.className = 'uit-side' + (cls ? ' ' + cls : '');
    fillIcon(side, { name, icon });
    const q = el('div', '', side); q.className = 'q'; q.textContent = `${name} ×${clampN(count)}`;
  }
  function renderTrade(p) {
    const s = tradeSession || {};
    const head = el('div', '', p); head.className = 'uiv-head';
    const npcWrap = el('div', '', head); npcWrap.className = 'uit-npc';
    const ava = el('div', '', npcWrap); ava.className = 'uit-ava'; ava.textContent = JOB_EMOJI[s.job] || '🧑';
    const nb = el('div', '', npcWrap);
    const nm = el('div', '', nb); nm.className = 'uit-name'; nm.textContent = s.npc || '住人';
    const jb = el('div', '', nb); jb.className = 'uit-job'; jb.textContent = s.job ? `（${s.job}）` : '';
    const x = el('div', '', head); x.className = 'uiv-x'; x.textContent = '✕ 閉じる（Esc）'; x.addEventListener('click', closeMenu);

    if (s.greeting) { const say = el('div', '', p); say.className = 'uit-say'; say.textContent = s.greeting; }

    el('div', '', p).className = 'uiv-sec'; p.lastChild.textContent = '取引（渡す → もらう・クリックで交換）';
    const offers = Array.isArray(s.offers) ? s.offers : [];
    if (!offers.length) { const n = el('div', '', p); n.className = 'uit-none'; n.textContent = '今は取引できるものがないようだ…'; }
    offers.forEach((o) => {
      const btn = el('button', '', p); btn.className = 'uit-offer'; btn.disabled = !o.canAfford;
      offerSide(btn, o.giveName, o.giveIcon, o.giveCount);          // 渡す（プレイヤー支払い）
      const ar = el('div', '', btn); ar.className = 'uit-arrow'; ar.textContent = '➡';
      offerSide(btn, o.getName, o.getIcon, o.getCount, 'uit-get');  // 受け取る
      // ② もらえる物の効果（武器/防具/食料等）を1行で明示＝取引の価値が伝わるように
      const getKey = (o.getIcon || '').replace(/^item_/, '');
      const eff = EQUIP_KIND_INFO[getKey] || ITEM_INFO[getKey] || '';
      if (eff) { const ec = el('div', '', btn); ec.className = 'uit-eff'; ec.textContent = '→ ' + eff; }
      btn.title = o.canAfford ? `${o.giveName}×${o.giveCount} を渡して ${o.getName}×${o.getCount} を受け取る` : `${o.giveName}×${o.giveCount} が足りません`;
      bindTip(btn, () => `<b>${o.getName} ×${o.getCount}</b>${eff ? `<br><span class="tip-eff">${eff}</span>` : ''}<br><span style="opacity:.8">${o.giveName} ×${o.giveCount} を渡す</span>` + (o.canAfford ? '' : '<br><span style="color:#ff9a9a">在庫不足</span>'));
      btn.addEventListener('click', () => {
        if (btn.disabled) return;
        let updated = null;
        try { const i = window.VoxelGame; if (i && typeof i.trade === 'function') updated = i.trade(o.id); } catch (e) {}
        try { window.playSFX && window.playSFX('trade'); } catch (e) {}
        if (updated && (updated.offers || updated.npc)) tradeSession = updated; // 更新セッションがあれば差し替え
        renderMenu('trade'); // 在庫/可否を反映して再描画
      });
    });

    // ③ 仲間にする（session.recruit が来た時だけ表示。可否は recruit.canRecruit、不可理由でラベル変化）
    const rc = s.recruit;
    if (rc && typeof rc.cost === 'number') {
      el('div', '', p).className = 'uiv-sec'; p.lastChild.textContent = '仲間';
      const rbtn = el('button', '', p); rbtn.className = 'uit-recruit';
      const reason = rc.already ? '仲間済み' : rc.full ? '満員' : !rc.canRecruit ? 'コイン不足' : '';
      rbtn.disabled = !rc.canRecruit;
      const ico = el('div', '', rbtn); ico.className = 'e'; ico.textContent = '🤝';
      const lab = el('div', '', rbtn);
      lab.textContent = rc.canRecruit ? `仲間にする（${rc.cost}コイン）` : `仲間にする（${reason}）`;
      const sub = el('div', '', rbtn); sub.className = 'sub'; sub.textContent = rc.canRecruit ? '' : `必要${rc.cost}コイン`;
      rbtn.title = rc.canRecruit ? `${rc.cost}コインで仲間にする` : `仲間にできません：${reason}`;
      rbtn.addEventListener('click', () => {
        if (rbtn.disabled) return;
        let updated = null;
        try { const i = coreInput(); if (i && typeof i.recruit === 'function') updated = i.recruit(); } catch (e) {}
        try { window.playSFX && window.playSFX('trade'); } catch (e) {}
        if (updated && (updated.offers || updated.npc)) tradeSession = updated; // recruit は更新後 session を返す
        renderMenu('trade'); // 仲間化後の状態（already=true 等）を反映
      });
    }
  }
  function openTrade(session) {
    tradeSession = session || tradeSession || {};
    menuOpen = true; renderMenu('trade');
    dom.menu.classList.add('open');
    if (document.pointerLockElement) document.exitPointerLock();
  }

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
    // 軸対応: stickVec.x = 左右(strafe, dx) / stickVec.z = 前後(forward, dy)。上=前進=z<0。
    // ① コアが input.move(dx, dz) 受け口を提供したら最優先で両軸を渡す（第1引数=左右, 第2引数=前後）
    //   コア(index.html)実装: move(fwd,-z)+move(right,+x)＝上倒し(z<0)で前進・右倒し(x>0)で右。符号一致。
    if (i && typeof i.move === 'function') {
      // フォールバックで合成したWASDが残っていれば解除（経路切替時の前進固定バグ防止。未heldなら no-op）
      setKey('KeyW', false); setKey('KeyS', false); setKey('KeyA', false); setKey('KeyD', false);
      try { i.move(stickVec.x, stickVec.z); } catch (e) {}
      return;
    }
    // ② フォールバック: WASD 合成キー。左右(x)が抜けないよう A/D も毎回判定する
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
    el('div', '', attack).className = 'chg';   // 弓溜め（長押し）の充填リング
    const place = mkBtn(tbtns, 'place', '⛏', '設置');
    const dashWrap = el('div', '', cont); dashWrap.className = 'ui-tdash';
    const dash = mkBtn(dashWrap, '', '🏃', 'ダッシュ');
    const top = el('div', '', cont); top.className = 'ui-ttop';
    const invBtn = mkBtn(top, '', '🎒');
    const statusBtn = mkBtn(top, '', '📊'); // ④ ステータス画面
    const menuBtn = mkBtn(top, '', '⏸');
    // ② NPC接近時に出る「話す」ボタン（近接判定で tick が .show を付け外し）
    const talkWrap = el('div', '', cont); talkWrap.className = 'ui-ttalk';
    const talkBtn = mkBtn(talkWrap, '', '💬', '話す');
    dom.touch = cont; dom.look = look; dom.stick = stick; dom.knob = knob; dom.talkWrap = talkWrap;

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
    // 攻撃：タップで攻撃/破壊、長押しで弓溜め（core が primary 押下保持を溜めとして扱う）。
    //   約200ms以上の保持で充填リングを点灯し「溜め中」を視覚化（実際の溜めは core 側）。
    let chargeTimer = null;
    holdBtn(attack,
      () => { inputAct('primary', true); chargeTimer = setTimeout(() => attack.classList.add('charging'), 200); },
      () => { inputAct('primary', false); if (chargeTimer) { clearTimeout(chargeTimer); chargeTimer = null; } attack.classList.remove('charging'); });
    holdBtn(place, () => inputAct('secondary', true), () => inputAct('secondary', false));
    tapBtn(dash, () => { dashOn = !dashOn; dash.classList.toggle('on', dashOn); setKey('ShiftLeft', dashOn); });
    tapBtn(invBtn, () => { window.UI._routed = true; toggleInv(); });
    tapBtn(statusBtn, () => { window.UI._routed = true; (menuOpen && menuScreen === 'status') ? closeMenu() : openMenu('status'); });
    tapBtn(menuBtn, () => { window.UI._routed = true; menuOpen ? closeMenu() : openMenu('menu'); });
    // ② 話す：近くのNPCに話しかける（core が window.UI.openTrade(session) を呼び会話UIを開く）
    tapBtn(talkBtn, () => { window.UI._routed = true; inputAct('talk'); });
  }

  function setTouchMode(on) {
    touchOn = on;
    // コアがプレイ判定に使えるフラグを公開。スマホはポインタロックが使えないため、
    // コアのループ/overlay 制御は `document.pointerLockElement===canvas || window.UI_TOUCH` で判定すべき。
    window.UI_TOUCH = on;
    if (!dom.touch) return;
    dom.touch.classList.toggle('on', on);
    dom.look.style.display = on ? 'block' : 'none';
    if (on) dom.hint.style.display = 'none'; // スマホではキーヒントを出さない
  }

  // =====================================================================
  // レーダーミニマップ（北を上にしたシンプル版・プレイヤー中心）
  // =====================================================================
  const RADAR_RANGE = 44; // 半径（ブロック）

  // 構造物メタ（レーダー色・発見トーストの絵文字/和名・縁の方向矢印対象を一元化）
  //   1号機が state().structures[].type に流す想定の type 名:
  //   village=村 / fort=砦 / castle=王国城 / shrine=祠 / dungeon=ダンジョン / chest=宝箱 / spawner=スポナー
  const STRUCT_META = {
    village: { color: '#9be86a', glyph: '🏘', name: '村',         arrow: true,  discover: true },
    fort:    { color: '#d9b36a', glyph: '🏯', name: '砦',         arrow: true,  discover: true },
    castle:  { color: '#ffd54a', glyph: '🏰', name: '王国城',     arrow: true,  discover: true, big: true },
    shrine:  { color: '#7be0ff', glyph: '⛩',  name: '祠',         arrow: true,  discover: true },
    dungeon: { color: '#c58cff', glyph: '🗝', name: 'ダンジョン', arrow: true,  discover: true },
    chest:   { color: '#ffd54a', glyph: '📦', name: '宝箱',       arrow: false, discover: false },
    spawner: { color: '#ff6a6a', glyph: '💀', name: 'スポナー',   arrow: false, discover: false },
  };
  function structKey(s) { return (s.id != null) ? ('id:' + s.id) : (s.type + ':' + Math.round(s.x) + ':' + Math.round(s.z)); }
  function structName(s) { const m = STRUCT_META[s.type]; return s.name || (m && m.name) || '構造物'; }

  // 探索の足跡：一定距離ごとに通過点を記録（固定長リングで軽量）
  const trail = [];
  let lastTrailX = null, lastTrailZ = null;
  function recordTrail(px, pz) {
    if (lastTrailX === null || (px - lastTrailX) * (px - lastTrailX) + (pz - lastTrailZ) * (pz - lastTrailZ) >= 12) {
      trail.push({ x: px, z: pz });
      lastTrailX = px; lastTrailZ = pz;
      if (trail.length > 800) trail.shift();
    }
  }
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

    const px = st.pos ? st.pos.x : 0, pz = st.pos ? st.pos.z : 0;
    const edge = R - 8;

    // 探索の足跡（一定距離ごとに記録した過去位置を薄く点描）
    recordTrail(px, pz);
    ctx.fillStyle = 'rgba(160,210,255,.16)';
    for (let i = 0; i < trail.length; i++) {
      const dx = (trail[i].x - px) * scale, dz = (trail[i].z - pz) * scale;
      if (dx * dx + dz * dz > edge * edge) continue;
      ctx.beginPath(); ctx.arc(R + dx, R + dz, 2.4, 0, Math.PI * 2); ctx.fill();
    }

    // 構造物マーカー（四角／重要拠点は大きめ＋外周リング）＋範囲外は縁に方向矢印
    const structs = Array.isArray(st.structures) ? st.structures : [];
    for (const s of structs) {
      const dx = (s.x - px) * scale, dz = (s.z - pz) * scale;
      const m = STRUCT_META[s.type], col = (m && m.color) || '#fff', dist = Math.hypot(dx, dz);
      if (dist <= edge) {
        const r = (m && m.big) ? 4.6 : 3.4; // 王国城など big は大きめに描く
        ctx.save(); ctx.translate(R + dx, R + dz);
        ctx.fillStyle = col; ctx.fillRect(-r, -r, r * 2, r * 2);
        ctx.strokeStyle = 'rgba(0,0,0,.55)'; ctx.lineWidth = 1; ctx.strokeRect(-r, -r, r * 2, r * 2);
        if (m && m.big) { // 王国城は外周リングで一段目立たせる
          ctx.globalAlpha = 0.85; ctx.strokeStyle = col; ctx.lineWidth = 1.4;
          ctx.beginPath(); ctx.arc(0, 0, r + 3, 0, Math.PI * 2); ctx.stroke();
        }
        ctx.restore();
      } else if (m && m.arrow) {
        const a = Math.atan2(dz, dx);
        ctx.save(); ctx.translate(R + Math.cos(a) * edge, R + Math.sin(a) * edge); ctx.rotate(a);
        ctx.fillStyle = col; ctx.globalAlpha = 0.9;
        const sz = (m && m.big) ? 6 : 5;
        ctx.beginPath(); ctx.moveTo(sz, 0); ctx.lineTo(-sz + 2, -3.2); ctx.lineTo(-sz + 2, 3.2); ctx.closePath(); ctx.fill();
        ctx.restore();
      }
    }

    // モブ blip（北上＝world +x→右, +z→下）
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
  // 構造物 発見トースト
  //   ・主に state().structures への近接で自動検知（一度きり）。
  //   ・1号機が明示通知したい時は window.onDiscover({type,name}) / window.UI.toast(text,opts)。
  // =====================================================================
  const DISCOVER_RANGE = 40;        // この距離まで近づくと「発見」（≒レーダー入り）
  const discovered = new Set();     // 既発見キー（再通知しない）
  const toasts = [];                // 表示中 {el, life, ttl}
  const toastQueue = [];            // 未表示の {text, glyph, label, color}
  const MAX_TOAST_SHOWN = 3;

  function enqueueToast(t) {
    toastQueue.push(t);
    if (toastQueue.length > 10) toastQueue.shift(); // 暴発時の保険
  }
  // 構造物発見の自動検知（state 駆動・防御的）
  function checkDiscovery(st) {
    const structs = Array.isArray(st.structures) ? st.structures : [];
    if (!structs.length) return;
    const px = st.pos ? st.pos.x : 0, pz = st.pos ? st.pos.z : 0;
    for (const s of structs) {
      const m = STRUCT_META[s.type];
      if (!m || !m.discover) continue;             // 主要ランドマークのみ（宝箱/スポナーは除外）
      const k = structKey(s);
      if (discovered.has(k)) continue;
      const dx = s.x - px, dz = s.z - pz;
      if (dx * dx + dz * dz <= DISCOVER_RANGE * DISCOVER_RANGE) {
        discovered.add(k);
        enqueueToast({ glyph: m.glyph, text: structName(s) + ' を発見！', label: m.big ? 'NEW LANDMARK' : '発見', color: m.color });
      }
    }
  }
  function spawnToastEl(t) {
    const e = el('div', '', dom.toastWrap); e.className = 'ui-toast';
    e.style.borderColor = t.color || '#fff';
    e.style.boxShadow = `0 0 14px ${(t.color || '#fff')}55, 0 3px 10px rgba(0,0,0,.5)`;
    const g = el('span', '', e); g.className = 'tg'; g.textContent = t.glyph || '📍';
    const tx = el('span', '', e); tx.textContent = t.text || '';
    if (t.label) { const l = el('span', '', e); l.className = 'tl'; l.textContent = t.label; }
    return { el: e, life: 0, ttl: 3.6 };
  }
  function stepToasts(dt) {
    if (!dom) return;
    while (toasts.length < MAX_TOAST_SHOWN && toastQueue.length) toasts.push(spawnToastEl(toastQueue.shift()));
    for (let i = toasts.length - 1; i >= 0; i--) {
      const t = toasts[i]; t.life += dt;
      const k = t.life / t.ttl;
      if (k >= 1) { t.el.remove(); toasts.splice(i, 1); continue; }
      let op = 1, ty = 0;
      if (k < 0.12) { const e = k / 0.12; op = e; ty = (1 - e) * -16; }          // スライドイン
      else if (k > 0.84) { const e = (k - 0.84) / 0.16; op = 1 - e; ty = e * -10; } // フェードアウト
      t.el.style.opacity = op.toFixed(3);
      t.el.style.transform = `translateY(${ty.toFixed(1)}px)`;
    }
  }

  // =====================================================================
  // ① 仲間（コンパニオン）ステータス＆指示
  //   ・主経路: state().companions = [ { id, name, hp, maxHp, icon?/glyph?, order?, color?, dead? }, … ]（最大3人表示）
  //       order: 'follow'(追従) | 'wait'(待機) | 'attack'(攻撃)。不在/空で非表示（1号機未実装の間は休止）。
  //   ・指示: ボタン押下で window.VoxelGame.commandCompanion(id, order) を呼ぶ（在庫/AIはcore側）。
  //   ・加入/離脱トーストは id 差分で自動。明示通知は window.onCompanionJoin/Leave（push経路・重複は抑止）。
  // =====================================================================
  const COMP_MAX = 3;
  const ORDER_META = [
    { id: 'follow', label: '追従', glyph: '🐾' },
    { id: 'wait',   label: '待機', glyph: '✋' },
    { id: 'attack', label: '攻撃', glyph: '⚔' },
  ];
  const companionSeen = new Map();   // id -> name（加入/離脱トーストの差分検知）
  // 職業type→絵文字（icon/glyph 未指定時のアバター退避。1号機 state().companions[].type に対応）
  const JOB_GLYPH = {
    villager:'🧑', merchant:'🧑‍💼', blacksmith:'🧑‍🏭', farmer:'🧑‍🌾',
    guard:'💂', child:'🧒', elder:'🧓', baker:'🧑‍🍳',
  };
  function compId(c, i) { return (c && c.id != null) ? c.id : ('comp' + i); }
  function compGlyph(c) { return c.glyph || JOB_GLYPH[c.type] || '🧑'; }
  function callCommand(id, order) {
    const vg = window.VoxelGame;
    if (vg && typeof vg.commandCompanion === 'function') { try { vg.commandCompanion(id, order); return true; } catch (e) {} }
    return false;
  }
  function compToast(name, join) {
    enqueueToast(join
      ? { glyph: '🤝', text: (name || '仲間') + ' が仲間になった！', label: 'JOIN', color: '#7be08a' }
      : { glyph: '💨', text: (name || '仲間') + ' が離脱した', label: 'LEAVE', color: '#bcb6c8' });
  }
  function buildCompCard() {
    const root = el('div', '', dom.companions); root.className = 'ui-comp';
    const top = el('div', '', root); top.className = 'ui-comp-top';
    const ava = el('div', '', top); ava.className = 'ui-comp-ava';
    const mid = el('div', '', top); mid.className = 'ui-comp-mid';
    const name = el('div', '', mid); name.className = 'ui-comp-name';
    const hpbar = el('div', '', mid); hpbar.className = 'ui-comp-hpbar';
    const hpfill = el('div', '', hpbar); hpfill.className = 'ui-comp-hpfill';
    const hpnum = el('div', '', mid); hpnum.className = 'ui-comp-hpnum';
    const cmds = el('div', '', root); cmds.className = 'ui-comp-cmds';
    const card = { root, ava, name, hpfill, hpnum, cmds: {}, id: null, avaKey: null };
    ORDER_META.forEach((o) => {
      const b = el('div', '', cmds); b.className = 'ui-comp-cmd';
      const g = el('span', '', b); g.className = 'cg'; g.textContent = o.glyph;
      el('span', '', b).textContent = o.label;
      b.addEventListener('click', (e) => { e.stopPropagation(); if (card.id != null) callCommand(card.id, o.id); });
      card.cmds[o.id] = b;
    });
    return card;
  }
  function paintCompanions(st) {
    if (!dom || !dom.companions) return;
    const list = Array.isArray(st.companions) ? st.companions.slice(0, COMP_MAX) : [];

    // 加入/離脱トースト（id 差分・防御的）
    const cur = new Map();
    list.forEach((c, i) => cur.set(compId(c, i), (c && c.name) || ''));
    for (const [id, nm] of cur) if (!companionSeen.has(id)) { companionSeen.set(id, nm); compToast(nm, true); }
    for (const [id, nm] of Array.from(companionSeen)) if (!cur.has(id)) { companionSeen.delete(id); compToast(nm, false); }

    if (!list.length) { if (dom.companions.classList.contains('on')) dom.companions.classList.remove('on'); return; }
    dom.companions.classList.add('on');

    while (dom.compCards.length < list.length) dom.compCards.push(buildCompCard());
    for (let i = 0; i < dom.compCards.length; i++) {
      const card = dom.compCards[i], c = list[i];
      if (!c) { card.root.style.display = 'none'; continue; }
      card.root.style.display = '';
      card.id = compId(c, i);

      // アイコン（4号機アイコン優先・無ければ職業type/絵文字に退避）
      const url = iconUrl(c);
      const gly = compGlyph(c);
      const key = url || gly || c.name || '';
      if (key !== card.avaKey) {
        card.avaKey = key;
        if (url) { card.ava.style.backgroundImage = `url("${url}")`; card.ava.textContent = ''; }
        else { card.ava.style.backgroundImage = ''; card.ava.textContent = gly; }
      }
      card.name.textContent = c.name || ('仲間' + (i + 1));
      if (c.color) card.name.style.color = c.color; else card.name.style.color = '';

      const maxHp = (typeof c.maxHp === 'number' && c.maxHp > 0) ? c.maxHp : 20;
      const hp = clampN(c.hp); const ratio = clamp01(hp / maxHp);
      card.hpfill.style.width = (ratio * 100).toFixed(1) + '%';
      card.hpfill.className = 'ui-comp-hpfill' + (ratio < 0.3 ? ' low' : ratio < 0.6 ? ' mid' : '');
      card.hpnum.textContent = `${hp}/${maxHp}`;
      const dead = !!c.dead || hp <= 0;
      card.root.classList.toggle('dead', dead);

      // 指示ボタンのアクティブ表示（1号機は cmdMode を state().companions[].mode で出す＝order の別名）
      const order = c.order || c.mode || 'follow';
      ORDER_META.forEach((o) => card.cmds[o.id].classList.toggle('on', o.id === order));
    }
    for (let i = list.length; i < dom.compCards.length; i++) dom.compCards[i].root.style.display = 'none';
  }

  // =====================================================================
  // ボスHPバー
  //   ・主経路: state().boss = { name, hp, maxHp, color?, phase?, maxPhase?, id? }（不在=null/undefined で非表示）
  //   ・push経路: window.onBossEncounter(boss) / onBossUpdate(boss) / onBossDefeated(boss)
  //     （state を出さない実装でも push だけで動く。最終更新から ~10s で自動フェード）
  // =====================================================================
  let bossPushed = null, bossPushLife = 0;   // push 経路のキャッシュと寿命
  let bossSeenId = null, bossLastRatio = 1;  // 出現/撃破の遷移検知用
  let bossBannerT = 0;                        // 出現/撃破バナーの寿命
  function bossId(b) { return b ? (b.id != null ? b.id : (b.name || 'boss')) : null; }
  function setBossPush(b) { bossPushed = b || null; bossPushLife = b ? 10 : 0; }
  function bossBanner(text, color) {
    if (!dom || !dom.bossBan) return;
    dom.bossBan.textContent = text; dom.bossBan.style.color = color || '#ff5a6e';
    bossBannerT = 1.25; skillFlashT = Math.max(skillFlashT, 0.4); impactShake(0.4, true);
  }
  function renderBossPips(n, cur) {
    if (dom.bossPipN === n) { // 数は据え置き、点灯のみ更新
      for (let i = 0; i < dom.bossPips.children.length; i++)
        dom.bossPips.children[i].className = 'pip' + (i < cur ? ' on' : '');
      return;
    }
    dom.bossPips.innerHTML = ''; dom.bossPipN = n;
    for (let i = 0; i < n; i++) { const p = el('div', '', dom.bossPips); p.className = 'pip' + (i < cur ? ' on' : ''); }
  }
  function stepBoss(dt, st) {
    if (!dom) return;
    if (bossPushLife > 0) bossPushLife = Math.max(0, bossPushLife - dt);
    const boss = (st && st.boss) ? st.boss : (bossPushLife > 0 ? bossPushed : null);
    const id = bossId(boss);

    // --- 出現/撃破の遷移 ---
    if (id && id !== bossSeenId) {                       // 新ボス出現
      bossSeenId = id; bossLastRatio = 1;
      bossBanner('⚔ ' + (boss.name || 'ボス') + ' 出現！', boss.color || '#ff5a6e');
    } else if (!id && bossSeenId) {                      // state/push から消滅
      if (bossLastRatio < 0.15) bossBanner('✦ 撃破！', '#ffe24a'); // 瀕死で消えた＝撃破とみなす
      bossSeenId = null;
    }

    if (!boss) { if (dom.boss.style.display !== 'none') dom.boss.style.display = 'none'; stepBossBanner(dt); return; }
    dom.boss.style.display = 'flex';

    const max = (boss.maxHp > 0) ? boss.maxHp : Math.max(boss.hp || 1, 1);
    const hp = Math.max(0, Math.min(max, (boss.hp != null) ? boss.hp : max));
    const ratio = max > 0 ? hp / max : 0;
    bossLastRatio = ratio;
    dom.bossName.textContent = boss.name || 'ボス';
    if (boss.color) dom.bossName.style.textShadow = `0 0 10px ${boss.color}, 0 2px 4px #000`;
    dom.bossFill.style.width = (ratio * 100).toFixed(1) + '%';
    dom.bossNum.textContent = Math.ceil(hp) + ' / ' + max;
    dom.boss.classList.toggle('low', ratio < 0.25);

    const maxPhase = (boss.maxPhase > 1) ? Math.min(boss.maxPhase, 10) : 0;
    if (maxPhase) { dom.bossPips.style.display = 'flex'; renderBossPips(maxPhase, clampN(boss.phase || 0)); }
    else if (dom.bossPipN !== 0) { dom.bossPips.innerHTML = ''; dom.bossPipN = 0; dom.bossPips.style.display = 'none'; }

    stepBossBanner(dt);
  }
  function stepBossBanner(dt) {
    if (!dom || !dom.bossBan) return;
    if (bossBannerT > 0) {
      bossBannerT = Math.max(0, bossBannerT - dt * 0.7);
      const e = 1 - bossBannerT;
      const sc = 0.7 + clamp01(e / 0.14) * 0.45;
      const op = e < 0.1 ? e / 0.1 : (bossBannerT < 0.3 ? bossBannerT / 0.3 : 1);
      dom.bossBan.style.opacity = clamp01(op).toFixed(3);
      dom.bossBan.style.transform = `translate(-50%,-50%) scale(${sc.toFixed(3)})`;
    } else if (dom.bossBan.style.opacity !== '0') {
      dom.bossBan.style.opacity = '0';
    }
  }

  // =====================================================================
  // ダメージ／回復演出
  // =====================================================================
  let hurtT = 0, healT = 0, lastHp = null, levelUpT = 0;
  function flashDamage(amount) {
    hurtT = Math.min(1, 0.45 + clamp01((amount || 1) / 12) * 0.55);
  }
  function flashHeal() { healT = 0.7; }

  // 画面シェイク：本命はコアのカメラ揺れ（window.VoxelGame.shake）。無ければ HUD を軽く揺らす。
  //   通常攻撃ではフォールバックHUD揺れを抑え（うるさいので）、会心/必殺/被弾だけ許可。
  function impactShake(intensity, allowFallback) {
    const vg = window.VoxelGame;
    if (vg && typeof vg.shake === 'function') { try { vg.shake(intensity); return; } catch (e) {} }
    if (allowFallback) shakeT = Math.max(shakeT, Math.min(0.5, intensity));
  }

  // レベルアップ祝祭演出（1号機 core が window.onLevelUp(level) を呼ぶ）
  function doLevelUp(level) {
    if (!dom) return;
    if (dom.lu2) dom.lu2.textContent = 'Lv ' + clampN(level);
    levelUpT = 1; // バナーの寿命（tick で 0 へ）
    // 画面中央に金色の大バースト（fx canvas）
    hits.push({ x: innerWidth / 2, y: innerHeight * 0.36, life: 0, ttl: 0.7, kind: 'level', crit: true, ang: 0 });
    hits.push({ x: innerWidth / 2, y: innerHeight * 0.36, life: -0.12, ttl: 0.8, kind: 'level', crit: true, ang: 0 });
  }

  // ===== 必殺技：発動演出（全画面FX・技別）／習得通知 =====
  //   onUseSkill(skillId, opts?) / onLearnSkill(skill) を ui.js が定義、core が呼ぶ。
  //   opts = { name, kind:'nova'|'beam'|'slash'|'buff', color }
  const SKILL_KINDS = ['nova', 'beam', 'slash', 'buff'];
  const SKILL_COLORS = { nova: '#7ab8ff', beam: '#ff6bd0', slash: '#ffd54a', buff: '#7cff9b' };
  const skillFx = []; // {kind, color, life, ttl}
  let skillNameT = 0, skillFlashT = 0, shakeT = 0;
  function doUseSkill(skillId, opts) {
    if (!dom) return;
    opts = opts || {};
    const kind = SKILL_KINDS.indexOf(opts.kind) >= 0 ? opts.kind : 'nova';
    const color = opts.color || SKILL_COLORS[kind] || '#7ab8ff';
    skillFx.push({ kind, color, life: 0, ttl: 0.9 });
    skillFlashT = 0.6; impactShake(0.55, true);
    if (opts.name && dom.sk1) {
      dom.sk1.textContent = opts.name; dom.sk1.style.color = color;
      dom.sk2.textContent = '必殺技';
      skillNameT = 1;
    }
  }
  function doLearnSkill(skill) {
    if (!dom) return;
    skill = skill || {};
    if (dom.sk1) { dom.sk1.textContent = '✦ 新必殺技 習得！'; dom.sk1.style.color = '#ffe24a'; }
    if (dom.sk2) dom.sk2.textContent = skill.name || '';
    skillNameT = 1.2;
    skillFx.push({ kind: 'nova', color: '#ffe24a', life: 0, ttl: 0.9 });
  }

  // コアの既存フックに相乗り（コア改変不要）
  function hookDamage() {
    const prev = window.onPlayerHurt;
    window.onPlayerHurt = function (cause, amount) {
      try { if (typeof prev === 'function') prev(cause, amount); } catch (e) {}
      flashDamage(amount);
    };
    // ③ 死亡口（ui.jsが定義・core が呼ぶ＝dormant 受け皿）。core が即respawnを止めて呼ぶようになると発火
    const prevDeath = window.onPlayerDeath;
    window.onPlayerDeath = function (info) {
      try { if (typeof prevDeath === 'function') prevDeath(info); } catch (e) {}
      showGameOver(info);
    };
    // レベルアップ口（ui.jsが定義・coreは呼ぶだけ）。既存があれば相乗り
    const prevLU = window.onLevelUp;
    window.onLevelUp = function (level) {
      try { if (typeof prevLU === 'function') prevLU(level); } catch (e) {}
      doLevelUp(level);
    };
    // 必殺技 発動／習得（ui.jsが定義・coreは呼ぶだけ）
    const prevUse = window.onUseSkill;
    window.onUseSkill = function (skillId, opts) {
      try { if (typeof prevUse === 'function') prevUse(skillId, opts); } catch (e) {}
      doUseSkill(skillId, opts);
    };
    const prevLearn = window.onLearnSkill;
    window.onLearnSkill = function (skill) {
      try { if (typeof prevLearn === 'function') prevLearn(skill); } catch (e) {}
      doLearnSkill(skill);
    };
    // ボスHPバー push 口（ui.jsが定義・coreは呼ぶだけ。state().boss を使うなら未使用でも可）
    const prevBe = window.onBossEncounter;
    window.onBossEncounter = function (boss) {
      try { if (typeof prevBe === 'function') prevBe(boss); } catch (e) {}
      setBossPush(boss); // 出現バナーは stepBoss の id 遷移検知が自動で出す
    };
    const prevBu = window.onBossUpdate;
    window.onBossUpdate = function (boss) {
      try { if (typeof prevBu === 'function') prevBu(boss); } catch (e) {}
      setBossPush(boss); // 寿命を更新（HP変化の反映）
    };
    const prevBd = window.onBossDefeated;
    window.onBossDefeated = function (boss) {
      try { if (typeof prevBd === 'function') prevBd(boss); } catch (e) {}
      bossBanner('✦ ' + ((boss && boss.name) || 'ボス') + ' 撃破！', '#ffe24a');
      hits.push({ x: innerWidth / 2, y: innerHeight * 0.32, life: 0, ttl: 0.8, kind: 'level', crit: true, ang: 0 });
      bossPushed = null; bossPushLife = 0; bossSeenId = null; bossLastRatio = 1;
    };
    // 構造物 発見 push 口（任意。自動検知と併用可・キーで重複抑止）
    const prevDisc = window.onDiscover;
    window.onDiscover = function (info) {
      try { if (typeof prevDisc === 'function') prevDisc(info); } catch (e) {}
      info = info || {};
      const m = STRUCT_META[info.type] || {};
      const k = info.type ? ('push:' + info.type + ':' + (info.name || '')) : ('push:' + (info.name || info.text || ''));
      if (discovered.has(k)) return;
      discovered.add(k);
      enqueueToast({
        glyph: info.glyph || m.glyph || '📍',
        text: info.text || ((info.name || m.name || '構造物') + ' を発見！'),
        label: info.label || (m.big ? 'NEW LANDMARK' : '発見'),
        color: info.color || m.color || '#fff',
      });
    };
    // ① 仲間 加入/離脱 push 口（任意。state().companions の自動検知と併用可・id で重複抑止）
    const prevCJ = window.onCompanionJoin;
    window.onCompanionJoin = function (c) {
      try { if (typeof prevCJ === 'function') prevCJ(c); } catch (e) {}
      c = c || {}; const id = c.id != null ? c.id : (c.name || 'comp');
      if (companionSeen.has(id)) return;       // 既知（自動検知済み）なら二重トーストしない
      companionSeen.set(id, c.name || ''); compToast(c.name, true);
    };
    const prevCL = window.onCompanionLeave;
    window.onCompanionLeave = function (c) {
      try { if (typeof prevCL === 'function') prevCL(c); } catch (e) {}
      c = c || {}; const id = c.id != null ? c.id : (c.name || 'comp');
      const nm = companionSeen.get(id);
      if (!companionSeen.has(id)) return;
      companionSeen.delete(id); compToast(c.name || nm, false);
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

    // 手応え：会心は特大＋強シェイク、通常は控えめ、被弾は赤フラッシュ＋中シェイク
    if (self) { flashDamage(Math.abs(amt)); impactShake(0.28, true); }
    else if (heal) { /* 回復はシェイクなし */ }
    else if (crit) impactShake(0.34, true);
    else impactShake(0.13 + clamp01(amt / 20) * 0.12, false); // 通常はコアのカメラ揺れがある時だけ
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
      if (k < 0) continue; // 出現を少し遅らせる二重リング用（life 負スタート）
      if (k >= 1) { hits.splice(i, 1); continue; }
      const a = clamp01(1 - k);
      ctx.save();
      ctx.translate(h.x, h.y);
      if (h.kind === 'level') {
        // レベルアップ：大きな金色の拡散リング
        const lr = 40 + k * 150;
        ctx.globalAlpha = a * 0.85;
        ctx.strokeStyle = '#ffe24a'; ctx.lineWidth = 4;
        ctx.beginPath(); ctx.arc(0, 0, lr, 0, Math.PI * 2); ctx.stroke();
        ctx.globalAlpha = a * 0.5; ctx.strokeStyle = '#fff6c8'; ctx.lineWidth = 2;
        ctx.beginPath(); ctx.arc(0, 0, lr * 0.7, 0, Math.PI * 2); ctx.stroke();
        ctx.restore(); continue;
      }
      const col = h.kind === 'heal' ? '#7cff9b' : (h.crit ? '#ffec5c' : '#fff2cc');
      // 命中の白い閃光（インパクト）：序盤に強く光る
      const fa = clamp01(1 - k / 0.4);
      if (fa > 0) {
        ctx.globalAlpha = fa * (h.crit ? 0.85 : 0.6);
        ctx.fillStyle = '#fff';
        ctx.beginPath(); ctx.arc(0, 0, (h.crit ? 18 : 10) * (1 - k), 0, Math.PI * 2); ctx.fill();
      }
      const r = (h.crit ? 40 : 18) * (0.4 + k * 1.4);
      // 放射状の閃光リング
      ctx.globalAlpha = a * 0.9;
      ctx.strokeStyle = col;
      ctx.lineWidth = h.crit ? 4 : 2;
      ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.stroke();
      // 斬撃線（会心は大きく・二重線）
      ctx.globalAlpha = a;
      ctx.rotate(h.ang);
      const len = (h.crit ? 40 : 15) * (0.6 + k);
      ctx.lineWidth = h.crit ? 4 : 2; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(-len, 0); ctx.lineTo(len, 0); ctx.stroke();
      if (h.crit) { ctx.globalAlpha = a * 0.6; ctx.strokeStyle = '#fff';
        ctx.beginPath(); ctx.moveTo(-len * 0.7, 0); ctx.lineTo(len * 0.7, 0); ctx.stroke(); }
      ctx.restore();
    }

    // --- レベルアップ祝祭バナー ---
    if (dom.levelup) {
      if (levelUpT > 0) {
        levelUpT = Math.max(0, levelUpT - dt * 0.6); // 約1.7秒
        const e = 1 - levelUpT;                       // 経過 0→1
        const sc = 0.6 + clamp01(e / 0.18) * 0.4 + Math.sin(clamp01(e) * Math.PI) * 0.06;
        const op = e < 0.12 ? e / 0.12 : (levelUpT < 0.25 ? levelUpT / 0.25 : 1);
        dom.levelup.style.opacity = clamp01(op).toFixed(3);
        dom.levelup.style.transform = `translate(-50%,-50%) scale(${sc.toFixed(3)})`;
      } else if (dom.levelup.style.opacity !== '0') {
        dom.levelup.style.opacity = '0';
      }
    }

    // --- 必殺技：発動演出（全画面FX・技別）---
    const cx = innerWidth / 2, cy = innerHeight / 2;
    for (let i = skillFx.length - 1; i >= 0; i--) {
      const f = skillFx[i]; f.life += dt;
      const k = f.life / f.ttl;
      if (k >= 1) { skillFx.splice(i, 1); continue; }
      const a = clamp01(1 - k);
      ctx.save();
      ctx.globalAlpha = a;
      ctx.strokeStyle = f.color; ctx.fillStyle = f.color;
      if (f.kind === 'nova') {
        for (let r = 0; r < 3; r++) { ctx.globalAlpha = a * (0.8 - r * 0.2); ctx.lineWidth = 6 - r * 1.5;
          ctx.beginPath(); ctx.arc(cx, cy, (40 + r * 50) + k * (innerWidth * 0.7), 0, Math.PI * 2); ctx.stroke(); }
      } else if (f.kind === 'beam') {
        const h = innerHeight * (0.18 + Math.sin(clamp01(k) * Math.PI) * 0.16);
        ctx.globalAlpha = a * 0.85; ctx.fillRect(0, cy - h / 2, innerWidth, h);
        ctx.globalAlpha = a; ctx.fillStyle = '#fff'; ctx.fillRect(0, cy - h * 0.12, innerWidth, h * 0.24);
      } else if (f.kind === 'slash') {
        ctx.globalAlpha = a; ctx.lineWidth = 10 + 30 * Math.sin(clamp01(k) * Math.PI);
        ctx.lineCap = 'round'; ctx.beginPath();
        ctx.moveTo(-50, innerHeight * 0.15 + k * 60); ctx.lineTo(innerWidth + 50, innerHeight * 0.85 - k * 60); ctx.stroke();
      } else { // buff：中心から立ち上るオーラ
        for (let r = 0; r < 3; r++) { ctx.globalAlpha = a * (0.5 - r * 0.12);
          ctx.beginPath(); ctx.arc(cx, cy + innerHeight * 0.18, (60 + r * 40) * (0.5 + k), Math.PI, 0); ctx.stroke(); }
      }
      ctx.restore();
    }
    // 発動時の全画面フラッシュ
    skillFlashT = Math.max(0, skillFlashT - dt * 2.4);
    if (skillFlashT > 0) {
      ctx.save(); ctx.globalAlpha = skillFlashT * 0.5; ctx.fillStyle = '#fff';
      ctx.fillRect(0, 0, innerWidth, innerHeight); ctx.restore();
    }

    // --- スキル名／習得バナー ---
    if (dom.skillname) {
      if (skillNameT > 0) {
        skillNameT = Math.max(0, skillNameT - dt * 0.6);
        const e = 1 - skillNameT;
        const sc = 0.7 + clamp01(e / 0.14) * 0.45;
        const op = e < 0.1 ? e / 0.1 : (skillNameT < 0.3 ? skillNameT / 0.3 : 1);
        dom.skillname.style.opacity = clamp01(op).toFixed(3);
        dom.skillname.style.transform = `translate(-50%,-50%) scale(${sc.toFixed(3)})`;
      } else if (dom.skillname.style.opacity !== '0') {
        dom.skillname.style.opacity = '0';
      }
    }

    // --- 画面シェイク（FXレイヤー＋HUDを軽く揺らす＝インパクト）---
    shakeT = Math.max(0, shakeT - dt * 2);
    if (shakeT > 0 && dom.root) {
      const m = shakeT * 9, ph = f0 += dt * 60; // 決定的（乱数不使用）
      const ox = Math.sin(ph) * m, oy = Math.cos(ph * 1.3) * m;
      dom.root.style.transform = `translate(${ox.toFixed(1)}px,${oy.toFixed(1)}px)`;
    } else if (dom.root && dom.root.style.transform) {
      dom.root.style.transform = '';
    }
  }
  let f0 = 0;

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

  // 照準を出してよい「実プレイ中」か判定（堅牢・出す方向に倒す）。
  //   ・自前インベントリ/メニューを開いている間は出さない（閉じれば自動復活）。
  //   ・ポインタロック中なら確実にプレイ中＝出す（一人称/三人称は不問・両方で出る）。
  //   ・ロック前後でも、コアのスタート/再開オーバーレイが外れていれば出す。
  //   ・タイトル表示中（overlay が見えている）だけ確実に抑止する。
  function gameActive() {
    if (invOpen || menuOpen) return false;
    if (document.pointerLockElement) return true;          // 明確に操作中
    if (touchOn) return true;                              // スマホはロック不使用
    try {
      const o = document.getElementById('overlay');
      if (o && o.style && o.style.display === 'none') return true; // オーバーレイが外れている＝プレイ中
    } catch (e) {}
    return false;
  }

  // equip デバッグ表示：window.getEquipDebug() の値を一目で（剣のworld向き・盾のworld Y）。
  // 口が無くても localStorage voxel_ui_equipdebug='1' で枠だけ "—" 点灯でき、口が値を返せば自動点灯。
  let equipDbgForce = null;
  function readEquipDbgForce() {
    if (equipDbgForce === null) { try { equipDbgForce = localStorage.getItem('voxel_ui_equipdebug') === '1'; } catch (e) { equipDbgForce = false; } }
    return equipDbgForce;
  }
  function dbgNum(n) { return (typeof n === 'number' && isFinite(n)) ? n.toFixed(2) : null; }
  function dbgVec(v) {
    if (!v) return null;
    const a = Array.isArray(v) ? v : [v.x, v.y, v.z];
    if (a.length < 3 || a.some(x => typeof x !== 'number' || !isFinite(x))) return null;
    return '(' + a.map(x => (x >= 0 ? ' ' : '') + x.toFixed(2)).join(', ') + ')';
  }
  function updateEquipDebug() {
    const elx = dom && dom.equipdbg; if (!elx) return;
    const fn = window.getEquipDebug;
    const hasFn = typeof fn === 'function';
    if (!hasFn && !readEquipDbgForce()) { if (elx.style.display !== 'none') elx.style.display = 'none'; return; }
    if (elx.style.display !== 'block') elx.style.display = 'block';

    let d = null;
    if (hasFn) { try { d = fn(); } catch (e) { d = null; } }
    const sword = d && d.sword, shield = d && d.shield;
    const sdir = sword ? dbgVec(sword.dir) : null;
    const sang = sword ? dbgNum(sword.angle) : null;
    const sy = shield ? dbgNum(typeof shield.worldY === 'number' ? shield.worldY : (shield && shield.y)) : null;

    const dash = '<span class="dim">—</span>';
    const build = d && typeof d.build === 'string' ? ` <span class="dim">${d.build}</span>` : '';
    elx.innerHTML =
      `<span class="t">⚙ equip</span>${build}<br>` +
      `<span class="k">剣 dir</span> ${sdir || dash}${sang != null ? ` <span class="k">∠</span>${sang}°` : ''}<br>` +
      `<span class="k">盾 Y&nbsp;&nbsp;</span>${sy || dash}` +
      (!hasFn ? `<br><span class="dim">getEquipDebug() 待ち</span>` : '');
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
      if (dom) { dom.root.style.display = 'none'; if (dom.cross) dom.cross.classList.remove('on'); } // 照準は root 外なので明示的に消す
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

    // --- Lv/EXP バー（state().level がある時だけ表示） ---
    if (typeof st.level === 'number') {
      dom.expRow.style.display = '';
      dom.explv.textContent = 'Lv ' + clampN(st.level);
      const need = (typeof st.expToNext === 'number' && st.expToNext > 0) ? st.expToNext : 0;
      const cur = clampN(st.exp);
      const ratio = need > 0 ? clamp01(cur / need) : 0;
      dom.expfill.style.width = (ratio * 100).toFixed(1) + '%';
      dom.expnum.textContent = need > 0 ? `${cur}/${need}` : '';
    } else if (dom.expRow.style.display !== 'none') {
      dom.expRow.style.display = 'none';
    }

    // --- 必殺技 HUD（state().skills がある時だけ） ---
    if (st.skills) paintSkills(st.skills);
    else { dom.skills.style.display = 'none'; dom.ult.style.display = 'none'; }

    // --- レーダー＆情報 ---
    paintRadar(st);

    // --- 仲間ステータス（state().companions が来たら自動点灯） ---
    paintCompanions(st);

    // --- ボスHPバー＆構造物発見トースト ---
    stepBoss(dt, st);
    checkDiscovery(st);
    stepToasts(dt);

    // --- 照準（クロスヘア）：プレイ中のみ最前面・中央に表示 ---
    if (dom.cross) dom.cross.classList.toggle('on', gameActive());
    const time = st.time || {};
    const hh = String(clampN(time.hh)).padStart(2, '0'), mm = String(clampN(time.mm)).padStart(2, '0');
    dom.info.innerHTML =
      `<span class="b">${hh}:${mm}</span> ${time.phase || ''} / ${st.weather || ''}<br>` +
      `${st.biome || ''}${st.riding ? ' 🐴騎乗' : ''}`;

    // --- equip デバッグ表示（剣のworld向き・盾のworld Y）---
    updateEquipDebug();

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

    // --- ④ スティック保持中は毎フレーム移動を再送（傾けっぱなし対応）。
    //   input.move 提供時はもちろん、WASD 合成キー経路でも再送して左右(A/D)の取りこぼしを防ぐ。
    //   setKey は heldKeys でガードされ冪等なので、同一状態の連続呼び出しはイベントを発火しない。 ---
    if (touchOn && stickId !== null) applyStick();

    // --- ② 「話す」ボタン：近くに住人NPCが居る時だけ表示（会話中=メニュー開は隠す）。core 近接判定に追従 ---
    if (touchOn && dom.talkWrap) {
      let near = false;
      const p = st.pos, list = Array.isArray(st.mobs) ? st.mobs : [];
      if (p && !menuOpen && !invOpen) {
        for (const m of list) {
          if (!TALKABLE_TYPES.has(m.type)) continue;
          const dx = m.x - p.x, dz = m.z - p.z;
          if (dx * dx + dz * dz <= TALK_RANGE * TALK_RANGE) { near = true; break; }
        }
      }
      dom.talkWrap.classList.toggle('show', near);
    }
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
    window.UI.open = (which, data) => {
      window.UI._routed = true;
      if (which === 'trade') openTrade(data);
      else if (which === 'menu' || which === 'settings' || which === 'slots' || which === 'skills') openMenu(which === 'menu' ? 'menu' : which);
      else openInv();
    };
    window.UI.openTrade = (session) => { window.UI._routed = true; openTrade(session); };
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
    // ボス／発見トーストの簡易口（state() 不使用でも呼べる別名）
    window.UI.boss = (boss) => setBossPush(boss);                 // null で消す
    window.UI.bossDefeated = (boss) => window.onBossDefeated(boss);
    window.UI.discover = (info) => window.onDiscover(info);
    window.UI.toast = (text, opts) => { opts = opts || {}; enqueueToast({ glyph: opts.glyph || '📍', text: text || '', label: opts.label || '', color: opts.color || '#fff' }); };
    // ① 仲間 加入/離脱の簡易口（state() 不使用でも呼べる別名）
    window.UI.companionJoin = (c) => window.onCompanionJoin(c);
    window.UI.companionLeave = (c) => window.onCompanionLeave(c);

    // ④ PC：Tab でステータス画面を開閉（core は Tab 未使用。フォーカス移動を抑止）
    document.addEventListener('keydown', (e) => {
      if (e.code !== 'Tab' || !coreIntegrated()) return;
      e.preventDefault();
      window.UI._routed = true;
      (menuOpen && menuScreen === 'status') ? closeMenu() : openMenu('status');
    });

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
