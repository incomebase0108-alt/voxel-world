# -*- coding: utf-8 -*-
# VOXEL WORLD - モブ第三弾：スライム（敵性） 生成スクリプト
# Blender 5.1 / headless: blender --background --python tools/build_mob_slime.py
#   出力: models/mob_slime.glb （Y-up / 足元原点 / 正面 -Z / 高さ約0.6m / 1ブロック≒1m）
#   アニメ: idle / walk / attack（クリップ名を全モデルで統一）
# 方針: 丸い半透明風グリーンの塊＋目。squash&stretch で生命感。subsurf1+decimateで軽量(<1MB)。
#   単一メッシュ（body+目を結合）。原点=底面中心。scale/location をキーフレームしてアニメ。
#   前方(攻撃方向)= Blender +Y（= glTF -Z）。

import bpy, os, math, mathutils

bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for blk in (bpy.data.meshes, bpy.data.materials, bpy.data.objects, bpy.data.actions):
    for it in list(blk):
        try: blk.remove(it)
        except Exception: pass
scene=bpy.context.scene; scene.render.fps=24

def mat(n,rgb,r=0.35,me=0.0):
    m=bpy.data.materials.new(n); m.use_nodes=True; b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*rgb,1.0); b.inputs["Roughness"].default_value=r; b.inputs["Metallic"].default_value=me; return m
M_SLIME=mat("Slime",(0.30,0.75,0.35),0.3); M_EYE=mat("Eye",(0.04,0.05,0.05)); M_MOUTH=mat("Mouth",(0.10,0.20,0.12))

parts=[]
def sphere(n,loc,s,m,segs=16,rings=10):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs,ring_count=rings,location=loc)
    o=bpy.context.active_object; o.name=n; o.scale=s; o.data.materials.append(m); parts.append(o); return o
def cube(n,loc,s,m):
    bpy.ops.mesh.primitive_cube_add(location=loc); o=bpy.context.active_object
    o.name=n; o.scale=s; o.data.materials.append(m); parts.append(o); return o

# 本体（角丸キューブ＝スライムらしい塊）。中心 z=0.30、底0・上0.60。
cube("Body",(0,0,0.30),(0.32,0.32,0.30),M_SLIME)
# 目（前=+Y、上方）
sphere("EyeL",(0.11,0.27,0.40),(0.05,0.04,0.06),M_EYE,segs=12,rings=8)
sphere("EyeR",(-0.11,0.27,0.40),(0.05,0.04,0.06),M_EYE,segs=12,rings=8)
# ハイライト（小さな白）
sphere("HiL",(0.13,0.30,0.43),(0.018,0.015,0.02),mat("Hi",(0.9,0.95,0.9),0.2),segs=8,rings=6)
sphere("HiR",(-0.09,0.30,0.43),(0.018,0.015,0.02),mat("Hi2",(0.9,0.95,0.9),0.2),segs=8,rings=6)
# 口（前面の細い窪み）
cube("Mouth",(0,0.31,0.22),(0.10,0.02,0.02),M_MOUTH)

# ジオメトリ確定（subsurf2で角丸→decimate。本体だけ角丸が要るのでsubsurf2、目は1）
for o in parts:
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
    s=o.modifiers.new("S",'SUBSURF'); lvl=2 if o.name=="Body" else 1; s.levels=lvl; s.render_levels=lvl
    bpy.ops.object.shade_smooth(); bpy.ops.object.modifier_apply(modifier=s.name)
    d=o.modifiers.new("D",'DECIMATE'); d.decimate_type='COLLAPSE'
    d.ratio = 0.8 if o.name=="Body" else 0.5   # 本体は丸み維持で緩め
    bpy.ops.object.modifier_apply(modifier=d.name); bpy.ops.object.shade_smooth()

# 結合 → 原点を底面中心(0,0,0)へ（squashが下に潰れるように）
bpy.ops.object.select_all(action='DESELECT')
for o in parts: o.select_set(True)
bpy.context.view_layer.objects.active=parts[0]; bpy.ops.object.join()
slime=bpy.context.active_object; slime.name="Slime"
bpy.ops.object.select_all(action='DESELECT')
slime.select_set(True); bpy.context.view_layer.objects.active=slime
# モデリング時のスケールをメッシュへ焼き込む（以後 scale アニメは 1.0 基準で正しく効く）
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
# 底面（最下点）を z=0 に合わせる（subsurf丸めで浮く分を補正）
bpy.context.view_layer.update()
minz = min((slime.matrix_world @ mathutils.Vector(c)).z for c in slime.bound_box)
slime.location.z -= minz
bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
scene.cursor.location=(0,0,0)
bpy.ops.object.origin_set(type='ORIGIN_CURSOR'); slime.location=(0,0,0)

# アニメ（idle/walk/attack）。scale と location をキーフレーム。
def new_action(n):
    if slime.animation_data is None: slime.animation_data_create()
    a=bpy.data.actions.new(n); a.use_fake_user=True; slime.animation_data.action=a; return a
def push(t):
    ad=slime.animation_data; act=ad.action; tr=ad.nla_tracks.new(); tr.name=t
    tr.strips.new(act.name,int(act.frame_range[0]),act); ad.action=None
def key(f, sx,sy,sz, lz=0.0, ly=0.0):
    slime.scale=(sx,sy,sz); slime.location=(0,ly,lz)
    slime.keyframe_insert('scale',frame=f); slime.keyframe_insert('location',frame=f)

# idle（48f）: ゆるい呼吸 squash&stretch
new_action("idle")
key(1, 1,1,1); key(24, 1.05,1.05,0.92); key(48, 1,1,1)
push("idle")
# walk（24f）: その場ホップ（しゃがみ→跳躍→着地squash）
new_action("walk")
key(1, 1.10,1.10,0.85, 0.0)      # しゃがみ
key(6, 0.92,0.92,1.18, 0.16)     # 跳び上がり・伸び
key(12,1.0,1.0,1.0, 0.22)        # 頂点
key(18,1.15,1.15,0.80, 0.0)      # 着地squash
key(24,1.10,1.10,0.85, 0.0)      # ループ接続
push("walk")
# attack（20f）: 溜め→前方(+Y)へランジ＆ストレッチ→戻り
new_action("attack")
key(1, 1,1,1, 0.0, 0.0)
key(5, 1.18,1.18,0.78, 0.0, -0.04)   # 溜め（しゃがみ＆わずかに後退）
key(10,0.85,0.92,1.18, 0.10, 0.26)   # 前方ランジ＋縦伸び
key(15,1.05,1.05,0.95, 0.0, 0.04)    # 戻り
key(20,1,1,1, 0.0, 0.0)
push("attack")

repo=os.path.abspath(os.path.join(os.path.dirname(__file__),"..")); models=os.path.join(repo,"models"); os.makedirs(models,exist_ok=True)
out=os.path.join(models,"mob_slime.glb")
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_yup=True,
    export_apply=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_optimize_animation_size=True)
zs=[];ys=[];xs=[]
for v in slime.bound_box:
    w=slime.matrix_world@mathutils.Vector(v); xs.append(w.x);ys.append(w.y);zs.append(w.z)
print("[voxel] export OK ->",out)
print("[voxel] bbox X:%.2f..%.2f Y:%.2f..%.2f Z:%.2f..%.2f"%(min(xs),max(xs),min(ys),max(ys),min(zs),max(zs)))
print("[voxel] clips: idle / walk / attack")
