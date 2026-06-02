# -*- coding: utf-8 -*-
# VOXEL WORLD - 装飾ブロック案のスウォッチ生成（1号機エンジンのブロックパレット拡張提案）
# Blender 5.1 / headless: blender --background --python tools/gen_block_swatches.py
#   出力: tools/block_swatches.png（提案ブロックを格子状に並べた一覧）
#         models/BLOCKS_PROPOSAL.md（各ブロックの具体マテリアル値・1号機が流用）
#   ブロックはエンジン側voxel（glb非依存）なので、ここでは「色/質感の提案」だけ。新規glb量産はしない。

import bpy, os, math, mathutils, json
V=mathutils.Vector
repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))

bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)

# 提案ブロック: name, rgb, roughness, metallic, alpha, emissive(or None), 説明
PROP=[
 ("brick",        (0.62,0.24,0.18),0.80,0.0,1.0,None,        "赤レンガ。建物の壁/暖炉に"),
 ("cobblestone",  (0.50,0.50,0.52),0.95,0.0,1.0,None,        "丸石。基礎/ダンジョン床"),
 ("mossy_cobble", (0.40,0.50,0.40),0.92,0.0,1.0,None,        "苔石。古びた遺跡/洞窟"),
 ("dark_wood",    (0.30,0.20,0.12),0.70,0.0,1.0,None,        "濃色材。梁/高級建材"),
 ("iron_block",   (0.80,0.80,0.83),0.35,0.9,1.0,None,        "鉄ブロック。金属建材/装飾"),
 ("gold_block",   (0.92,0.76,0.26),0.30,0.95,1.0,None,       "金ブロック。宝物庫/装飾"),
 ("bookshelf",    (0.55,0.40,0.24),0.70,0.0,1.0,None,        "本棚。室内装飾（背表紙は別テクスチャ推奨）"),
 ("hay",          (0.80,0.66,0.22),0.85,0.0,1.0,None,        "干し草。農村/納屋"),
 ("snow",         (0.95,0.96,0.98),0.60,0.0,1.0,None,        "雪。雪原バイオーム"),
 ("obsidian",     (0.10,0.08,0.14),0.30,0.2,1.0,None,        "黒曜石。硬質/ポータル枠"),
 ("crystal",      (0.55,0.80,0.95),0.12,0.0,0.55,(0.4,0.7,1.0),"水晶。半透明＋淡い発光。洞窟の鉱脈"),
 ("lantern",      (1.00,0.82,0.40),0.30,0.0,1.0,(1.0,0.78,0.35),"ランタン。発光・夜間照明"),
 ("lava",         (1.00,0.45,0.10),0.50,0.0,1.0,(1.0,0.42,0.08),"溶岩。発光・ダメージ源"),
 ("amethyst",     (0.62,0.42,0.85),0.25,0.0,0.85,(0.45,0.3,0.7),"紫水晶。装飾/淡い発光"),
]

def mat(n,rgb,r,me,alpha,emis):
    m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*rgb,alpha);b.inputs["Roughness"].default_value=r;b.inputs["Metallic"].default_value=me
    if alpha<1.0:
        b.inputs["Alpha"].default_value=alpha
        try: m.blend_method='BLEND'
        except Exception: pass
    if emis is not None:
        b.inputs["Emission Color"].default_value=(*emis,1.0); b.inputs["Emission Strength"].default_value=2.5
    return m

# 格子配置（cols列）
cols=5; gap=1.5
for i,(name,rgb,r,me,al,emis,note) in enumerate(PROP):
    cx=(i%cols)*gap; cy=-(i//cols)*gap
    bpy.ops.mesh.primitive_cube_add(location=(cx,cy,0)); o=bpy.context.active_object
    o.scale=(0.5,0.5,0.5); o.name=name; o.data.materials.append(mat(name,rgb,r,me,al,emis))
    bv=o.modifiers.new("B",'BEVEL'); bv.width=0.02; bv.segments=1; bpy.ops.object.modifier_apply(modifier=bv.name)
    bpy.ops.object.shade_smooth()

# ライト/カメラ/レンダ
bpy.ops.object.light_add(type='SUN', location=(4,-6,10)); bpy.context.active_object.data.energy=4.0
bpy.ops.object.light_add(type='SUN', location=(-5,5,5)); bpy.context.active_object.data.energy=1.8
scene=bpy.context.scene
try: scene.render.engine='BLENDER_EEVEE_NEXT'
except Exception: scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=1100; scene.render.resolution_y=520
scene.world=scene.world or bpy.data.worlds.new("W"); scene.world.use_nodes=True
scene.world.node_tree.nodes["Background"].inputs[0].default_value=(0.20,0.22,0.26,1)
rows=(len(PROP)+cols-1)//cols
cx=(cols-1)*gap/2; cy=-(rows-1)*gap/2
bpy.ops.object.camera_add(location=(cx, cy-7.5, 6.0)); cam=bpy.context.active_object
d=bpy.data.objects.new("E",None); scene.collection.objects.link(d); d.location=(cx,cy,0)
c=cam.constraints.new('TRACK_TO'); c.target=d
scene.camera=cam; scene.render.filepath=os.path.join(repo,"tools","block_swatches.png")
bpy.ops.render.render(write_still=True)
print("[voxel] swatches ->", scene.render.filepath)

# 提案md
lines=["# VOXEL WORLD 装飾ブロック案（1号機エンジンのブロックパレット拡張提案）\n",
 "ブロックはエンジン側voxel（glb非依存）。下記は**色/質感の提案値**で、1号機がブロック定義にそのまま流用可。",
 "スウォッチ画像 → `tools/block_swatches.png`（左上から順に下表と一致）。再生成 `tools/gen_block_swatches.py`。\n",
 "値は Three.js MeshStandardMaterial 想定（color=RGB, roughness, metalness, opacity/transparent, emissive）。\n",
 "| # | name | RGB(0-1) | rough | metal | alpha | emissive | 用途 |",
 "|---|---|---|---|---|---|---|---|"]
for i,(name,rgb,r,me,al,emis,note) in enumerate(PROP):
    e="—" if emis is None else "(%.2f,%.2f,%.2f)"%emis
    lines.append("| %d | `%s` | (%.2f,%.2f,%.2f) | %.2f | %.2f | %.2f | %s | %s |"%(i+1,name,rgb[0],rgb[1],rgb[2],r,me,al,e,note))
lines+=["\n## メモ",
 "- *新規glb量産はしていない*（ブロックはエンジン描画）。採用するものだけ1号機が定義に追加すればOK。",
 "- 発光系（lantern/lava/crystal/amethyst）は emissive 指定。夜間ライティングや危険源の視認に。",
 "- 半透明系（crystal/amethyst）は既存 glass と同様 `transparent:true` ＋ 固体衝突を推奨。",
 "- bookshelf/brick 等は単色近似。テクスチャ（タイル絵）が要るなら4号機で 16×16/32×32 のタイル画像も作れます。",
 "- 既存9種（grass/dirt/stone/sand/wood/leaves/planks/stonebrick/glass）はアイコンを `tools/icons/` に用意済み。"]
open(os.path.join(repo,"models","BLOCKS_PROPOSAL.md"),"w",encoding="utf-8").write("\n".join(lines)+"\n")
print("[voxel] -> models/BLOCKS_PROPOSAL.md")
