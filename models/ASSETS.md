# VOXEL WORLD アセット一覧（自動生成）

`python tools/gen_asset_index.py` で再生成。models/ASSETS.json が機械可読版。

**規約**: Y-up / 正面 glTF -Z / 1ブロック≒1m / Draco不使用。
クリップ名は **idle / walk**（敵性=+`attack`、ボス=+`heavy`）。構造物は `idle` ＋ 固有クリップ。

**原点**: プレイヤー/モブ/NPC/構造物=足元中心 z=0 ／ 消費アイテム=形状中心 ／ 装備 剣・ピッケル・斧=柄基部・弓=握り中央・盾/防具=中心。

**合計**: 97 ファイル / 13.83 MB


## プレイヤー

| ファイル | 容量(MB) | クリップ | mesh/node |
|---|---|---|---|
| `player.glb` | 1.0230 | `idle`, `walk`, `attack`, `swim` | 5/5 |
| `player_azure.glb` | 1.0224 | `idle`, `walk`, `attack`, `swim` | 5/5 |
| `player_crimson.glb` | 1.0224 | `idle`, `walk`, `attack`, `swim` | 5/5 |
| `player_emerald.glb` | 1.0226 | `idle`, `walk`, `attack`, `swim` | 5/5 |
| `player_gold.glb` | 1.0224 | `idle`, `walk`, `attack`, `swim` | 5/5 |

## モブ

| ファイル | 容量(MB) | クリップ | mesh/node |
|---|---|---|---|
| `mob_chicken.glb` | 0.1079 | `walk`, `idle`, `die`, `hit` | 7/7 |
| `mob_cow.glb` | 0.2493 | `walk`, `idle`, `die`, `hit` | 26/26 |
| `mob_demon.glb` | 0.4007 | `idle`, `walk`, `attack`, `heavy` | 5/5 |
| `mob_dragon.glb` | 0.3086 | `idle`, `walk`, `attack`, `heavy` | 5/5 |
| `mob_fish.glb` | 0.1255 | `idle`, `swim` | 2/2 |
| `mob_fish_koi.glb` | 0.1258 | `idle`, `swim` | 2/2 |
| `mob_fish_puffer.glb` | 0.1325 | `idle`, `swim` | 2/2 |
| `mob_fish_tropical.glb` | 0.1290 | `idle`, `swim` | 2/2 |
| `mob_golem.glb` | 0.2460 | `idle`, `walk`, `attack`, `heavy` | 5/5 |
| `mob_horse.glb` | 0.1591 | `walk`, `idle`, `die`, `hit` | 6/6 |
| `mob_pig.glb` | 0.1115 | `walk`, `idle`, `die`, `hit` | 7/7 |
| `mob_sheep.glb` | 0.2026 | `walk`, `idle`, `die`, `hit` | 7/7 |
| `mob_skeleton.glb` | 0.2962 | `idle`, `walk`, `attack` | 5/5 |
| `mob_skeleton_king.glb` | 0.3635 | `idle`, `walk`, `attack`, `heavy` | 5/5 |
| `mob_slime.glb` | 0.0429 | `attack`, `walk`, `idle`, `die`, `hit` | 1/1 |
| `mob_zombie.glb` | 0.2767 | `idle`, `walk`, `attack` | 5/5 |

## NPC

| ファイル | 容量(MB) | クリップ | mesh/node |
|---|---|---|---|
| `npc_baker.glb` | 0.2046 | `idle`, `walk`, `sit`, `work`, `talk` | 5/5 |
| `npc_blacksmith.glb` | 0.2188 | `idle`, `walk`, `sit`, `work`, `talk` | 5/5 |
| `npc_child.glb` | 0.1980 | `idle`, `walk`, `sit`, `work`, `talk` | 5/5 |
| `npc_elder.glb` | 0.2293 | `idle`, `walk`, `sit`, `work`, `talk` | 5/5 |
| `npc_farmer.glb` | 0.2132 | `idle`, `walk`, `sit`, `work`, `talk` | 5/5 |
| `npc_guard.glb` | 0.2306 | `idle`, `walk`, `sit`, `work`, `talk` | 5/5 |
| `npc_merchant.glb` | 0.2144 | `idle`, `walk`, `sit`, `work`, `talk` | 5/5 |
| `npc_soldier_captain.glb` | 0.2459 | `idle`, `walk`, `sit`, `work`, `talk`, `attack` | 5/5 |
| `npc_soldier_spear.glb` | 0.2424 | `idle`, `walk`, `sit`, `work`, `talk`, `attack` | 5/5 |
| `npc_soldier_sword.glb` | 0.2427 | `idle`, `walk`, `sit`, `work`, `talk`, `attack` | 5/5 |
| `npc_villager.glb` | 0.2112 | `idle`, `walk`, `sit`, `work`, `talk` | 5/5 |
| `npc_woman.glb` | 0.2017 | `idle`, `walk`, `sit`, `work`, `talk` | 5/5 |

## 構造物

