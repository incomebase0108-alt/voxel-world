# -*- coding: utf-8 -*-
# VOXEL WORLD - 王国城パーツ（大天守ほか・最終目標ランドマーク）【プレビュー方向確認フェーズ】
# Blender 5.1 / headless: blender --background --python tools/build_castle.py [-- --render]
#   ★preview限定: ライブ models/ は上書きせず tools/_work/castle_keep.glb に出力し、
#     front/3q プレビューを tools/ に描画する。OK後に models/ へ本採用＆他パーツ展開。
#   規約: Y-up / 足元中心z=0 / 正面 -Z(glTF)=Blender+Y / 1ブロック≒1m / 格子整合 / 軽量(flat+bevel+decimate)・アニメ無し。
#   方針(司令塔): 世界に1〜2個の最終目標。砦の素の角櫓と差別化し「王国」の格。
#     幅広の根石→主塔(明かりの窓・王旗)→四隅の円塔(青い円錐屋根＋金頂華)→中央の高い青尖塔(金頂華＋深紅の幟)→正面の大アーチ門。

import bpy, os, math, mathutils, sys
V=mathutils.Vector
scene=bpy.context.scene

def reset():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for blk in (bpy.data.meshes,bpy.data.materials,bpy.data.objects,bpy.data.actions):
        for it in list(blk):
            try: blk.remove(it)
            except Exception: pass
    parts.clear()

def mat(n,rgb,r=0.9,me=0.0,emis=None,es=2.0):
    m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*rgb,1.0);b.inputs["Roughness"].default_value=r;b.inputs["Metallic"].default_value=me
    if emis is not None:
        b.inputs["Emission Color"].default_value=(*emis,1.0); b.inputs["Emission Strength"].default_value=es
    return m

parts=[]
def cube(n,loc,s,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.rotation_euler=rot;o.data.materials.append(m);parts.append(o);return o
def cyl(n,loc,r,d,m,verts=16,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d,location=loc)
    o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);parts.append(o);return o
def cone(n,loc,r,d,m,verts=16,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r,radius2=0.0,depth=d,location=loc)
    o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);parts.append(o);return o

repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
work=os.path.join(repo,"tools","_work"); os.makedirs(work,exist_ok=True)

def finish(name, outdir, ratio=0.55, bevel=0.012):
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
    bpy.ops.object.shade_flat()
    bpy.context.view_layer.update()
    xs=[(o.matrix_world@V(c)).x for c in o.bound_box]; ys=[(o.matrix_world@V(c)).y for c in o.bound_box]; zs=[(o.matrix_world@V(c)).z for c in o.bound_box]
    scene.cursor.location=((min(xs)+max(xs))/2,(min(ys)+max(ys))/2,min(zs))   # 足元中心 z=0
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR'); o.location=(0,0,0)
    out=os.path.join(outdir,name+".glb")
    bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_animations=False)
    sz=os.path.getsize(out)
    print("[voxel] %-16s -> %.3f MB  dims=%.2fx%.2fx%.2f (W,D,H)"%(name, sz/1048576, max(xs)-min(xs),max(ys)-min(ys),max(zs)-min(zs)))
    return o

# 材質
def STONE(): return mat("Stone",(0.58,0.56,0.53),0.92)
def STONE2(): return mat("Stone2",(0.47,0.46,0.45),0.92)
def MORTAR(): return mat("Mortar",(0.36,0.35,0.34),0.9)
def ROOF(): return mat("Roof",(0.13,0.21,0.46),0.5)          # 王国の青い屋根
def ROOF2(): return mat("Roof2",(0.10,0.16,0.36),0.55)
def GOLD(): return mat("Gold",(0.88,0.71,0.24),0.3,me=0.85)  # 金の頂華・縁
def BANNER(): return mat("Banner",(0.66,0.13,0.15),0.7)      # 深紅の王旗
def WINDOW(): return mat("Window",(1.0,0.82,0.45),0.3,emis=(1.0,0.78,0.4),es=2.6)  # 灯る窓
def WOOD(): return mat("Wood",(0.40,0.27,0.15),0.7)
def IRON(): return mat("Iron",(0.24,0.24,0.27),0.4,me=0.7)

# =================== castle_keep（大天守ランドマーク）===================
reset()
S=STONE(); S2=STONE2(); MO=MORTAR(); RF=ROOF(); RF2=ROOF2(); GD=GOLD(); BN=BANNER(); WIN=WINDOW(); WD=WOOD(); IR=IRON()
FY=1  # 正面はBlender +Y（=glTF -Z）

