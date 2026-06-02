# UI 統合契約（3号機 ⇄ 1号機 / 2号機）

`ui.js`（3号機・UI/HUD担当）は **コア（index.html）を一切改変せず**、読み取り口経由でのみ
状態を受け取り、画面表示に専念します。本書はそのための最小の連携仕様です。

`ui.js` は **classic script 1本**（ESM ではない）。自前で `<style>` を注入するので CSS の追加配線は不要。

---

# ★ 1号機 最短配線（これだけ・コピペ可／所要約2分）

> 下の **A〜C** を入れれば *新HUD・ダメージFX・インベントリ・設定・スロット・スマホ操作* が一斉点灯します。
> 変数名は現行 index.html（`P.maxHp` 等）に合わせ済み。既存関数 `attackMob/breakBlock/placeBlock` を流用。

### A. スクリプト追加（`sound.js` の直後・1行）
```html
<script src="ui.js"></script>
```

### B. `window.VoxelGame = { … };`（現行 L634 付近）の **直後** にこのブロックを貼る
```js
Object.assign(window.VoxelGame, {
  state: () => ({
    hp, maxHp: P.maxHp, hunger, maxHunger: P.maxHunger, breath, maxBreath: P.breathMax,
    inWater: breath < P.breathMax - 0.05, selBlock,
    hotbar: HOTBAR.map(b => ({ block:b, name:NAMES[b], swatch:SWATCH[b], count:counts[b]||0, active:b===selBlock })),
    items:  ITEM_DEFS.map(k => ({ key:k, name:ITEM_NAMES[k]||k, count:itemCounts[k]||0 })),
    recipes: RECIPES.map(r => ({ outName:NAMES[r.out], n:r.n, inName:NAMES[r.in], cost:r.cost, canCraft:(counts[r.in]||0)>=r.cost })),
    time: { hh:Math.floor(((dayTime+0.5)%1)*24), mm:Math.floor((((dayTime+0.5)%1)*24%1)*60), phase:isNight()?'夜':isDay()?'昼':'薄明' },
    weather, biome: biomeAt(Math.floor(player.pos.x), Math.floor(player.pos.z)),
    riding: !!ridingMob, thirdPerson,
    pos: { x:player.pos.x, y:player.pos.y, z:player.pos.z }, yaw: player.yaw,
    mobs: mobs.map(m => ({ x:m.obj.position.x, z:m.obj.position.z, hostile:!!m.hostile, type:m.def.type })),
  }),
  project: (x,y,z) => { const v = new THREE.Vector3(x,y,z).project(camera);
    return { x:(v.x*0.5+0.5)*innerWidth, y:(-v.y*0.5+0.5)*innerHeight, visible:v.z < 1 }; },
  selectBlock: (b) => { selBlock = b; updateHotbar(); },
  craft: (i) => { craft(RECIPES[i]); },
  input: {
    look: (dx, dy) => { player.yaw -= dx*0.0045; player.pitch = Math.max(-1.55, Math.min(1.55, player.pitch - dy*0.0045)); },
    primary:   (down) => { if (down) { if (!attackMob()) breakBlock(); } },
    secondary: (down) => { if (down) placeBlock(); },
  },
});
```
そして戦闘の命中処理で（クリティカル判定があれば `crit:true`）:
```js
window.spawnDamagePopup && window.spawnDamagePopup(mob.obj.position.x, mob.obj.position.y+1, mob.obj.position.z, dmg, { crit });
```

### C. inline HUD を `UI_TAKEOVER` でスキップ（既存の各所に1行ずつ）
| 場所（現行行） | 変更 |
|---|---|
| `function updateHotbar() {`（L1372） | 直後に `if (window.UI_TAKEOVER) return;` |
| HUD更新（L2485-2490 の `hpEl/hungerEl/hurtEl/breathEl` 反映） | 全体を `if (!window.UI_TAKEOVER) { …4行… }` で囲う |
| Eキー（L1357 `if (e.code === 'KeyE') {…}`） | `if (e.code==='KeyE'){ if(window.UI_TAKEOVER&&window.UI){window.UI.toggle('inventory');} else { invOpen?closeInventory():openInventory(); } }` |
| マウス感度（L1326 `const s = 0.0023;`） | `const s = 0.0023 * ((window.UI_SETTINGS&&window.UI_SETTINGS.sensitivity)||1);` |

