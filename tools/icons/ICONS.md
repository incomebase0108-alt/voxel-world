# VOXEL WORLD アイコン一覧（3号機 インベントリ/ホットバーUI 用）

`blender --background --python tools/gen_icons.py` で再生成。`tools/icons/icons.json` が機械可読版。

**仕様**: 128×128 / 透過PNG(RGBA) / 斜め45°(方位45°·仰角30°) / 余白約10% / モデルごとに枠いっぱい正規化。
サイズ/形式/アングルの変更は環境変数 `ICON_PX/ICON_AZ/ICON_EL/ICON_MARGIN` で一括再出力可。

| name | file | type |
|---|---|---|
| `item_meat` | `icon_item_meat.png` | item |
| `item_egg` | `icon_item_egg.png` | item |
| `item_coin` | `icon_item_coin.png` | item |
| `item_apple` | `icon_item_apple.png` | item |
| `item_sword` | `icon_item_sword.png` | equipment |
| `item_pickaxe` | `icon_item_pickaxe.png` | equipment |
| `item_axe` | `icon_item_axe.png` | equipment |
| `item_bow` | `icon_item_bow.png` | equipment |
| `item_shield` | `icon_item_shield.png` | equipment |
| `item_armor` | `icon_item_armor.png` | equipment |
| `block_grass` | `icon_block_grass.png` | block |
| `block_dirt` | `icon_block_dirt.png` | block |
| `block_stone` | `icon_block_stone.png` | block |
| `block_sand` | `icon_block_sand.png` | block |
| `block_wood` | `icon_block_wood.png` | block |
| `block_leaves` | `icon_block_leaves.png` | block |
| `block_planks` | `icon_block_planks.png` | block |
| `block_stonebrick` | `icon_block_stonebrick.png` | block |
| `block_glass` | `icon_block_glass.png` | block |
| `block_snow` | `icon_block_snow.png` | block |
