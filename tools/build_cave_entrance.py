# -*- coding: utf-8 -*-
# VOXEL WORLD - 横穴洞窟の入口パーツ（cave_entrance）【本採用】
# Blender 5.1 / headless: blender --background --python tools/build_cave_entrance.py
#   本採用フェーズ: models/cave_entrance.glb を出力し front/3q プレビューを tools/ に描画。
#   方向確認(commit 6a03780)で承認済の見た目をそのまま本採用。
#   規約: Y-up / 正面 Blender+Y(=glTF -Z) / 1ブロック≒1m / 接地原点 z=0 / 2MB以下・アニメ無し。
#   方針(司令塔): 山の斜面に置いて「ここが入口」と分かる横穴の口。
#     ゴツゴツした岩のアーチ＋垂れ下がるつらら状の岩牙＋奥が暗い喉（穴に吸い込まれる見た目）。
#   1号機の地形生成が山肌へ設置。正面(+Y)から入る。背面(-Y)が山の内側。

import bpy, os, math, mathutils, random, sys
V=mathutils.Vector
random.seed(7)
scene=bpy.context.scene
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for blk in (bpy.data.meshes,bpy.data.materials,bpy.data.objects):
    for it in list(blk):
        try: blk.remove(it)
        except Exception: pass

def mat(n,rgb,r=0.9,me=0.0,emis=None,es=1.5):
    m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*rgb,1.0);b.inputs["Roughness"].default_value=r;b.inputs["Metallic"].default_value=me
    if emis is not None:
        b.inputs["Emission Color"].default_value=(*emis,1.0); b.inputs["Emission Strength"].default_value=es
    return m

P=[]
def cube(loc,s,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.active_object;o.scale=s;o.rotation_euler=rot;o.data.materials.append(m);P.append(o);return o
def ico(loc,s,m,subd=1,rot=(0,0,0)):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subd,location=loc)
    o=bpy.context.active_object;o.scale=s;o.rotation_euler=rot;o.data.materials.append(m);P.append(o);return o
def cone(loc,r,d,m,verts=8,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r,radius2=0.0,depth=d,location=loc)
    o=bpy.context.active_object;o.rotation_euler=rot;o.data.materials.append(m);P.append(o);return o

ROCK =mat("Rock",(0.46,0.45,0.47),0.92)
ROCK2=mat("Rock2",(0.37,0.36,0.39),0.92)
ROCK3=mat("Rock3",(0.52,0.50,0.50),0.9)      # 明るめ岩（陽の当たる稜）
DARK =mat("CaveDark",(0.025,0.025,0.035),1.0)# 奥の闇（穴）
MOSS =mat("Moss",(0.18,0.30,0.12),0.95)      # 苔（口の縁に少し）
GLINT=mat("CaveGlint",(0.30,0.55,0.65),0.4,emis=(0.18,0.45,0.55),es=2.2)  # 奥のかすかな光(何かが居る示唆)

def rock(loc, s, m, jitter=0.18):
    r=(random.uniform(-jitter,jitter),random.uniform(-jitter,jitter),random.uniform(-jitter,jitter))
    sc=(s[0]*random.uniform(0.85,1.15), s[1]*random.uniform(0.85,1.15), s[2]*random.uniform(0.85,1.15))
    return ico(loc, sc, m, subd=1, rot=r)

# ===== 暗い喉（穴・最初に置いて奥に）=====
# 開口の奥に暗い箱状の空洞。正面(+Y)から覗くと闇＝穴に見える。背面(-Y)＝山の内側。
cube((0,-1.95,1.75),(1.7,0.12,1.75),DARK)                 # 奥の壁
cube((0,-1.1,0.10),(1.7,0.95,0.12),DARK)                  # 喉の床
cube((0,-1.1,3.35),(1.75,0.95,0.14),DARK)                 # 喉の天井
cube((-1.62,-1.1,1.7),(0.12,0.95,1.7),DARK)               # 喉の左壁
cube(( 1.62,-1.1,1.7),(0.12,0.95,1.7),DARK)               # 喉の右壁
ico((0.3,-1.7,1.4),(0.5,0.4,0.6),DARK,subd=1)             # 奥の不整な岩（闇に沈む）
ico((-0.4,-1.5,2.2),(0.45,0.4,0.5),DARK,subd=1)
cone((0.2,-1.6,2.05),0.10,0.7,GLINT,verts=8)              # 奥のかすかな光（結晶の気配）

# ===== 左右のゴツゴツした岩柱（ジャム）=====
for sgn in (1,-1):
    x=2.05*sgn
    rock((x,0.0,0.5),(0.62,0.7,0.6),ROCK)
    rock((x+0.12*sgn,0.05,1.4),(0.58,0.66,0.62),ROCK2)
    rock((x-0.05*sgn,-0.02,2.4),(0.55,0.62,0.6),ROCK)
    rock((x+0.08*sgn,0.04,3.25),(0.5,0.58,0.5),ROCK3)
    rock((x+0.30*sgn,0.06,0.35),(0.4,0.45,0.4),ROCK2)     # 裾の張り出し岩
    # 開口側へ少し迫り出す岩（口のゴツゴツ感）
    rock((x-0.55*sgn,0.18,1.6),(0.3,0.34,0.42),ROCK2,jitter=0.3)
    rock((x-0.5*sgn,0.16,2.5),(0.26,0.3,0.34),ROCK,jitter=0.3)