任意：Escでメニュー → keydown に `if (e.code==='Escape' && window.UI_TAKEOVER && window.UI) window.UI.toggle('menu');`

> **据え置きでOK**（ui.js は触りません）: 診断H・宝箱トースト・セーブ表示・照準・タイトル色選択。
> A だけ先に入れても無害（ui.js は state() 不在の間 休止）。**B で点灯、C で二重表示を解消**、の順で安全に進められます。

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

## NPC会話／取引UI（1号機のNPC会話実装と接続）

`ui.js` が会話/取引パネルを描画します。core はNPCに話しかけた時に **`window.UI.openTrade(session)`**（または
`window.UI.open('trade', session)`）を呼ぶだけ。*取引成立は `window.VoxelGame.trade(offerId)` 経由*（在庫増減はcore）。

```js
// 話しかけたとき
window.UI.openTrade({
  npc: '商人トム', job: 'merchant',          // job: merchant/blacksmith/farmer/guard/child/elder/baker/villager（顔絵文字に使用）
  greeting: 'いらっしゃい！素材があればいい物と交換するよ。',
  offers: [
    { id:0, giveName:'コイン', giveIcon:'item_coin', giveCount:5,
            getName:'りんご', getIcon:'item_apple', getCount:2, canAfford:true },
    { id:1, giveName:'鉄',    giveIcon:'item_iron', giveCount:3,
            getName:'剣',     getIcon:'item_sword', getCount:1, canAfford:false },
  ],
});

// 取引ボタン押下で ui.js が呼ぶ（core が在庫を増減）。
// 戻り値に更新後の {offers:[...]} か session を返せば、その場で在庫/可否が再描画されます（省略可）。
window.VoxelGame.trade = (offerId) => { /* 支払い可なら itemCounts 増減 → 更新session返す */ };
```

- `giveIcon`/`getIcon` は `tools/icons` のアイコン名（例 `item_coin`・無ければ名前→アイコン→スウォッチに自動退避）。
- 取引成立音は **2号機 `playSFX('trade')`**（ui.jsが鳴らします・口が無ければ無音）。
- 口が呼ばれなければ何も出ません（dormant-safe）。Escで閉じる。

---

## ミニマップ（レーダー）の構造物表示

`state()` に **`structures`** を入れると、レーダーに*構造物マーカー*（四角）と、*範囲外の重要構造物への縁の方向矢印*が出ます（無ければ出ません）。探索の足跡（通過点）は ui.js が自動記録・点描します。
```js
structures: [ { x, z, type:'village'|'fort'|'dungeon'|'chest'|'spawner' }, … ]
// 色: village=緑 / fort=橙 / dungeon=紫 / chest=金 / spawner=赤。範囲外矢印は village/fort/dungeon のみ。
```

---

## 必殺技 連携（1号機の技ロジックと接続・三位一体の演出担当）

`ui.js` が *必殺技ゲージ・装備スキルボタン(Z X C V)・発動演出(全画面FX)・習得通知・技選択UI* を担当。

### state() に追記（あれば表示・無ければ非表示）
```js
skills: {
  energy: 0..1,                       // 必殺ゲージ（任意）
  equipped: ['fire','quake', …],      // 装備中ID（最大4・HUDボタン順）
  list: [ { id:'fire', name:'火炎斬', icon:'item_sword'/*任意*/, kind:'slash',
            color:'#ffd54a'/*任意*/, ready:true, cooldown:0/*残割合0..1*/, desc:'前方を炎で薙ぐ' }, … ],
}
```
`kind` は発動演出の種類：**`nova`(全方位放射) / `beam`(横薙ぎ閃光) / `slash`(巨大斬撃) / `buff`(オーラ)**。

### ui.js が定義する口（core は呼ぶだけ）
```js
window.onUseSkill(skillId, { name, kind, color });  // 発動演出＋技名バナー＋全画面フラッシュ＋画面シェイク
window.onLearnSkill({ name, icon });                // 「✦ 新必殺技 習得！」バナー（Lv演出と同系）
```
### ui.js が core を呼ぶ口（実装してください）
```js
window.VoxelGame.useSkill  = (skillId) => { /* 発動（ゲージ/CD消費・効果適用）→ window.onUseSkill を呼ぶ */ };
window.VoxelGame.equipSkill = (skillId) => { /* 装備のトグル（最大4） */ };
```
- スキルボタンは *ready の時だけ* 押下可（`useSkill` を呼ぶ）。キー Z/X/C/V を core 側で `useSkill(equipped[i])` に割り当ててもOK。
- 技一覧/装備は `window.UI.open('skills')`（ポーズメニューにも「⚡必殺技」）。
- 発動音は **2号機 `playSFX('skill')`**（kind別に `playSFX('skill_'+kind)` でも可）。
- レベルアップで習得する想定なら、Lvアップ処理で `window.onLearnSkill(skill)` を1行。