# --- 幅広の根石（バッター＝下広がり）。footprint ~4.4x4.4 ---
cube("Plinth",(0,0,0.28),(2.2,2.2,0.28),S2)
cube("PlinthTop",(0,0,0.60),(2.0,2.0,0.06),GD)               # 金の見切り縁
# --- 主塔本体 3.2x3.2 / z0.66..5.0 ---
cube("Body",(0,0,2.83),(1.6,1.6,2.17),S)
for z in (1.3,2.0,2.7,3.4,4.1):                              # 石積み目地
    cube("Course",(0,0,z),(1.61,1.61,0.012),MO)
# 角の付け柱（垂直のリブ）
for sx in (-1,1):
    for sy in (-1,1):
        cube("Pilaster",(sx*1.58,sy*1.58,2.83),(0.06,0.06,2.17),S2)
# 灯る縦長アーチ窓（各面2つ、2段）— 前面と側面
def window(cx,cy,cz,face):  # face: 'y' or 'x'
    if face=='y':
        cube("WinR",(cx,cy,cz),(0.16,0.05,0.42),WIN)
        cube("WinFrm",(cx,cy-0.02*FY,cz),(0.22,0.04,0.50),S2)
        cone("WinArch",(cx,cy,cz+0.46),0.16,0.18,GD,verts=8,rot=(math.radians(-90*FY),0,0))
    else:
        cube("WinR",(cx,cy,cz),(0.05,0.16,0.42),WIN)
        cube("WinFrm",(cx,cy,cz),(0.04,0.22,0.50),S2)
for (wx) in (-0.7,0.7):
    for wz in (2.0,3.4):
        window(wx,1.61,wz,'y')                                # 前面(+Y)
for (wy) in (-0.7,0.7):
    for wz in (2.0,3.4):
        window(1.61*1,wy,wz,'x'); window(-1.61,wy,wz,'x')     # 左右面
# 正面中央の王紋（金の盾＋紋章）
cube("Crest",(0,1.64,3.0),(0.34,0.04,0.46),GD)
cube("CrestIn",(0,1.66,3.0),(0.22,0.03,0.32),BN)

# --- 主塔頂部：持ち送り＋クレネル胸壁 ---
cube("Corbel",(0,0,5.06),(1.78,1.78,0.12),S2)
cube("CorbelG",(0,0,5.14),(1.80,1.80,0.03),GD)
for x in (-1.5,-0.9,-0.3,0.3,0.9,1.5):                        # 前後縁メルロン
    for sy in (-1,1):
        cube("Mer",(x,sy*1.66,5.42),(0.20,0.16,0.26),S)
for y in (-0.9,-0.3,0.3,0.9):                                 # 左右縁メルロン
    for sx in (-1,1):
        cube("MerS",(sx*1.66,y,5.42),(0.16,0.20,0.26),S)

# --- 上段（一回り小さい第2層）3.0..? z5.18..6.4 ---
cube("Upper",(0,0,5.8),(1.15,1.15,0.62),S)
for z in (5.5,6.1):
    cube("UCourse",(0,0,z),(1.16,1.16,0.012),MO)
for wx in (-0.45,0.45):                                       # 上段の窓（前面）
    window(wx,1.16,5.95,'y')
cube("UCorbel",(0,0,6.46),(1.28,1.28,0.10),S2)

# --- 中央の高い青尖塔（4面ピラミッド）z6.5..9.3 ---
cone("Spire",(0,0,7.9),1.55,2.8,RF,verts=4,rot=(0,0,math.radians(45)))
cone("SpireBand",(0,0,6.75),1.45,0.5,RF2,verts=4,rot=(0,0,math.radians(45)))  # 裾の濃色帯
cyl("FinialRod",(0,0,9.35),0.04,0.5,GD,verts=8)
bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,location=(0,0,9.62))
o=bpy.context.active_object;o.name="FinialBall";o.scale=(0.12,0.12,0.14);o.data.materials.append(GD);parts.append(o)
cone("FinialTop",(0,0,9.86),0.07,0.20,GD,verts=8)
# 尖塔の深紅の王旗（前面+Yへなびく）
cyl("KBannerPole",(0,0,9.55),0.022,0.5,GD,verts=6)
cube("KBanner",(0,0.34,9.55),(0.006,0.34,0.30),BN)
bpy.ops.mesh.primitive_cone_add(vertices=4,radius1=0.30,radius2=0.0,depth=0.18,location=(0,0.55,9.40),rotation=(math.radians(90),0,0))
o=bpy.context.active_object;o.name="KBannerTail";o.scale=(0.012,1.0,1.0);o.data.materials.append(BN);parts.append(o)