# ===== 上の庇・アーチ（重い岩のまぐさ）=====
for i,x in enumerate((-1.5,-0.6,0.3,1.2,1.9)):
    z=4.05+0.18*math.sin(i)        # 緩い弧
    rock((x,0.05,z),(0.62,0.7,0.55),ROCK if i%2 else ROCK2)
rock((0,0.10,4.5),(0.9,0.7,0.5),ROCK3)                     # 頂のかぶさり岩
rock((-0.2,0.28,3.7),(0.5,0.4,0.45),ROCK2,jitter=0.3)      # 庇が前へ迫り出す
rock((0.6,0.30,3.6),(0.45,0.38,0.4),ROCK,jitter=0.3)

# ===== つらら状の岩牙（開口の上縁から垂れる）=====
for i,x in enumerate((-1.25,-0.65,-0.05,0.55,1.15)):
    ln=random.uniform(0.55,1.05); rr=random.uniform(0.10,0.16)
    cone((x,0.0,3.4-ln/2),rr,ln,ROCK2 if i%2 else ROCK,verts=7,rot=(math.radians(180),0,random.uniform(-0.15,0.15)))
# 下からの石筍を数本（口の足元）
for x in (-1.4,1.3):
    cone((x,0.15,0.45),0.16,0.9,ROCK2,verts=8)

# ===== 敷居（足元の岩段）＋苔 =====
cube((0,0.55,0.12),(1.8,0.5,0.12),ROCK2,rot=(math.radians(-6),0,0))
rock((0.0,0.75,0.18),(0.7,0.3,0.18),ROCK)
# 苔：口の縁・庇の下に点々
for (mx,mz) in [(-1.7,2.6),(1.6,2.2),(-0.8,3.45),(0.9,3.4),(1.9,1.2)]:
    ico((mx,0.22,mz),(0.18,0.06,0.16),MOSS,subd=1)

# ===== 結合・原点(接地中心)・出力 =====
bpy.ops.object.select_all(action='DESELECT')
for o in P: o.select_set(True)
bpy.context.view_layer.objects.active=P[0]; bpy.ops.object.join()
o=bpy.context.active_object; o.name="cave_entrance"
bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
bv=o.modifiers.new("B",'BEVEL'); bv.width=0.02; bv.segments=1; bpy.ops.object.modifier_apply(modifier=bv.name)
d=o.modifiers.new("D",'DECIMATE'); d.decimate_type='COLLAPSE'; d.ratio=0.5; bpy.ops.object.modifier_apply(modifier=d.name)
bpy.ops.object.shade_flat()
bpy.context.view_layer.update()
xs=[(o.matrix_world@V(c)).x for c in o.bound_box]; ys=[(o.matrix_world@V(c)).y for c in o.bound_box]; zs=[(o.matrix_world@V(c)).z for c in o.bound_box]
scene.cursor.location=((min(xs)+max(xs))/2,(min(ys)+max(ys))/2,min(zs))   # 接地中心
bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
bpy.ops.object.origin_set(type='ORIGIN_CURSOR'); o.location=(0,0,0)

repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
models=os.path.join(repo,"models"); os.makedirs(models,exist_ok=True)
out=os.path.join(models,"cave_entrance.glb")
bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_animations=False)
print("[voxel] cave_entrance(models) -> %.3f MB  dims=%.2fx%.2fx%.2f (W×D×H)"%(os.path.getsize(out)/1048576, max(xs)-min(xs),max(ys)-min(ys),max(zs)-min(zs)))

# ===== プレビュー（front / 3q）=====
try:
    scene.render.engine='BLENDER_EEVEE_NEXT'
except Exception:
    scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=720; scene.render.resolution_y=720
scene.world=bpy.data.worlds.new("W"); scene.world.use_nodes=True
scene.world.node_tree.nodes["Background"].inputs[0].default_value=(0.55,0.62,0.72,1)
scene.world.node_tree.nodes["Background"].inputs[1].default_value=0.7
bpy.ops.object.light_add(type='SUN',location=(5,7,9)); bpy.context.active_object.data.energy=3.5
bpy.ops.object.light_add(type='SUN',location=(-4,6,3)); bpy.context.active_object.data.energy=1.2
def shot(name,loc,look=(0,-0.4,2.0)):
    bpy.ops.object.camera_add(location=loc); cam=bpy.context.active_object
    d=bpy.data.objects.new("E",None); scene.collection.objects.link(d); d.location=look
    cam.constraints.new('TRACK_TO').target=d; scene.camera=cam
    scene.render.filepath=os.path.join(repo,"tools",name); bpy.ops.render.render(write_still=True); print("[voxel] ->",name)
shot("hero_cave_entrance_front.png",(0.0, 9.0, 2.6))      # 正面(+Y)から口を覗く
shot("hero_cave_entrance_3q.png",  (-6.5, 7.0, 4.2))      # 前斜め
print("[voxel] cave_entrance preview done")