---

## レベルアップ連携（1号機レベルシステムと接続）

- `state()` に **`level` / `exp` / `expToNext`** を入れると、ui.js が*ホットバー上に Lv/EXP バー*を自動表示します（無ければ非表示）。
- **`window.onLevelUp(level)`** は *ui.js が定義*します（祝祭バナー＋金バースト）。core は*呼ぶだけ*（空代入で上書きしないでください）。
  - 加えて core が `playSFX('levelup')` を鳴らせば音と画面が一致（音は2号機）。

```js
// state() に追記（B のブロック内）
level: lvl, exp: curExp, expToNext: needExp,
// レベルアップ時に1行
window.onLevelUp && window.onLevelUp(lvl);
```

---

## ② インベントリ／クラフトの操作口（方針A・コア改修不要の範囲）

`ui.js` が独自のインベントリ/クラフト画面（4号機アイコン込み）を描画します。読み取りは `state()`、
**状態変更はコアの口経由のみ**（ui.js はコア変数を直接書きません）。以下を `window.VoxelGame` に追加してください。

```js
window.VoxelGame.selectBlock = (block) => { selBlock = block; updateHotbar(); };   // ブロック選択
window.VoxelGame.craft       = (i)     => { craft(RECIPES[i]); };                   // i番目のレシピを実行
```

`state().recipes[]` に **`outIcon`**（例 `'block_planks'`）を足してもらえると、クラフト結果のアイコンが出ます
（無ければ ui.js が日本語名→アイコンでフォールバックするので必須ではありません）。

### Eキーの委譲（二重オープン回避）
`UI_TAKEOVER` 時、コアの E は**自前の invEl を開かず** `window.UI.toggle('inventory')` を呼ぶだけにしてください。
ui.js 側は「`window.UI.toggle` が一度でも呼ばれたら自前のフォールバックEを止める」ので二重に開きません。
ポインタロックは ui.js が開く瞬間に `exitPointerLock()` します。閉じたあとの再ロックはコア側の既存導線（クリックで開始）でOK。

> `state()` 実装後、ui.js は右下に「E：インベントリ」のヒントを自動表示します。

---

## ③ メニュー／設定／セーブスロットの連携

`ui.js` がメニュー/設定/セーブスロット画面を描画します（`window.UI.open('menu'|'settings'|'slots')`）。

- *音量*：2号機 `window.setMasterVolume/setSfxVolume/setBgmVolume/setMuted` に配線済み（追加作業不要）。
- *セーブスロット*：1号機 `window.VoxelGame.list/current/switchSlot/newWorld/deleteSlot` に配線済み（既存口でフル機能）。
- *タイトルの色選択*：既存のコア実装（`#charsel`）をそのまま使用。ui.js は重複描画しません。

### 1号機にお願い（軽微・任意）
1. *Escの委譲*：`UI_TAKEOVER` 時、コアのEscは自前のポーズではなく `window.UI.toggle('menu')` を呼ぶ。
   （E同様、ui.js は委譲を検知して自前フォールバックを止めます）
2. *感度/画質の消費*：ui.js は設定を `window.UI_SETTINGS = { sensitivity:1.0, quality:'high'|'low' }` で公開し、
   変更時に `uisettingschange` イベントを出します。コア側で読んで反映してください：
   ```js
   // マウス移動（既存 s=0.0023 に感度を掛ける）
   const s = 0.0023 * ((window.UI_SETTINGS && window.UI_SETTINGS.sensitivity) || 1);
   // 画質（任意）：'low' のとき pixelRatio/描画半径を落とす等
   ```
   未対応でも設定値は localStorage に保存され無害です。

---

## 戦闘演出の口（1号機の戦闘実装と接続）

`ui.js` が **以下2つを定義・公開**します。1号機は命中時にこれを呼ぶだけ（演出の中身はUI側）。
**呼ばれなくても無害／呼んでも口未整備なら安全に無効化**します。

