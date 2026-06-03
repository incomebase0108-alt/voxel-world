# -*- coding: utf-8 -*-
# VOXEL WORLD - 祠（聖域の小社・世界拡張②）
# Blender 5.1 / headless: blender --background --python tools/build_shrine.py [-- --preview] [-- --render]
#   規約: Y-up / 足元中心z=0 / 正面 -Z(glTF)=Blender+Y / 1ブロック≒1m / 格子整合 / 軽量(flat+bevel+decimate)・アニメ無し。
#   方針(司令塔): 王国城が「目標の格」なら、祠は「世界に点在する聖域の気配」。
#     石の段→朱の鳥居門→苔むした石社→灯る神器(発光)→脇の石灯籠。砦/城と素材で差別化(朱・苔・霊光)。
#   出力: models/shrine.glb（--preview 時のみ tools/_work/）。

import bpy, os, math, mathutils, sys
V=mathutils.Vector
scene=bpy.context.scene

parts=[]
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

def cube(n,loc,s,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.rotation_euler=rot;o.data.materials.append(m);parts.append(o);return o
def cyl(n,loc,r,d,m,verts=14,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d,location=loc)
    o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);parts.append(o);return o
def cone(n,loc,r,d,m,verts=14,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r,radius2=0.0,depth=d,location=loc)
    o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);parts.append(o);return o
def sphere(n,loc,s,m,segs=14,rings=10):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs,ring_count=rings,location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.data.materials.append(m);parts.append(o);return o

repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
work=os.path.join(repo,"tools","_work"); os.makedirs(work,exist_ok=True)

def finish(name, outdir, ratio=0.6, bevel=0.012):
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
    scene.cursor.location=((min(xs)+max(xs))/2,(min(ys)+max(ys))/2,min(zs))
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR'); o.location=(0,0,0)
    out=os.path.join(outdir,name+".glb")
    bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_animations=False)
    print("[voxel] %-14s -> %.3f MB  dims=%.2fx%.2fx%.2f (W,D,H)"%(name, os.path.getsize(out)/1048576, max(xs)-min(xs),max(ys)-min(ys),max(zs)-min(zs)))
    return o

# 材質
STONE=lambda:mat("Stone",(0.56,0.55,0.52),0.92)
STONE2=lambda:mat("Stone2",(0.46,0.46,0.44),0.92)
MOSS=lambda:mat("Moss",(0.28,0.42,0.20),0.9)
VERM=lambda:mat("Verm",(0.74,0.18,0.12),0.6)        # 朱（鳥居）
VERM2=lambda:mat("Verm2",(0.60,0.13,0.10),0.65)
WOOD=lambda:mat("Wood",(0.34,0.23,0.13),0.8)
ROOF=lambda:mat("Roof",(0.20,0.22,0.26),0.7)        # 苔まじりの板葺き(暗灰)
GOLD=lambda:mat("Gold",(0.86,0.70,0.26),0.3,me=0.8)
RELIC=lambda:mat("Relic",(0.6,0.95,1.0),0.2,emis=(0.5,0.9,1.0),es=3.4)   # 霊光の神器
LANT=lambda:mat("Lant",(1.0,0.82,0.45),0.3,emis=(1.0,0.75,0.4),es=2.8)   # 灯籠の灯
ROPE=lambda:mat("Rope",(0.86,0.82,0.66),0.8)        # 注連縄

# =================== shrine（聖域の小社）===================
reset()
S=STONE(); S2=STONE2(); MS=MOSS(); VM=VERM(); VM2=VERM2(); WD=WOOD(); RF=ROOF(); GD=GOLD(); RL=RELIC(); LT=LANT(); RP=ROPE()
FY=1  # 正面 +Y

# --- 石の基壇＋正面の段（footprint ~2.4x2.4）---
cube("Base",(0,0,0.16),(1.2,1.2,0.16),S2)
cube("BaseTop",(0,0,0.34),(1.05,1.05,0.04),S)
cube("Step1",(0,1.18,0.10),(0.55,0.16,0.10),S)       # 正面の踏み段
cube("Step2",(0,1.40,0.05),(0.45,0.12,0.05),S2)
cube("MossB1",(0.7,-0.6,0.34),(0.3,0.28,0.012),MS)   # 苔のしみ
cube("MossB2",(-0.55,0.5,0.34),(0.26,0.22,0.012),MS)

# --- 朱の鳥居門（正面 +Y の手前）---
TZ=1.62
for sx in (-1,1):
    cyl("ToriiPost%d"%sx,(sx*0.62,1.7,0.86),0.075,1.72,VM,verts=12)
cube("ToriiLintel",(0,1.7,1.66),(0.86,0.09,0.085),VM)        # 貫
cube("ToriiKasagi",(0,1.7,1.82),(0.98,0.12,0.10),VM2)        # 笠木（反り上端）
for sx in (-1,1):                                            # 笠木の反り端
    cube("ToriiTip%d"%sx,(sx*0.92,1.7,1.86),(0.10,0.13,0.06),VM2,rot=(0,math.radians(12*sx),0))