| ファイル | 容量(MB) | クリップ | mesh/node |
|---|---|---|---|
| `struct_altar.glb` | 0.0281 | `idle` | 2/2 |
| `struct_chest.glb` | 0.0134 | `open` | 2/2 |
| `struct_door.glb` | 0.0124 | —（静物） | 1/1 |
| `struct_door_double.glb` | 0.0204 | —（静物） | 1/1 |
| `struct_fence.glb` | 0.0072 | —（静物） | 1/1 |
| `struct_roof.glb` | 0.0036 | —（静物） | 1/1 |
| `struct_roof_hip.glb` | 0.0058 | —（静物） | 1/1 |
| `struct_spawner.glb` | 0.0336 | `idle` | 2/2 |
| `struct_torch.glb` | 0.0113 | `idle` | 2/2 |
| `struct_wall.glb` | 0.0079 | —（静物） | 1/1 |
| `struct_wall_stone.glb` | 0.0214 | —（静物） | 1/1 |
| `struct_wall_tall.glb` | 0.0097 | —（静物） | 1/1 |
| `struct_well.glb` | 0.0310 | —（静物） | 1/1 |
| `struct_window.glb` | 0.0080 | —（静物） | 1/1 |
| `struct_window_arch.glb` | 0.0137 | —（静物） | 1/1 |

## アイテム

| ファイル | 容量(MB) | クリップ | mesh/node |
|---|---|---|---|
| `item_apple.glb` | 0.0334 | —（静物） | 1/1 |
| `item_coal.glb` | 0.0230 | —（静物） | 1/1 |
| `item_coin.glb` | 0.0082 | —（静物） | 1/1 |
| `item_egg.glb` | 0.0273 | —（静物） | 1/1 |
| `item_gem.glb` | 0.0036 | —（静物） | 1/1 |
| `item_gold.glb` | 0.0074 | —（静物） | 1/1 |
| `item_iron.glb` | 0.0074 | —（静物） | 1/1 |
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
| `cave_boulder.glb` | 0.0707 | —（静物） | 1/1 |
| `cave_crystal.glb` | 0.0360 | —（静物） | 1/1 |
| `cave_crystal_purple.glb` | 0.0360 | —（静物） | 1/1 |
| `cave_entrance.glb` | 0.1756 | —（静物） | 1/1 |
| `cave_geode.glb` | 0.0748 | —（静物） | 1/1 |
| `cave_mushroom.glb` | 0.0760 | —（静物） | 1/1 |
| `cave_pillar.glb` | 0.0215 | —（静物） | 1/1 |
| `cave_stalactite.glb` | 0.0109 | —（静物） | 1/1 |
| `cave_stalagmite.glb` | 0.0109 | —（静物） | 1/1 |
| `ore_coal.glb` | 0.0375 | —（静物） | 1/1 |
| `ore_gem.glb` | 0.0266 | —（静物） | 1/1 |
| `ore_gold.glb` | 0.0356 | —（静物） | 1/1 |
| `ore_iron.glb` | 0.0332 | —（静物） | 1/1 |

## 王国城（ランドマーク）

| ファイル | 容量(MB) | クリップ | mesh/node |
|---|---|---|---|
| `castle_keep.glb` | 0.3656 | —（静物） | 1/1 |

## 砦・城塞

| ファイル | 容量(MB) | クリップ | mesh/node |
|---|---|---|---|
| `fort_battlement.glb` | 0.0184 | —（静物） | 1/1 |
| `fort_flag.glb` | 0.0059 | —（静物） | 1/1 |
| `fort_gate.glb` | 0.0549 | —（静物） | 1/1 |
| `fort_tower.glb` | 0.0461 | —（静物） | 1/1 |
| `fort_wall.glb` | 0.0235 | —（静物） | 1/1 |

## 船

| ファイル | 容量(MB) | クリップ | mesh/node |
|---|---|---|---|
| `ship_rowboat.glb` | 0.0436 | `idle` | 1/1 |
| `ship_sailboat.glb` | 0.0428 | `idle` | 1/1 |
| `ship_wreck.glb` | 0.0375 | —（静物） | 1/1 |

## 祠・聖域

| ファイル | 容量(MB) | クリップ | mesh/node |
|---|---|---|---|
| `shrine.glb` | 0.1651 | —（静物） | 1/1 |

## 演出（ボス出現FX）

| ファイル | 容量(MB) | クリップ | mesh/node |
|---|---|---|---|
| `fx_collapse.glb` | 0.0738 | `loop` | 3/3 |
| `fx_magic_circle.glb` | 0.3806 | `loop` | 3/3 |
| `fx_miasma.glb` | 0.3016 | `loop` | 3/3 |

## 町小物

| ファイル | 容量(MB) | クリップ | mesh/node |
|---|---|---|---|
| `prop_barrel.glb` | 0.0187 | —（静物） | 1/1 |
| `prop_bench.glb` | 0.0063 | —（静物） | 1/1 |
| `prop_brazier.glb` | 0.0210 | —（静物） | 1/1 |
| `prop_cart.glb` | 0.0218 | —（静物） | 1/1 |
| `prop_crate.glb` | 0.0170 | —（静物） | 1/1 |
| `prop_lamp.glb` | 0.0116 | —（静物） | 1/1 |
| `prop_laundry.glb` | 0.0101 | —（静物） | 1/1 |
| `prop_sign.glb` | 0.0063 | —（静物） | 1/1 |
| `prop_stall.glb` | 0.0188 | —（静物） | 1/1 |