```js
window.spawnDamagePopup(x, y, z, amount, opts?)  // ダメージ数字ポップ＋命中閃光
window.spawnHitEffect(x, y, z, opts?)            // 命中点の閃光／斬撃線のみ
//   x,y,z   : 命中位置（ワールド座標）
//   amount  : ダメージ量（負値=回復扱い）
//   opts    : { crit?:bool, self?:bool, heal?:bool, screen?:bool }
//             crit=クリティカル（大きく金色＋強閃光） / self=プレイヤー被ダメ（赤フラッシュ統合）
//             screen=true のとき x,y を画面px直指定（projector無し時のフォールバック）
```

### お願い：world→screen 投影口 `window.VoxelGame.project(x,y,z)`（強く推奨・数行）
ワールド座標を画面座標へ変換するため、カメラを持つコア側に1つください。これが無いと
ポップの表示位置が出せません（`opts.screen` 直指定のフォールバックは可だが、3D命中点には不向き）。

```js
window.VoxelGame.project = (x, y, z) => {
  const v = new THREE.Vector3(x, y, z).project(camera);   // camera は既存
  return { x:(v.x*0.5+0.5)*innerWidth, y:(-v.y*0.5+0.5)*innerHeight, visible: v.z < 1 };
};
```

呼び出し例（1号機の戦闘・被ダメ処理に1行ずつ）:
```js
// モブに命中したとき（クリティカル判定があれば crit:true）
window.spawnDamagePopup && window.spawnDamagePopup(mob.obj.position.x, mob.obj.position.y+1, mob.obj.position.z, dmg, { crit });
// プレイヤーが被弾したとき（赤フラッシュは ui.js 側で統合）
window.spawnDamagePopup && window.spawnDamagePopup(player.pos.x, player.pos.y+1.2, player.pos.z, dmg, { self:true });
```

### 手応え強化（②）の任意フック
- *カメラシェイク*：`window.VoxelGame.shake(intensity 0..1)` を用意すると、ui.js は命中/会心/必殺/被弾で*本物のカメラ揺れ*を使います（無い時は HUD を軽く揺らすフォールバック）。一瞬カメラを微小オフセット→減衰で戻すだけでOK。
- *敵の白フラッシュ*：「敵が白く光る」はメッシュ着色なので*コア側*でお願いします（命中時に対象mobのmaterialを一瞬白へ）。ui.js は命中点の閃光/斬撃線/特大会心数字を担当します。
- 通常攻撃と必殺技で*演出を別格化*済み：通常=小さな閃光+控えめ、会心=特大数字(40px)+大リング+二重斬撃、必殺=全画面FX(`onUseSkill`)。

> 既存の `window.onPlayerHurt(cause, amount)` も ui.js がフックして赤フラッシュを出します（こちらは据え置きでOK）。
> `self:true` 付きで `spawnDamagePopup` を呼ぶ場合は赤フラッシュが二重にならないよう、どちらか一方で。

---

## ④ スマホ向けタッチ入力の口（1号機）

`ui.js` がタッチ端末でのみ仮想スティック＋ボタンを表示します（PCは非表示・操作不変）。

- *移動 / ジャンプ / ダッシュ* … ui.js が**合成キー(WASD/Space/ShiftLeft)を発火**するので**コア改修なしで即動作**します。
- *視点 / 破壊(攻撃) / 設置* … ポインタロックが使えないスマホでは合成マウスが効かないため、
  以下の入力口を `window.VoxelGame.input` に用意してください（未提供ならその操作だけ無効・他は動く）。

```js
window.VoxelGame.input = {
  look: (dx, dy) => { player.yaw -= dx * 0.0045; player.pitch = clamp(player.pitch - dy * 0.0045); }, // 視点デルタ(px)
  primary:   (down) => { /* 押下中フラグ。down時に breakBlock()/attackOrBreak() 相当 */ },
  secondary: (down) => { /* down時に placeBlock() 相当 */ },
  // 任意: 提供されれば移動も合成キーでなくこちらを使う（カメラ相対 x,z = -1..1）
  move: (x, z) => { /* 例: 前後左右の入力ベクトルとして使用 */ },
};
```

> `primary`/`secondary` は押しっぱなし対応のため `down=true/false` で来ます（単発なら down=true 時だけ処理）。
> 提供が無い間も、移動・ジャンプ・ダッシュ・インベントリ(🎒)・メニュー(⏸)ボタンは機能します。

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
