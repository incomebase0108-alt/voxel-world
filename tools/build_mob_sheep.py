# -*- coding: utf-8 -*-
# VOXEL WORLD - モブ第二弾：羊（中立・小型四足） 生成スクリプト
# Blender 5.1 / headless: blender --background --python tools/build_mob_sheep.py
#   出力: models/mob_sheep.glb （Y-up / 足元原点 / 正面 -Z / 高さ約0.6m / 1ブロック≒1m）
#   アニメ: idle / walk（牛と骨格・クリップ名を統一）
# 方針: もこもこ白毛＋黒い顔。subsurf1+decimateで軽量(<1MB)。armature不使用・NLAトラック方式。

import bpy, os, math, mathutils

bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for blk in (bpy.data.meshes, bpy.data.materials, bpy.data.objects, bpy.data.actions):
    for it in list(blk):
        try: blk.remove(it)
        except Exception: pass
scene = bpy.context.scene; scene.render.fps = 24

def mat(n,rgb,r=0.8,me=0.0):
    m=bpy.data.materials.new(n); m.use_nodes=True; b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*rgb,1.0); b.inputs["Roughness"].default_value=r; b.inputs["Metallic"].default_value=me; return m
M_WOOL=mat("Wool",(0.95,0.95,0.93)); M_FACE=mat("Face",(0.16,0.14,0.13))
M_LEG =mat("Leg",(0.14,0.12,0.11));  M_EYE=mat("Eye",(0.04,0.04,0.05)); M_EAR=mat("Ear",(0.20,0.17,0.15))

def sphere(g,n,loc,s,m,segs=14,rings=10):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs,ring_count=rings,location=loc)
    o=bpy.context.active_object; o.name=n; o.scale=s; o.data.materials.append(m); g.append(o); return o
def cyl(g,n,loc,r,d,m,verts=12,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d,location=loc)
    o=bpy.context.active_object; o.name=n; o.rotation_euler=rot; o.data.materials.append(m); g.append(o); return o
def set_origin(o,p):
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
    scene.cursor.location=p; bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

BODY=[]
# もこもこ胴（中心の楕円＋毛玉バンプ）。中心 z=0.42。
sphere(BODY,"Wool",(0,0,0.42),(0.215,0.31,0.235),M_WOOL,segs=18,rings=12)
# 毛玉バンプを密に配置してモコモコの羊毛に（深く重ねて連続した綿の塊に）
for i,(x,y,z,s) in enumerate([(0.15,0.10,0.50,0.12),(-0.15,0.05,0.48,0.12),(0.12,-0.18,0.46,0.11),
                              (-0.12,-0.15,0.50,0.11),(0,0.20,0.46,0.11),(0,-0.26,0.44,0.10),
                              (0.16,-0.02,0.36,0.10),(-0.16,-0.05,0.38,0.10),
                              (0.10,0.02,0.58,0.105),(-0.10,0.0,0.56,0.105),(0.0,0.28,0.54,0.10),
                              (0.0,-0.04,0.60,0.11),(0.19,-0.14,0.45,0.095),(-0.19,-0.11,0.47,0.095),
                              (0.09,0.26,0.39,0.095),(-0.09,0.22,0.40,0.095),(0.0,-0.30,0.54,0.095),
                              (0.18,0.12,0.40,0.095),(-0.18,0.10,0.42,0.095)]):
    sphere(BODY,"Puff%d"%i,(x,y,z),(s,s,s),M_WOOL,segs=12,rings=8)
# 頭（前=+Y、黒い顔）
head_parts=[]
sphere(head_parts,"Head",(0,0.34,0.50),(0.12,0.13,0.13),M_FACE,segs=16,rings=10)
sphere(head_parts,"WoolTop",(0,0.30,0.58),(0.12,0.10,0.09),M_WOOL)   # 頭の毛
sphere(head_parts,"EyeL",(0.06,0.44,0.52),(0.018,0.014,0.02),M_EYE,segs=10,rings=8)
sphere(head_parts,"EyeR",(-0.06,0.44,0.52),(0.018,0.014,0.02),M_EYE,segs=10,rings=8)
sphere(head_parts,"EarL",(0.13,0.32,0.50),(0.055,0.025,0.035),M_EAR)
sphere(head_parts,"EarR",(-0.13,0.32,0.50),(0.055,0.025,0.035),M_EAR)
sphere(head_parts,"Snout",(0,0.46,0.47),(0.05,0.05,0.045),M_FACE)

# 脚 ×4（股関節 z=0.28、下端0）。前=+Y。
HIP=0.28; LEN=0.28
def make_leg(n,x,y):
    leg=cyl([],"_tmp",(x,y,HIP-LEN/2),0.04,LEN,M_LEG); leg.name=n
    set_origin(leg,(x,y,HIP)); return leg