cube("ToriiGaku",(0,1.66,1.74),(0.13,0.03,0.10),GD)          # 額束（金）
# 注連縄
cube("Shime",(0,1.62,1.55),(0.70,0.04,0.05),RP)
for sx in (-0.4,0,0.4):
    cube("Shide%g"%sx,(sx,1.60,1.46),(0.03,0.012,0.10),RP)

# --- 苔むした石社（本体・奥）---
cube("Body",(0,-0.15,0.86),(0.62,0.50,0.52),S)
for z in (0.6,0.95):
    cube("Course%g"%z,(0,-0.15,z),(0.63,0.51,0.01),S2)       # 石目地
cube("MossBody",(0,-0.66,1.0),(0.5,0.02,0.34),MS)            # 背面の苔
cube("MossBody2",(0.55,-0.15,0.8),(0.02,0.4,0.3),MS)
# 正面の祠口（暗い奥＝神器が灯る）
cube("Niche",(0,0.30,0.84),(0.30,0.10,0.34),S2)
cube("NicheDark",(0,0.33,0.84),(0.24,0.06,0.28),mat("Dark",(0.05,0.05,0.06),0.9))
# 神器（霊光の珠＋台）
cyl("Pedestal",(0,0.30,0.62),0.10,0.10,S2,verts=12)
sphere("Relic",(0,0.30,0.80),(0.10,0.10,0.12),RL,segs=16,rings=12)
sphere("RelicGlow",(0,0.30,0.80),(0.16,0.16,0.18),mat("Glow",(0.5,0.9,1.0),0.2,emis=(0.5,0.9,1.0),es=1.2))

# --- 切妻屋根（反りのある板葺き）---
cube("Eave",(0,-0.15,1.16),(0.78,0.66,0.05),S2)             # 軒の見切り
cube("RoofL",(0,-0.15,1.30),(0.50,0.70,0.05),RF,rot=(0,math.radians(28),0))
cube("RoofR",(0,-0.15,1.30),(0.50,0.70,0.05),RF,rot=(0,math.radians(-28),0))
cube("Ridge",(0,-0.15,1.44),(0.06,0.74,0.05),GD)            # 棟（金）
cube("RoofMoss",(0.28,-0.15,1.34),(0.16,0.5,0.012),MS,rot=(0,math.radians(28),0))
for sy in (-1,1):                                           # 千木（棟端の交差材）
    cube("Chigi%d"%sy,(0,sy*0.72,1.52),(0.03,0.04,0.20),WD,rot=(math.radians(18*sy),0,0))

# --- 脇の石灯籠（2基・灯る）---
for sx in (-1,1):
    x=sx*1.0
    cyl("LantBase%d"%sx,(x,0.7,0.18),0.13,0.16,S2,verts=10)
    cyl("LantPole%d"%sx,(x,0.7,0.46),0.05,0.5,S,verts=8)
    cube("LantBox%d"%sx,(x,0.7,0.80),(0.13,0.13,0.13),S2)
    cube("LantFire%d"%sx,(x,0.7,0.80),(0.08,0.08,0.10),LT)   # 灯
    cone("LantCap%d"%sx,(x,0.7,0.98),0.18,0.16,S,verts=8)
    sphere("LantTop%d"%sx,(x,0.7,1.08),(0.05,0.05,0.06),S2)

OUT = work if "--preview" in sys.argv else os.path.join(repo,"models")
os.makedirs(OUT,exist_ok=True)
shrine=finish("shrine", OUT, ratio=0.6, bevel=0.012)

# ---- プレビュー描画（--render 時のみ）----
try:
    if "--render" in sys.argv:
        try: scene.render.engine='BLENDER_EEVEE_NEXT'
        except Exception: scene.render.engine='BLENDER_EEVEE'
        scene.render.resolution_x=860; scene.render.resolution_y=900
        world=bpy.data.worlds.new("W"); scene.world=world; world.use_nodes=True
        world.node_tree.nodes["Background"].inputs[0].default_value=(0.16,0.20,0.18,1)   # 木陰
        world.node_tree.nodes["Background"].inputs[1].default_value=0.9
        bpy.ops.object.light_add(type='SUN',location=(4,-6,9)); sun=bpy.context.active_object
        sun.data.energy=3.0; sun.rotation_euler=(math.radians(56),0,math.radians(30))
        bpy.ops.object.light_add(type='AREA',location=(-4,-4,4)); fill=bpy.context.active_object
        fill.data.energy=120; fill.data.color=(0.7,0.85,0.8); fill.data.size=5.0
        def shot(name,loc,rot,lens=45):
            bpy.ops.object.camera_add(location=loc,rotation=rot)
            cam=bpy.context.active_object; scene.camera=cam; cam.data.lens=lens
            scene.render.filepath=os.path.join(repo,"tools",name)
            bpy.ops.render.render(write_still=True); bpy.data.objects.remove(cam,do_unlink=True)
        shot("hero_shrine_front.png",(0,6.5,1.7),(math.radians(82),0,math.radians(180)))
        shot("hero_shrine_3q.png",(5,5,3.2),(math.radians(70),0,math.radians(135)))
        print("[voxel] shrine preview rendered: tools/hero_shrine_front/3q.png")
except Exception as e:
    print("[voxel] shrine preview skipped:", e)
