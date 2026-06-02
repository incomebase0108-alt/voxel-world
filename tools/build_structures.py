# -*- coding: utf-8 -*-
# VOXEL WORLD - 構造物用モデル群①：建物パーツ（村/構造物自動生成用）
# Blender 5.1 / headless: blender --background --python tools/build_structures.py
#   出力: models/struct_wall.glb / struct_roof.glb / struct_door.glb /
#         struct_window.glb / struct_well.glb / struct_fence.glb
#   規約: Y-up / 足元中心が原点(z=0) / 正面 -Z / 1ブロック≒1m / グリッド整合。
#   アニメ無し（静物）。軽量(<0.3MB目安)。1号機②の構造物自動生成(村)に直結。
# 設計指針: 1セル=1m に乗る寸法。壁=1x1x1、ドア=幅1x高2、窓=1x1、柵=幅1x高1、
#   井戸=2x2接地。原点は設置点（足元中心 z=0、x/y中心）に統一＝1号機がグリッドに置きやすい。

import bpy, os, math, mathutils
V = mathutils.Vector

def reset():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for blk in (bpy.data.meshes,bpy.data.materials,bpy.data.objects,bpy.data.actions):
        for it in list(blk):
            try: blk.remove(it)
            except Exception: pass
    parts.clear()

def mat(n,rgb,r=0.7,me=0.0,alpha=1.0):
    m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*rgb,alpha);b.inputs["Roughness"].default_value=r;b.inputs["Metallic"].default_value=me
    if alpha<1.0:
        b.inputs["Alpha"].default_value=alpha
        try: m.blend_method='BLEND'
        except Exception: pass
    return m

parts=[]
def cube(n,loc,s,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.rotation_euler=rot;o.data.materials.append(m);parts.append(o);return o
def cyl(n,loc,r,d,m,verts=16,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d,location=loc)
    o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);parts.append(o);return o
def sphere(n,loc,s,m,segs=14,rings=8):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs,ring_count=rings,location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.data.materials.append(m);parts.append(o);return o

repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."));models=os.path.join(repo,"models");os.makedirs(models,exist_ok=True)
scene=bpy.context.scene

def finish(name, subsurf=0, ratio=0.6, bevel=0.0, flat=False):
    """parts を結合→(bevel/subsurf/decimate)→足元中心(z=0,x/y中心)を原点→GLB書き出し"""
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
    if flat: bpy.ops.object.shade_flat()
    else: bpy.ops.object.shade_smooth()
    # 足元中心を原点に（x/y中心・最下点 z=0）
    bpy.context.view_layer.update()
    xs=[(o.matrix_world@V(c)).x for c in o.bound_box]
    ys=[(o.matrix_world@V(c)).y for c in o.bound_box]
    zs=[(o.matrix_world@V(c)).z for c in o.bound_box]
    scene.cursor.location=((min(xs)+max(xs))/2,(min(ys)+max(ys))/2,min(zs))
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR'); o.location=(0,0,0)
    out=os.path.join(models,name+".glb")
    bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_animations=False)
    sz=os.path.getsize(out)
    print("[voxel] %s -> %.3f MB  dims=%.2fx%.2fx%.2f"%(name, sz/1048576, max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs)))

# ---- 共通マテリアル ----
def planks(): return mat("Planks",(0.66,0.45,0.26),0.65)
def darkwood(): return mat("DarkWood",(0.40,0.26,0.14),0.6)
def stone(): return mat("Stone",(0.55,0.55,0.57),0.85)
def stone2(): return mat("Stone2",(0.44,0.44,0.47),0.85)

# ============ struct_wall（1x1x1 木の壁ブロック・板張り＋梁）============
reset()
PL=planks(); DW=darkwood()
cube("Panel",(0,0,0.5),(0.5,0.45,0.5),PL)                 # 本体 1x0.9x1
# 板の継ぎ目（縦の梁）と隅柱で板張り感
for x in (-0.5,-0.17,0.17,0.5):
    cube("BeamV",(x,-0.46,0.5),(0.03,0.02,0.5),DW)
cube("BeamTop",(0,-0.46,0.97),(0.5,0.02,0.04),DW)          # 上端梁
cube("BeamBot",(0,-0.46,0.03),(0.5,0.02,0.04),DW)          # 下端梁（土台）
finish("struct_wall", bevel=0.01)

# ============ struct_roof（1m幅・切妻スロープ片）============
# 三角柱を倒した形＝勾配屋根。設置時に並べて屋根面に。茅葺き/瓦色。
reset()
ROOF=mat("Roof",(0.62,0.25,0.18),0.7); RIDGE=mat("Ridge",(0.45,0.18,0.13),0.7)
# 楔形（断面が三角）：cubeを回して片流れに。幅x=1、奥行y=1、棟高0.5
wedge=cube("Wedge",(0,0,0.5),(0.5,0.5,0.5),ROOF)
# 片流れにするため上面を斜めに：頂点を編集する代わり簡易に三角柱を作る
bpy.ops.object.select_all(action='DESELECT'); wedge.select_set(True); bpy.context.view_layer.objects.active=wedge
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.object.mode_set(mode='OBJECT')
# 上の+Z+Y稜2頂点を-Z側へ落として勾配に（メッシュ頂点直接操作）
me=wedge.data
for vtx in me.vertices:
    if vtx.co.z>0 and vtx.co.y>0:   # 上面の後ろ側を下げる→前下がりスロープ
        vtx.co.z=-1.0
