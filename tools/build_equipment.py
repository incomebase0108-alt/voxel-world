# -*- coding: utf-8 -*-
# VOXEL WORLD - 装備・道具モデル（item_*.glb）
# Blender 5.1 / headless: blender --background --python tools/build_equipment.py
#   出力: models/item_sword.glb / item_pickaxe.glb / item_axe.glb /
#         item_bow.glb / item_shield.glb / item_armor.glb
#   規約: Y-up / 正面 Blender+Y(=glTF -Z) / 1ブロック≒1m。アニメ無し・軽量。
#   手持ち＋地面ドロップ両対応。原点(=ノード基準点)は装備ごとの「握り/中心」に統一:
#     sword/pickaxe/axe : 柄の最下端（握り基部）。刃/頭は +Z 方向へ伸びる。
#     bow               : 握り中央（弓の中点）。
#     shield/armor      : 形状中心（背面の握り＝中心）。
#   → 1号機は origin を手ボーンに付ければ自然に持てる。ドロップ時は origin 周りで回転表示でOK。

import bpy, os, math, mathutils
V=mathutils.Vector

def reset():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for blk in (bpy.data.meshes,bpy.data.materials,bpy.data.objects,bpy.data.actions):
        for it in list(blk):
            try: blk.remove(it)
            except Exception: pass
    parts.clear()

def mat(n,rgb,r=0.6,me=0.0,alpha=1.0):
    m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*rgb,alpha);b.inputs["Roughness"].default_value=r;b.inputs["Metallic"].default_value=me
    return m

parts=[]
def cube(n,loc,s,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.rotation_euler=rot;o.data.materials.append(m);parts.append(o);return o
def cyl(n,loc,r,d,m,verts=14,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d,location=loc)
    o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);parts.append(o);return o
def sphere(n,loc,s,m,segs=14,rings=8):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs,ring_count=rings,location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.data.materials.append(m);parts.append(o);return o
def cone(n,loc,r,d,m,verts=14,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r,radius2=0.0,depth=d,location=loc)
    o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);parts.append(o);return o

repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."));models=os.path.join(repo,"models");os.makedirs(models,exist_ok=True)
scene=bpy.context.scene

def finish(name, grip, subsurf=0, ratio=0.7, bevel=0.0):
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts: o.select_set(True)
    bpy.context.view_layer.objects.active=parts[0]; bpy.ops.object.join()
    o=bpy.context.active_object; o.name=name
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel>0:
        bv=o.modifiers.new("B",'BEVEL'); bv.width=bevel; bv.segments=1
        bpy.ops.object.modifier_apply(modifier=bv.name)
    if subsurf:
        s=o.modifiers.new("S",'SUBSURF');s.levels=subsurf;s.render_levels=subsurf
        bpy.ops.object.shade_smooth();bpy.ops.object.modifier_apply(modifier=s.name)
    if ratio<1.0:
        d=o.modifiers.new("D",'DECIMATE');d.decimate_type='COLLAPSE';d.ratio=ratio
        bpy.ops.object.modifier_apply(modifier=d.name)
    bpy.ops.object.shade_smooth()
    scene.cursor.location=grip
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR'); o.location=(0,0,0)
    bpy.context.view_layer.update()
    xs=[(o.matrix_world@V(c)).x for c in o.bound_box]; ys=[(o.matrix_world@V(c)).y for c in o.bound_box]; zs=[(o.matrix_world@V(c)).z for c in o.bound_box]
    out=os.path.join(models,name+".glb")
    bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_animations=False)
    sz=os.path.getsize(out)
    print("[voxel] %-14s -> %.3f MB  size=%.2fx%.2fx%.2f"%(name, sz/1048576, max(xs)-min(xs),max(ys)-min(ys),max(zs)-min(zs)))

# 共通マテリアル
def steel(): return mat("Steel",(0.78,0.80,0.84),0.3,me=0.9)
def steel2(): return mat("Steel2",(0.62,0.64,0.68),0.35,me=0.9)
def wood(): return mat("Wood",(0.52,0.36,0.20),0.7)
def leather(): return mat("Leather",(0.34,0.22,0.13),0.8)
def iron(): return mat("Iron",(0.28,0.28,0.30),0.45,me=0.8)
def gold(): return mat("GoldT",(0.88,0.70,0.24),0.3,me=0.85)

# ============ item_sword（握り基部=原点・刃が+Z）============
reset()
ST=steel(); ST2=steel2(); LE=leather(); GD=gold()
cyl("Grip",(0,0,0.10),0.022,0.20,LE,verts=12)               # 握り z0..0.20
sphere("Pommel",(0,0,0.0),(0.035,0.035,0.035),GD,segs=12,rings=8)  # 柄頭
cube("Guard",(0,0,0.215),(0.13,0.035,0.025),GD)              # 鍔
cube("Blade",(0,0,0.57),(0.045,0.012,0.34),ST)              # 刀身 0.23..0.91
cube("Fuller",(0,0,0.57),(0.012,0.014,0.33),ST2)            # 樋（中央溝）
cone("Tip",(0,0,0.93),0.045,0.10,ST,verts=8)                # 切先
finish("item_sword", grip=(0,0,0.0), bevel=0.004)