legs={}
for n,x,y in [("LegFL",0.10,0.18),("LegFR",-0.10,0.18),("LegBL",0.10,-0.18),("LegBR",-0.10,-0.18)]:
    legs[n]=make_leg(n,x,y)
# 尾（短い・背面 -Y）
tail=cyl([],"_t",(0,-0.30,0.46),0.03,0.10,M_WOOL,rot=(math.radians(30),0,0)); tail.name="Tail"
set_origin(tail,(0,-0.28,0.50))

# ジオメトリ確定（subsurf1+decimate）
movable=[*legs.values(), tail]
geo_all=BODY+head_parts+movable
for o in geo_all:
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
    s=o.modifiers.new("S",'SUBSURF'); s.levels=1; s.render_levels=1
    bpy.ops.object.shade_smooth(); bpy.ops.object.modifier_apply(modifier=s.name)
    d=o.modifiers.new("D",'DECIMATE'); d.decimate_type='COLLAPSE'; d.ratio=0.5
    bpy.ops.object.modifier_apply(modifier=d.name); bpy.ops.object.shade_smooth()

# body結合（胴＋毛玉）、head結合
def join(group,name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in group: o.select_set(True)
    bpy.context.view_layer.objects.active=group[0]; bpy.ops.object.join()
    obj=bpy.context.active_object; obj.name=name; return obj
body=join(BODY,"Body"); head=join(head_parts,"Head")

def parent(c,p):
    bpy.ops.object.select_all(action='DESELECT'); c.select_set(True); p.select_set(True)
    bpy.context.view_layer.objects.active=p; bpy.ops.object.parent_set(type='OBJECT',keep_transform=True)
parent(head,body)
for lg in legs.values(): parent(lg,body)
parent(tail,body)

# アニメ（idle/walk）
def new_action(o,n):
    if o.animation_data is None: o.animation_data_create()
    a=bpy.data.actions.new(n); a.use_fake_user=True; o.animation_data.action=a; return a
def push(o,t):
    ad=o.animation_data; act=ad.action; tr=ad.nla_tracks.new(); tr.name=t
    tr.strips.new(act.name,int(act.frame_range[0]),act); ad.action=None
def kz(o,f,z): o.location.z=z; o.keyframe_insert('location',index=2,frame=f)
def krx(o,f,d): o.rotation_euler[0]=math.radians(d); o.keyframe_insert('rotation_euler',index=0,frame=f)
def kry(o,f,d): o.rotation_euler[1]=math.radians(d); o.keyframe_insert('rotation_euler',index=1,frame=f)
BZ=body.location.z

# idle
new_action(body,"body_idle")
for f,z in [(1,BZ),(24,BZ+0.015),(48,BZ)]: kz(body,f,z)
push(body,"idle")
new_action(head,"head_idle")
for f,d in [(1,0),(24,3),(48,0)]: krx(head,f,d)
push(head,"idle")
new_action(tail,"tail_idle")
for f,d in [(1,-5),(24,5),(48,-5)]: kry(tail,f,d)
push(tail,"idle")
# walk
AMP=20.0
phaseA=[legs["LegFL"],legs["LegBR"]]; phaseB=[legs["LegFR"],legs["LegBL"]]
def swing(o,sign):
    new_action(o,o.name+"_walk")
    for f,p in [(1,1),(11,-1),(21,1)]: krx(o,f,sign*p*AMP)
    push(o,"walk")
for lg in phaseA: swing(lg,1)
for lg in phaseB: swing(lg,-1)
new_action(body,"body_walk")
for f,z in [(1,BZ),(6,BZ+0.02),(11,BZ),(16,BZ+0.02),(21,BZ)]: kz(body,f,z)
push(body,"walk")
new_action(tail,"tail_walk")
for f,d in [(1,-10),(11,10),(21,-10)]: kry(tail,f,d)
push(tail,"walk")

# 書き出し
repo=os.path.abspath(os.path.join(os.path.dirname(__file__),"..")); models=os.path.join(repo,"models"); os.makedirs(models,exist_ok=True)
out=os.path.join(models,"mob_sheep.glb")
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_yup=True,
    export_apply=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_optimize_animation_size=True)
zs=[]; ys=[]; xs=[]
for o in [body,head,*legs.values(),tail]:
    for v in o.bound_box:
        w=o.matrix_world@mathutils.Vector(v); xs.append(w.x); ys.append(w.y); zs.append(w.z)
print("[voxel] export OK ->",out)
print("[voxel] bbox  X:%.2f..%.2f Y:%.2f..%.2f Z:%.2f..%.2f"%(min(xs),max(xs),min(ys),max(ys),min(zs),max(zs)))
print("[voxel] clips: idle / walk")
