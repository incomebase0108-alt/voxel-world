# -*- coding: utf-8 -*-
# VOXEL WORLD - 中立モブ：馬（四足・将来の騎乗用候補）
# blender --background --python tools/build_mob_horse.py
#   出力: models/mob_horse.glb （Y-up / 足元原点 / 正面 -Z / 背の高さ約1.4m / 1ブロック≒1m）
#   アニメ: idle / walk（牛と骨格・クリップ名統一）
#   騎乗想定: 背(鞍)位置 ≒ 高さ1.4m / 体の中央やや前。鞍を載せてある。
import bpy, os, math, mathutils
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for blk in (bpy.data.meshes,bpy.data.materials,bpy.data.objects,bpy.data.actions):
    for it in list(blk):
        try: blk.remove(it)
        except Exception: pass
scene=bpy.context.scene; scene.render.fps=24
def mat(n,rgb,r=0.6):
    m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*rgb,1.0);b.inputs["Roughness"].default_value=r;return m
M_BODY=mat("Horse",(0.45,0.30,0.18)); M_MANE=mat("Mane",(0.20,0.13,0.08)); M_HOOF=mat("Hoof",(0.12,0.10,0.09))
M_EYE=mat("HEye",(0.05,0.04,0.04)); M_SADDLE=mat("Saddle",(0.30,0.16,0.10)); M_MUZZLE=mat("Muzzle",(0.30,0.20,0.12))
def sphere(g,n,loc,s,m,segs=16,rings=10):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs,ring_count=rings,location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.data.materials.append(m);g.append(o);return o
def cyl(g,n,loc,r,d,m,verts=12,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d,location=loc)
    o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);g.append(o);return o