# ============ item_pickaxe（柄基部=原点・頭が+Z上端で横向き）============
reset()
WD=wood(); IR=iron(); ST2=steel2()
cyl("Handle",(0,0,0.34),0.026,0.68,WD,verts=12)             # 柄 z0..0.68
# 頭（横長・両端が尖る曲がりつるはし）
cube("HeadMid",(0,0,0.70),(0.07,0.05,0.05),IR)
cube("HeadL",(0.22,0,0.685),(0.18,0.04,0.04),IR,rot=(0,math.radians(12),0))
cube("HeadR",(-0.22,0,0.685),(0.18,0.04,0.04),IR,rot=(0,math.radians(-12),0))
cone("PtL",(0.40,0,0.665),0.04,0.10,ST2,verts=8,rot=(0,math.radians(102),0))
cone("PtR",(-0.40,0,0.665),0.04,0.10,ST2,verts=8,rot=(0,math.radians(-102),0))
finish("item_pickaxe", grip=(0,0,0.0), bevel=0.004)

# ============ item_axe（柄基部=原点・斧頭が片側）============
reset()
WD=wood(); IR=iron(); ST=steel()
cyl("Handle",(0,0,0.34),0.026,0.68,WD,verts=12)             # 柄 z0..0.68
cube("HeadBack",(0,0,0.66),(0.05,0.05,0.10),IR)             # 頭の基部
cube("Blade",(0.17,0,0.66),(0.14,0.045,0.13),IR)            # 斧身
cube("Edge",(0.27,0,0.66),(0.02,0.05,0.15),ST)             # 刃先（やや広い）
finish("item_axe", grip=(0,0,0.0), bevel=0.004)

# ============ item_bow（握り中央=原点・縦の弓・木が+Yへ湾曲＝D字・弦は-Y側の直線）============
reset()
WD=wood(); WD2=mat("BowWood2",(0.42,0.28,0.15),0.7); ST2=steel2(); STR=mat("String",(0.92,0.90,0.82),0.6)
# 握り（中央・革巻き）
cyl("GripB",(0,0.02,0),0.026,0.18,leather(),verts=12)
# リム：上下それぞれ inner(外へ膨らむ)→outer(弦側へ戻る)→tip の3節でD字の弧
for sgn in (1,-1):
    cube("LimbIn",(0,0.10,sgn*0.17),(0.018,0.05,0.16),WD,rot=(math.radians(sgn*22),0,0))
    cube("LimbOut",(0,0.09,sgn*0.40),(0.016,0.045,0.14),WD2,rot=(math.radians(sgn*55),0,0))
    cone("Tip",(0,0.015,sgn*0.50),0.022,0.06,ST2,verts=8,rot=(math.radians(sgn*90+ (0 if sgn>0 else 180)),0,0))
# 弦（-Y側＝射手側の直線・上端tip〜下端tip）
cyl("Strg",(0,-0.005,0),0.006,1.00,STR,verts=6)
finish("item_bow", grip=(0,0,0.0), bevel=0.0, ratio=0.85)

# ============ item_shield（中心=原点・正面+Y・木板＋鉄縁＋ボス）============
reset()
WD=wood(); WD2=mat("Wood2",(0.44,0.30,0.16),0.7); IR=iron(); ST=steel()
cube("Board",(0,0,0),(0.28,0.04,0.38),WD)                   # 盾板 0.56x0.76
for x in (-0.14,0,0.14):
    cube("PlankLine",(x,0.045,0),(0.012,0.005,0.38),WD2)     # 板目（正面+Y）
# 鉄の縁
cube("RimT",(0,0.02,0.37),(0.28,0.05,0.03),IR)
cube("RimB",(0,0.02,-0.37),(0.28,0.05,0.03),IR)
cube("RimL",(-0.27,0.02,0),(0.03,0.05,0.38),IR)
cube("RimR",(0.27,0.02,0),(0.03,0.05,0.38),IR)
sphere("Boss",(0,0.07,0),(0.10,0.05,0.10),ST,segs=14,rings=8)  # 中央の鉄ボス（正面+Y）
finish("item_shield", grip=(0,0,0), bevel=0.006)

# ============ item_armor（中心=原点・胸当て・正面+Y）============
reset()
ST=steel(); ST2=steel2(); GD=gold()
cube("Chest",(0,0,0.04),(0.26,0.16,0.26),ST)                # 胴
cube("Collar",(0,0,0.30),(0.20,0.15,0.05),ST2)              # 襟
for sgn in (1,-1):
    cube("Shoulder",(sgn*0.30,0,0.22),(0.10,0.14,0.10),ST2) # 肩当て
cube("Belt",(0,0,-0.22),(0.27,0.16,0.05),ST2)               # 腰帯
cube("Crest",(0,0.15,0.06),(0.05,0.02,0.12),GD)             # 胸の紋章（正面+Y）
finish("item_armor", grip=(0,0,0), subsurf=1, ratio=0.5, bevel=0.0)

print("[voxel] all equipment done")
