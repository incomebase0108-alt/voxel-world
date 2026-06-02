# -*- coding: utf-8 -*-
# VOXEL WORLD - 砦/城塞パーツ（1号機の構造物生成・攻略拠点用）
# Blender 5.1 / headless: blender --background --python tools/build_fort.py
#   出力: models/fort_wall.glb / fort_battlement.glb / fort_tower.glb /
#         fort_gate.glb / fort_flag.glb
#   規約: Y-up / 足元中心z=0 / 正面 -Z(glTF) / 1ブロック≒1m / グリッド整合 / 軽量・アニメ無し。
#   城壁=1x1x1の石ランパート(積み重ね), 狭間=クレネル(城壁天端のキャップ),
#   塔=2x2の角櫓, 門=2幅x3高の門楼(扉+落とし格子), 旗=塔/壁に立てる幟。
#   配置見本は LAYOUT.md「砦」章を参照（build_layout_demo.py で再現/レンダ）。

import bpy, os, math, mathutils
V=mathutils.Vector

def reset():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for blk in (bpy.data.meshes,bpy.data.materials,bpy.data.objects,bpy.data.actions):
        for it in list(blk):
            try: blk.remove(it)
            except Exception: pass
    parts.clear()

def mat(n,rgb,r=0.9,me=0.0):
    m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*rgb,1.0);b.inputs["Roughness"].default_value=r;b.inputs["Metallic"].default_value=me;return m

parts=[]
def cube(n,loc,s,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.rotation_euler=rot;o.data.materials.append(m);parts.append(o);return o
def cyl(n,loc,r,d,m,verts=12,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d,location=loc)
    o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);parts.append(o);return o

repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."));models=os.path.join(repo,"models");os.makedirs(models,exist_ok=True)
scene=bpy.context.scene

def finish(name, ratio=0.7, bevel=0.012, flat=True):
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts: o.select_set(True)
    bpy.context.view_layer.objects.active=parts[0]; bpy.ops.object.join()
    o=bpy.context.active_object; o.name=name
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel>0:
        bv=o.modifiers.new("B",'BEVEL'); bv.width=bevel; bv.segments=1
        bpy.ops.object.modifier_apply(modifier=bv.name)
    if ratio<1.0:
        d=o.modifiers.new("D",'DECIMATE');d.decimate_type='COLLAPSE';d.ratio=ratio
        bpy.ops.object.modifier_apply(modifier=d.name)
    if flat: bpy.ops.object.shade_flat()
    else: bpy.ops.object.shade_smooth()
    bpy.context.view_layer.update()
    xs=[(o.matrix_world@V(c)).x for c in o.bound_box]; ys=[(o.matrix_world@V(c)).y for c in o.bound_box]; zs=[(o.matrix_world@V(c)).z for c in o.bound_box]
    scene.cursor.location=((min(xs)+max(xs))/2,(min(ys)+max(ys))/2,min(zs))
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR'); o.location=(0,0,0)
    out=os.path.join(models,name+".glb")
    bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_animations=False)
    sz=os.path.getsize(out)
    print("[voxel] %-16s -> %.3f MB  dims=%.2fx%.2fx%.2f"%(name, sz/1048576, max(xs)-min(xs),max(ys)-min(ys),max(zs)-min(zs)))

def STONE(): return mat("Stone",(0.52,0.51,0.50),0.92)
def STONE2(): return mat("Stone2",(0.43,0.42,0.42),0.92)
def MORTAR(): return mat("Mortar",(0.34,0.33,0.32),0.9)

# ============ fort_wall（1x1x1 石ランパート・積み重ね用・全方位石）============
reset()
S=STONE(); S2=STONE2(); MO=MORTAR()
cube("Core",(0,0,0.5),(0.5,0.5,0.5),S)
# 石積みの目地（横2段・縦ずらし）＋数個の出っ張り石
for z in (0.33,0.66):
    cube("Mort",(0,0,z),(0.5,0.505,0.012),MO)
for (x,zz) in [(-0.5,0.5),(0.5,0.5),(0,0.5)]:
    cube("MortV",(x*0.5,0,zz),(0.012,0.505,0.5),MO)
cube("Stone_a",(0.26,-0.5,0.30),(0.16,0.02,0.13),S2)
cube("Stone_b",(-0.22,-0.5,0.72),(0.18,0.02,0.12),S2)
cube("Stone_c",(0.20,0.5,0.66),(0.15,0.02,0.12),S2)
finish("fort_wall", ratio=0.7, bevel=0.01)

# ============ fort_battlement（狭間＝クレネル・城壁天端キャップ・1幅・前面-Z外向き）============
reset()
S=STONE(); S2=STONE2()
cube("Walk",(0,0.0,0.07),(0.5,0.42,0.07),S2)              # 歩廊の床リップ
# 前縁(+Y=glTF-Z外向き)にメルロン3つ＋クレネル(隙間)2つ。高さ~0.45
for x in (-0.34,0.0,0.34):
    cube("Merlon",(x,0.36,0.30),(0.13,0.07,0.22),S)        # 立ち歯
