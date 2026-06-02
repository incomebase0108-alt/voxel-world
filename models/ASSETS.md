# VOXEL WORLD アセット一覧（自動生成）

`python tools/gen_asset_index.py` で再生成。models/ASSETS.json が機械可読版。

**規約**: Y-up / 正面 glTF -Z / 1ブロック≒1m / Draco不使用。
クリップ名は **idle / walk**（敵性=+`attack`、ボス=+`heavy`）。構造物は `idle` ＋ 固有クリップ。

**原点**: プレイヤー/モブ/NPC/構造物=足元中心 z=0 ／ 消費アイテム=形状中心 ／ 装備 剣・ピッケル・斧=柄基部・弓=握り中央・盾/防具=中心。

**合計**: 42 ファイル / 5.59 MB


## プレイヤー

| ファイル | 容量(MB) | クリップ | mesh/node |
|---|---|---|---|
| `player.glb` | 0.6617 | `idle`, `walk`, `attack` | 5/5 |
| `player_azure.glb` | 0.6620 | `idle`, `walk`, `attack` | 5/5 |
| `player_crimson.glb` | 0.6619 | `idle`, `walk`, `attack` | 5/5 |
| `player_emerald.glb` | 0.6619 | `idle`, `walk`, `attack` | 5/5 |
| `player_gold.glb` | 0.6618 | `idle`, `walk`, `attack` | 5/5 |

## モブ

| ファイル | 容量(MB) | クリップ | mesh/node |
|---|---|---|---|
| `mob_chicken.glb` | 0.1079 | `walk`, `idle`, `die`, `hit` | 7/7 |
| `mob_cow.glb` | 0.2493 | `walk`, `idle`, `die`, `hit` | 26/26 |
| `mob_golem.glb` | 0.1799 | `heavy`, `attack`, `walk`, `idle`, `die`, `hit` | 5/5 |
| `mob_horse.glb` | 0.1591 | `walk`, `idle`, `die`, `hit` | 6/6 |
| `mob_pig.glb` | 0.1115 | `walk`, `idle`, `die`, `hit` | 7/7 |
| `mob_sheep.glb` | 0.2026 | `walk`, `idle`, `die`, `hit` | 7/7 |
| `mob_skeleton.glb` | 0.2727 | `attack`, `walk`, `idle`, `die`, `hit` | 5/5 |
| `mob_slime.glb` | 0.0429 | `attack`, `walk`, `idle`, `die`, `hit` | 1/1 |
| `mob_zombie.glb` | 0.2333 | `attack`, `walk`, `idle`, `die`, `hit` | 5/5 |

## NPC

| ファイル | 容量(MB) | クリップ | mesh/node |
|---|---|---|---|
| `npc_villager.glb` | 0.2083 | `walk`, `idle`, `die`, `hit` | 5/5 |

## 構造物

| ファイル | 容量(MB) | クリップ | mesh/node |
|---|---|---|---|
| `struct_altar.glb` | 0.0281 | `idle` | 2/2 |
| `struct_chest.glb` | 0.0134 | `open` | 2/2 |
| `struct_door.glb` | 0.0124 | —（静物） | 1/1 |
| `struct_fence.glb` | 0.0072 | —（静物） | 1/1 |
| `struct_roof.glb` | 0.0036 | —（静物） | 1/1 |
| `struct_spawner.glb` | 0.0336 | `idle` | 2/2 |
| `struct_torch.glb` | 0.0113 | `idle` | 2/2 |
| `struct_wall.glb` | 0.0079 | —（静物） | 1/1 |
| `struct_well.glb` | 0.0310 | —（静物） | 1/1 |
| `struct_window.glb` | 0.0080 | —（静物） | 1/1 |

## アイテム

| ファイル | 容量(MB) | クリップ | mesh/node |
|---|---|---|---|
| `item_apple.glb` | 0.0334 | —（静物） | 1/1 |
| `item_coin.glb` | 0.0082 | —（静物） | 1/1 |
| `item_egg.glb` | 0.0273 | —（静物） | 1/1 |
| `item_meat.glb` | 0.0420 | —（静物） | 1/1 |

## 装備・道具

| ファイル | 容量(MB) | クリップ | mesh/node |
|---|---|---|---|
| `item_armor.glb` | 0.0081 | —（静物） | 1/1 |
| `item_axe.glb` | 0.0079 | —（静物） | 1/1 |
| `item_bow.glb` | 0.0098 | —（静物） | 1/1 |
| `item_pickaxe.glb` | 0.0103 | —（静物） | 1/1 |
| `item_shield.glb` | 0.0170 | —（静物） | 1/1 |
| `item_sword.glb` | 0.0131 | —（静物） | 1/1 |

## 洞窟・鉱石

| ファイル | 容量(MB) | クリップ | mesh/node |
|---|---|---|---|
| `cave_pillar.glb` | 0.0215 | —（静物） | 1/1 |
| `cave_stalactite.glb` | 0.0109 | —（静物） | 1/1 |
| `cave_stalagmite.glb` | 0.0109 | —（静物） | 1/1 |
| `ore_coal.glb` | 0.0375 | —（静物） | 1/1 |
| `ore_gem.glb` | 0.0266 | —（静物） | 1/1 |
| `ore_gold.glb` | 0.0356 | —（静物） | 1/1 |
| `ore_iron.glb` | 0.0332 | —（静物） | 1/1 |