cube("RidgeBar",(0,-0.5,1.0),(0.5,0.04,0.04),RIDGE)        # 軒先の縁
finish("struct_roof", bevel=0.008)

# ============ struct_door（幅1 x 高2・板戸＋取手）============
reset()
PL=planks(); DW=darkwood(); IRON=mat("Iron",(0.20,0.20,0.22),0.4,me=0.8)
cube("Slab",(0,0,1.0),(0.45,0.08,1.0),PL)                 # 戸板 0.9x0.16x2
for x in (-0.30,0,0.30):
    cube("Plank",(x,-0.085,1.0),(0.02,0.01,1.0),DW)        # 板継ぎ目
cube("BandT",(0,-0.085,1.6),(0.45,0.012,0.05),DW)         # 横帯（上）
cube("BandB",(0,-0.085,0.4),(0.45,0.012,0.05),DW)         # 横帯（下）
sphere("Knob",(0.33,-0.13,1.0),(0.05,0.05,0.05),IRON,segs=12,rings=8)  # 取手
cube("Hinge1",(-0.42,-0.09,1.55),(0.05,0.015,0.06),IRON)
cube("Hinge2",(-0.42,-0.09,0.45),(0.05,0.015,0.06),IRON)
finish("struct_door", bevel=0.006)

# ============ struct_window（1x1・木枠＋ガラス＋十字桟）============
reset()
DW=darkwood(); GLASS=mat("Glass",(0.62,0.78,0.86),0.1,alpha=0.35)
# 外枠（4辺）
cube("FrTop",(0,0,0.92),(0.5,0.08,0.08),DW)
cube("FrBot",(0,0,0.08),(0.5,0.08,0.08),DW)
cube("FrL",(-0.46,0,0.5),(0.04,0.08,0.5),DW)
cube("FrR",(0.46,0,0.5),(0.04,0.08,0.5),DW)
# 十字桟
cube("MullV",(0,0,0.5),(0.025,0.05,0.46),DW)
cube("MullH",(0,0,0.5),(0.46,0.05,0.025),DW)
# ガラス（薄板・半透明）
cube("Pane",(0,0.0,0.5),(0.44,0.012,0.44),GLASS)
finish("struct_window", bevel=0.004)

# ============ struct_fence（幅1・柵：2柱＋2横木）============
reset()
DW=darkwood(); PL=planks()
for x in (-0.45,0.45):
    cube("Post",(x,0,0.5),(0.07,0.07,0.5),DW)              # 柱
cube("RailT",(0,0,0.78),(0.45,0.045,0.05),PL)             # 上横木
cube("RailB",(0,0,0.40),(0.45,0.045,0.05),PL)             # 下横木
for x in (-0.45,0.45):
    cube("Cap",(x,0,1.02),(0.085,0.085,0.04),DW)           # 柱の笠木
finish("struct_fence", bevel=0.006)

# ============ struct_well（2x2接地・石組み＋屋根＋桶）============
reset()
ST=stone(); ST2=stone2(); DW=darkwood(); ROOF=mat("WRoof",(0.55,0.22,0.16),0.7)
WOOD=planks(); ROPE=mat("Rope",(0.72,0.62,0.40),0.8); WATER=mat("Water",(0.18,0.35,0.55),0.2,alpha=0.6)
# 石組みのリング（8分割で円筒風）。外径~0.95、高さ0.6
import math as _m
for i in range(8):
    a=_m.radians(i*45); x=_m.cos(a)*0.82; y=_m.sin(a)*0.82
    cube("Stone",(x,y,0.30),(0.22,0.22,0.30),ST if i%2 else ST2,rot=(0,0,a))
# 内側の水面
cyl("Water",(0,0,0.50),0.55,0.04,WATER,verts=20)
# 2本の支柱
for x in (-0.7,0.7):
    cube("Post",(x,0,1.15),(0.06,0.06,0.55),DW)
# 横棟木＋滑車軸
cube("Beam",(0,0,1.68),(0.06,0.06,0.78),DW,rot=(0,0,_m.radians(90)))
cyl("Axle",(0,0,1.55),0.03,1.0,ROPE,verts=10,rot=(_m.radians(90),0,_m.radians(90)))
# 小屋根（切妻・2スロープ）
r1=cube("RoofA",(0,0.0,2.0),(0.62,0.7,0.05),ROOF,rot=(_m.radians(28),0,0))
r2=cube("RoofB",(0,0.0,2.0),(0.62,0.7,0.05),ROOF,rot=(_m.radians(-28),0,0))
# 桶（縄で吊る）
cube("Rope",(0.0,0,1.35),(0.012,0.012,0.22),ROPE)
cyl("Bucket",(0,0,1.05),0.13,0.18,WOOD,verts=14)
cyl("BucketBand",(0,0,1.12),0.135,0.03,DW,verts=14)
finish("struct_well", subsurf=0, ratio=0.7, bevel=0.006)

print("[voxel] all building-part structures done")