cube("Parapet",(0,0.36,0.13),(0.5,0.07,0.07),S2)          # 前縁の腰壁
# 中央メルロンに矢狭間（細いスリット＝窪み）
cube("Slit",(0.0,0.40,0.34),(0.02,0.05,0.10),MORTAR())
finish("fort_battlement", ratio=0.8, bevel=0.008)

# ============ fort_tower（2x2の角櫓・約3.6m・天端クレネル・矢狭間）============
reset()
S=STONE(); S2=STONE2(); MO=MORTAR()
cube("Body",(0,0,1.55),(0.9,0.9,1.55),S)                  # 本体 1.8x1.8x3.1
# 石積み目地（数段）
for z in (0.7,1.4,2.1,2.8):
    cube("Mort",(0,0,z),(0.9,0.905,0.012),MO)
# 矢狭間（各面に縦スリット）
for (ax,ay,rotz) in [(0,0.9,0),(0,-0.9,0),(0.9,0,math.radians(90)),(-0.9,0,math.radians(90))]:
    cube("Slit",(ax*0.99,ay*0.99,1.7),(0.04,0.04,0.30),MO,rot=(0,0,rotz))
# 天端の張り出し＋クレネル
cube("Corbel",(0,0,3.16),(0.98,0.98,0.10),S2)             # 持ち送り
for x in (-0.66,-0.22,0.22,0.66):
    for y in (-0.66,0.66):
        cube("Mer",(x,y,3.42),(0.16,0.14,0.22),S)
    for yy in (-0.66,0.66):
        pass
for y in (-0.22,0.22):
    for x in (-0.82,0.82):
        cube("MerS",(x,y,3.42),(0.14,0.16,0.22),S)
finish("fort_tower", ratio=0.6, bevel=0.012)

# ============ fort_gate（2幅x3高の門楼・アーチ＋木扉＋落とし格子）============
reset()
S=STONE(); S2=STONE2(); WOOD=mat("GateWood",(0.40,0.27,0.15),0.7); IRON=mat("GateIron",(0.25,0.25,0.28),0.4,me=0.7)
# 両脇の塔状ピア（門の左右）
for sx in (-1,1):
    cube("Pier",(sx*0.9,0,1.5),(0.35,0.5,1.5),S)
    for z in (0.7,1.5,2.3):
        cube("PMort",(sx*0.9,0,z),(0.355,0.505,0.012),MORTAR())
# 上部の梁＋胸壁
cube("Lintel",(0,0,2.7),(1.25,0.5,0.30),S2)               # まぐさ
for x in (-0.85,-0.28,0.28,0.85):
    cube("GMer",(x,0.0,3.18),(0.16,0.5,0.22),S)            # 門上のクレネル
# 門の開口（中央 幅~1.0 x 高~2.4）に木扉＋落とし格子
cube("DoorL",(-0.26,0.30,1.15),(0.24,0.06,1.15),WOOD)
cube("DoorR",( 0.26,0.30,1.15),(0.24,0.06,1.15),WOOD)
for x in (-0.4,-0.13,0.13,0.4):
    cube("Bar",(x,0.40,1.3),(0.02,0.03,1.25),IRON)         # 落とし格子（縦棒）
for z in (0.4,1.3,2.2):
    cube("BarH",(0,0.40,z),(0.5,0.03,0.02),IRON)           # 横棒
finish("fort_gate", ratio=0.65, bevel=0.01)

# ============ fort_flag（旗竿＋幟・塔や壁に立てる・約2.3m）============
reset()
POLE=mat("Pole",(0.34,0.26,0.16),0.7); CLOTH=mat("Cloth",(0.70,0.16,0.16),0.7); GOLD=mat("FlagTop",(0.85,0.68,0.22),0.3,me=0.7)
cyl("Pole",(0,0,1.05),0.035,2.1,POLE,verts=10)
bpy.ops.mesh.primitive_cone_add(vertices=10,radius1=0.06,radius2=0.0,depth=0.16,location=(0,0,2.18))
o=bpy.context.active_object;o.name="Finial";o.data.materials.append(GOLD);parts.append(o)
# 幟（竿の片側になびく布）。前面+Y側にやや膨らみ
cube("Banner",(0.0,0.0,1.7),(0.005,0.34,0.42),CLOTH)      # 竿に沿う布（薄板）
cube("Banner2",(0.0,0.30,1.65),(0.005,0.06,0.36),CLOTH)   # なびく先端
# 三角の裾
bpy.ops.mesh.primitive_cone_add(vertices=4,radius1=0.30,radius2=0.0,depth=0.18,location=(0,0.0,1.40),rotation=(math.radians(90),0,0))
o=bpy.context.active_object;o.name="Tail";o.scale=(0.02,1.0,1.0);o.data.materials.append(CLOTH);parts.append(o)
finish("fort_flag", ratio=0.85, bevel=0.0, flat=False)

print("[voxel] all fort parts done")
