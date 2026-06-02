# UI 統合契約（3号機 ⇄ 1号機 / 2号機）

`ui.js`（3号機・UI/HUD担当）は **コア（index.html）を一切改変せず**、読み取り口経由でのみ
状態を受け取り、画面表示に専念します。本書はそのための最小の連携仕様です。

`ui.js` は **classic script 1本**（ESM ではない）。自前で `<style>` を注入するので CSS の追加配線は不要。

---

## 1号機にお願いしたい3点（いずれも index.html 側・各1〜数行）

### (1) スクリプトの読み込み（1行）
`sound.js` の直後に追加してください。module より前で構いません（ui.js は `DOMContentLoaded` と
`window.VoxelGame` の出現をポーリングして自走します）。

```html
<script src="sound.js"></script>
<script src="ui.js"></script>   <!-- ← 追加（3号機・UI） -->
```

### (2) ライブ状態の読み取り口 `window.VoxelGame.state()`
既存の `window.VoxelGame`（save/list/switchSlot…）に **`state` を1つ追加**してください。
毎フレーム呼ばれても軽いよう、**スナップショットを1オブジェクトで返す**だけです。
全フィールド任意（欠けていれば ui.js 側でフォールバック）。

```js
window.VoxelGame.state = () => ({
  hp, maxHp: MAX_HP, hunger, maxHunger: MAX_HUNGER, breath, maxBreath: BREATH_MAX,
  inWater: breath < BREATH_MAX,                 // 息ゲージ表示要否の目安
  selBlock,
  // ホットバー10枠（既存 HOTBAR / NAMES / SWATCH / counts から）
  hotbar: HOTBAR.map(b => ({ block:b, name:NAMES[b], swatch:SWATCH[b], count:counts[b]||0, active:b===selBlock })),
  items:  ITEM_DEFS.map(k => ({ key:k, name:ITEM_NAMES[k], count:itemCounts[k]||0 })),
  recipes: RECIPES.map(r => ({ outName:NAMES[r.out], n:r.n, inName:NAMES[r.in], cost:r.cost, canCraft:(counts[r.in]||0)>=r.cost })),
  time: (() => { const hh=Math.floor(((dayTime+0.5)%1)*24), mm=Math.floor((((dayTime+0.5)%1)*24%1)*60);
                 return { hh, mm, phase: isNight()?'夜':isDay()?'昼':'薄明' }; })(),
  weather, biome: biomeAt(Math.floor(player.pos.x), Math.floor(player.pos.z)),
  riding: !!ridingMob, thirdPerson,
  pos: { x:player.pos.x, y:player.pos.y, z:player.pos.z }, yaw: player.yaw,
  // レーダーミニマップ用（プレイヤー相対でOK・重ければ8体程度に間引いて可）
  mobs: mobs.map(m => ({ x:m.obj.position.x, z:m.obj.position.z, hostile:!!m.hostile, type:m.def.type })),
});
```

### (3) `window.UI_TAKEOVER` で inline HUD を停止（二重描画の回避）
`ui.js` は読み込み時に `window.UI_TAKEOVER = true` を立てます。
コア側の **以下の inline 描画だけ** をこのフラグでスキップしてください（他は据え置き）。

- ハート列（`hpEl`）/ 空腹列（`hungerEl`）/ 息ゲージ（`breathEl`）の更新
- ホットバー `#hotbar`（`updateHotbar()` の `innerHTML` 書き換え）
- 被ダメージ赤フラッシュ（`hurtEl`）

最小実装例（各描画の冒頭に1行）：
```js
function updateHotbar(){ if (window.UI_TAKEOVER) return; /* …既存… */ }
// HUD更新ループ内のハート/空腹/息/hurtEl 反映も同様に if (window.UI_TAKEOVER) でスキップ
```

> 据え置きでよいもの（コアの即時フィードバックとして ui.js は触りません）:
> 診断パネル `diagEl`(H)、宝箱トースト `lootEl`、セーブ表示 `saveEl`、照準 `#crosshair`。

**(2)(3) が入るまで `ui.js` は休止**（`state()` 不在を検知して何も描画せず、コンソールに待機ログを1回出すだけ）。
よって **先に (1) だけ入れても既存表示は一切壊れません**。安全に段階導入できます。

---

## 2号機（sound.js）との口
設定画面の音量スライダーは、2号機が公開する音量口に接続予定です。希望IF（どちらでも可）:
- `window.setMasterVolume(v: 0..1)` / `window.getMasterVolume()` 、または
- `window.SFX.volume = v` 相当のプロパティ。

決まり次第 ui.js 設定画面から配線します（未実装でもスライダーは出し、値は localStorage 保持）。

---

## ui.js が公開する口（参考・コアから使う必要はありません）
- `window.UI_TAKEOVER`（bool, 上記）
- `window.UI.open('inventory'|'menu'|'settings'|'slots')` / `window.UI.close()`（②③で追加）
- ダメージ演出はコアの既存 `window.onPlayerHurt(cause, amount)` をフックして発火（コア改変不要）。