# --- 四隅の円塔（青い円錐屋根＋金頂華）---
for sx in (-1,1):
    for sy in (-1,1):
        x=sx*1.85; y=sy*1.85
        cyl("TurBody",(x,y,2.9),0.46,5.4,S,verts=14)
        for z in (1.5,2.7,3.9,5.0):
            cyl("TurCourse",(x,y,z),0.47,0.012,MO,verts=14)
        cyl("TurCorbel",(x,y,5.66),0.54,0.10,S2,verts=14)
        # クレネル（小メルロン6つ）
        for k in range(6):
            a=math.radians(k*60)
            cube("TurMer",(x+0.5*math.cos(a),y+0.5*math.sin(a),5.84),(0.10,0.10,0.18),S)
        cone("TurRoof",(x,y,6.5),0.62,1.4,RF,verts=14)        # 青い円錐屋根
        cone("TurFinial",(x,y,7.35),0.05,0.22,GD,verts=8)     # 金の頂華
        # 円塔の灯る小窓（前面側）
        cube("TurWin",(x,y+0.46*1,3.4),(0.10,0.05,0.26),WIN)

# --- 正面の大アーチ門（前面 +Y 基部）---
cube("GateArchL",(-0.62,1.62,1.5),(0.18,0.10,1.5),S2)
cube("GateArchR",( 0.62,1.62,1.5),(0.18,0.10,1.5),S2)
cube("GateLintel",(0,1.62,2.5),(0.85,0.10,0.18),S2)
cone("GateArchTop",(0,1.62,2.55),0.62,0.5,S2,verts=10,rot=(math.radians(-90),0,0))
cube("GateArchGold",(0,1.66,2.5),(0.7,0.04,0.06),GD)
# 木扉＋落とし格子
cube("DoorL",(-0.28,1.55,1.2),(0.26,0.06,1.2),WD)
cube("DoorR",( 0.28,1.55,1.2),(0.26,0.06,1.2),WD)
for bx in (-0.42,-0.14,0.14,0.42):
    cube("PortBar",(bx,1.70,1.35),(0.02,0.03,1.3),IR)
for bz in (0.4,1.3,2.2):
    cube("PortBarH",(0,1.70,bz),(0.55,0.03,0.02),IR)
# 門脇の幟（壁旗・2本）
for sx in (-1,1):
    cube("WallBanner",(sx*1.0,1.66,2.0),(0.22,0.02,0.8),BN)
    cube("WallBannerT",(sx*1.0,1.66,1.55),(0.22,0.02,0.12),GD)

OUT = work if "--render" in sys.argv or "--preview" in sys.argv or True else os.path.join(repo,"models")
keep=finish("castle_keep", OUT, ratio=0.55, bevel=0.012)

# ---- プレビュー描画（昼光・建物 / --render 時のみ）----
try:
    if "--render" in sys.argv:
        try: scene.render.engine='BLENDER_EEVEE_NEXT'
        except Exception: scene.render.engine='BLENDER_EEVEE'
        scene.render.resolution_x=820; scene.render.resolution_y=980
        world=bpy.data.worlds.new("W"); scene.world=world; world.use_nodes=True
        world.node_tree.nodes["Background"].inputs[0].default_value=(0.45,0.58,0.78,1)   # 青空
        world.node_tree.nodes["Background"].inputs[1].default_value=1.0
        bpy.ops.object.light_add(type='SUN',location=(6,-8,12)); sun=bpy.context.active_object
        sun.data.energy=4.0; sun.rotation_euler=(math.radians(54),0,math.radians(32))
        bpy.ops.object.light_add(type='AREA',location=(-7,-6,6)); fill=bpy.context.active_object
        fill.data.energy=300; fill.data.color=(0.8,0.85,1.0); fill.data.size=8.0
        def shot(name,cam_loc,cam_rot,lens=40):
            bpy.ops.object.camera_add(location=cam_loc,rotation=cam_rot)
            cam=bpy.context.active_object; scene.camera=cam; cam.data.lens=lens
            scene.render.filepath=os.path.join(repo,"tools",name)
            bpy.ops.render.render(write_still=True)
            bpy.data.objects.remove(cam,do_unlink=True)
        # 正面（+Y側から）／3-4 俯瞰
        shot("hero_castle_keep_front.png",(0,16,5.2),(math.radians(84),0,math.radians(180)))
        shot("hero_castle_keep_3q.png",(12,12,8.5),(math.radians(72),0,math.radians(135)))
        print("[voxel] castle_keep preview rendered: tools/hero_castle_keep_front/3q.png")
except Exception as e:
    print("[voxel] castle preview skipped:", e)