def cube(g,n,loc,s,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.rotation_euler=rot;o.data.materials.append(m);g.append(o);return o
def set_origin(o,p):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    scene.cursor.location=p;bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

BODY=[]
# 胴（細長い）。背の高さ ≒ 1.30。
sphere(BODY,"Barrel",(0,0,1.18),(0.20,0.46,0.26),M_BODY,segs=20,rings=14)
sphere(BODY,"Chest",(0,0.34,1.16),(0.18,0.14,0.22),M_BODY)
sphere(BODY,"Rump",(0,-0.38,1.18),(0.19,0.16,0.23),M_BODY)
# 鞍（背の上・やや前）＝騎乗位置の目印。高さ≒1.42
cube(BODY,"Saddle",(0,0.05,1.40),(0.16,0.18,0.05),M_SADDLE)
cube(BODY,"SaddleHorn",(0,0.18,1.45),(0.04,0.04,0.05),M_SADDLE)
# 首（前方斜め上）
cyl(BODY,"Neck",(0,0.42,1.42),0.10,0.40,M_BODY,rot=(math.radians(55),0,0))
# 頭（前=+Y 上）
sphere(BODY,"Head",(0,0.60,1.62),(0.10,0.16,0.12),M_BODY,segs=16,rings=12)
sphere(BODY,"Muzzle",(0,0.66,1.52),(0.075,0.10,0.08),M_MUZZLE)
sphere(BODY,"EyeL",(0.07,0.62,1.66),(0.018,0.014,0.02),M_EYE,segs=8,rings=6)
sphere(BODY,"EyeR",(-0.07,0.62,1.66),(0.018,0.014,0.02),M_EYE,segs=8,rings=6)
cube(BODY,"EarL",(0.05,0.55,1.74),(0.02,0.02,0.05),M_BODY,rot=(math.radians(-10),0,0))
cube(BODY,"EarR",(-0.05,0.55,1.74),(0.02,0.02,0.05),M_BODY,rot=(math.radians(-10),0,0))
# たてがみ（首の後ろ稜線・濃色）
for i,t in enumerate([0.0,0.25,0.5,0.75,1.0]):
    z=1.30+t*0.30; y=0.30+t*0.22
    cube(BODY,"Mane%d"%i,(0,y,z+0.06),(0.03,0.05,0.07),M_MANE,rot=(math.radians(55),0,0))
# 尾（背面 -Y、流れる濃色）
TAIL=[]
cyl(TAIL,"Tail",(0,-0.50,1.00),0.04,0.40,M_MANE,rot=(math.radians(28),0,0))
sphere(TAIL,"TailEnd",(0,-0.56,0.78),(0.05,0.05,0.12),M_MANE)
# 脚×4（長い・股関節 z=0.85）
HIP=0.85; LEN=0.86
def make_leg(n,x,y):
    leg=cyl([],"_l",(x,y,HIP-LEN/2),0.05,LEN,M_BODY); leg.name=n
    hoof=cyl([],"_h",(x,y,0.04),0.055,0.08,M_HOOF); hoof.name=n+"_h"
    bpy.ops.object.select_all(action='DESELECT');leg.select_set(True);hoof.select_set(True)
    bpy.context.view_layer.objects.active=leg;bpy.ops.object.join()
    set_origin(leg,(x,y,HIP));return leg
legs={}
for n,x,y in [("LegFL",0.13,0.30),("LegFR",-0.13,0.30),("LegBL",0.13,-0.32),("LegBR",-0.13,-0.32)]:
    legs[n]=make_leg(n,x,y)

def join(group,name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in group:o.select_set(True)
    bpy.context.view_layer.objects.active=group[0];bpy.ops.object.join()
    o=bpy.context.active_object;o.name=name;return o
body=join(BODY,"Body");tail=join(TAIL,"Tail")
for o in (body,tail,*legs.values()):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    s=o.modifiers.new("S",'SUBSURF');s.levels=1;s.render_levels=1
    bpy.ops.object.shade_smooth();bpy.ops.object.modifier_apply(modifier=s.name)
    d=o.modifiers.new("D",'DECIMATE');d.decimate_type='COLLAPSE';d.ratio=0.5
    bpy.ops.object.modifier_apply(modifier=d.name);bpy.ops.object.shade_smooth()
set_origin(tail,(0,-0.46,1.05))
def parent(c,p):
    bpy.ops.object.select_all(action='DESELECT');c.select_set(True);p.select_set(True)
    bpy.context.view_layer.objects.active=p;bpy.ops.object.parent_set(type='OBJECT',keep_transform=True)
for c in (tail,*legs.values()): parent(c,body)
bpy.context.view_layer.update()
minz=min((o.matrix_world@mathutils.Vector(c)).z for o in (body,tail,*legs.values()) for c in o.bound_box)
body.location.z -= minz

def new_action(o,n):
    if o.animation_data is None:o.animation_data_create()
    a=bpy.data.actions.new(n);a.use_fake_user=True;o.animation_data.action=a;return a
def push(o,t):
    ad=o.animation_data;act=ad.action;tr=ad.nla_tracks.new();tr.name=t
    tr.strips.new(act.name,int(act.frame_range[0]),act);ad.action=None
def kz(o,f,z):o.location.z=z;o.keyframe_insert('location',index=2,frame=f)
def krx(o,f,d):o.rotation_euler[0]=math.radians(d);o.keyframe_insert('rotation_euler',index=0,frame=f)
def kry(o,f,d):o.rotation_euler[1]=math.radians(d);o.keyframe_insert('rotation_euler',index=1,frame=f)
BZ=body.location.z
new_action(body,"body_idle")
for f,z in [(1,BZ),(30,BZ+0.01),(60,BZ)]: kz(body,f,z)
push(body,"idle")
new_action(tail,"tail_idle")
for f,d in [(1,-6),(30,6),(60,-6)]: kry(tail,f,d)
push(tail,"idle")
AMP=20.0
for nm,sgn in [("LegFL",1),("LegBR",1),("LegFR",-1),("LegBL",-1)]:
    new_action(legs[nm],nm+"_walk")
    for f,p in [(1,1),(11,-1),(21,1)]: krx(legs[nm],f,sgn*p*AMP)
    push(legs[nm],"walk")
new_action(body,"body_walk")
for f,z in [(1,BZ),(6,BZ+0.02),(11,BZ),(16,BZ+0.02),(21,BZ)]: kz(body,f,z)
push(body,"walk")
new_action(tail,"tail_walk")
for f,d in [(1,-12),(11,12),(21,-12)]: kry(tail,f,d)
push(tail,"walk")

repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."));models=os.path.join(repo,"models");os.makedirs(models,exist_ok=True)
out=os.path.join(models,"mob_horse.glb")
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_yup=True,
    export_apply=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_optimize_animation_size=True)
print("[voxel] export OK ->",out); print("[voxel] clips: idle / walk ; 鞍(騎乗)位置≒高さ1.42m")
