# -*- coding: utf-8 -*-
# VOXEL WORLD - 中立モブ：豚（四足・食料源）
# blender --background --python tools/build_mob_pig.py
#   出力: models/mob_pig.glb （Y-up / 足元原点 / 正面 -Z / 高さ約0.75m / 1ブロック≒1m）
#   アニメ: idle / walk（牛と骨格・クリップ名統一）
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
M_PIG=mat("Pig",(0.93,0.66,0.66)); M_SNOUT=mat("PSnout",(0.88,0.56,0.56)); M_NOSE=mat("PNose",(0.55,0.32,0.34))
M_EYE=mat("PEye",(0.05,0.05,0.06)); M_HOOF=mat("PHoof",(0.30,0.22,0.22))
def sphere(g,n,loc,s,m,segs=16,rings=10):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs,ring_count=rings,location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.data.materials.append(m);g.append(o);return o
def cyl(g,n,loc,r,d,m,verts=12,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d,location=loc)
    o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);g.append(o);return o
def set_origin(o,p):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    scene.cursor.location=p;bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

BODY=[]
sphere(BODY,"Body",(0,0,0.46),(0.20,0.30,0.21),M_PIG,segs=18,rings=12)  # 丸い胴
HEAD=[]
sphere(HEAD,"Head",(0,0.32,0.50),(0.14,0.13,0.13),M_PIG,segs=16,rings=10)
sphere(HEAD,"Snout",(0,0.46,0.46),(0.08,0.06,0.07),M_SNOUT)
sphere(HEAD,"NoseL",(0.025,0.51,0.46),(0.015,0.01,0.015),M_NOSE,segs=8,rings=6)
sphere(HEAD,"NoseR",(-0.025,0.51,0.46),(0.015,0.01,0.015),M_NOSE,segs=8,rings=6)
sphere(HEAD,"EyeL",(0.07,0.42,0.55),(0.016,0.012,0.018),M_EYE,segs=8,rings=6)
sphere(HEAD,"EyeR",(-0.07,0.42,0.55),(0.016,0.012,0.018),M_EYE,segs=8,rings=6)
cyl(HEAD,"EarL",(0.09,0.30,0.60),0.03,0.02,M_PIG,verts=8,rot=(math.radians(20),0,0))
cyl(HEAD,"EarR",(-0.09,0.30,0.60),0.03,0.02,M_PIG,verts=8,rot=(math.radians(20),0,0))
# くるりんとした尾
TAIL=[]
cyl(TAIL,"Tail",(0,-0.30,0.52),0.012,0.08,M_PIG,verts=8,rot=(math.radians(-50),0,0))
sphere(TAIL,"TailTip",(0,-0.34,0.56),(0.02,0.02,0.02),M_PIG,segs=8,rings=6)
# 短い脚×4（股関節 z=0.30）
HIP=0.30; LEN=0.30
def make_leg(n,x,y):
    leg=cyl([],"_l",(x,y,HIP-LEN/2),0.045,LEN,M_PIG); leg.name=n
    hoof=cyl([],"_h",(x,y,0.03),0.05,0.05,M_HOOF); hoof.name=n+"_h"
    bpy.ops.object.select_all(action='DESELECT');leg.select_set(True);hoof.select_set(True)
    bpy.context.view_layer.objects.active=leg; bpy.ops.object.join()
    set_origin(leg,(x,y,HIP)); return leg
legs={}
for n,x,y in [("LegFL",0.11,0.18),("LegFR",-0.11,0.18),("LegBL",0.11,-0.18),("LegBR",-0.11,-0.18)]:
    legs[n]=make_leg(n,x,y)

def join(group,name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in group:o.select_set(True)
    bpy.context.view_layer.objects.active=group[0];bpy.ops.object.join()
    o=bpy.context.active_object;o.name=name;return o
body=join(BODY,"Body");head=join(HEAD,"Head");tail=join(TAIL,"Tail")
for o in (body,head,tail,*legs.values()):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    s=o.modifiers.new("S",'SUBSURF');s.levels=1;s.render_levels=1
    bpy.ops.object.shade_smooth();bpy.ops.object.modifier_apply(modifier=s.name)
    d=o.modifiers.new("D",'DECIMATE');d.decimate_type='COLLAPSE';d.ratio=0.5
    bpy.ops.object.modifier_apply(modifier=d.name);bpy.ops.object.shade_smooth()
set_origin(tail,(0,-0.28,0.52))

def parent(c,p):
    bpy.ops.object.select_all(action='DESELECT');c.select_set(True);p.select_set(True)
    bpy.context.view_layer.objects.active=p;bpy.ops.object.parent_set(type='OBJECT',keep_transform=True)
for c in (head,tail,*legs.values()): parent(c,body)
# 接地スナップ
bpy.context.view_layer.update()
minz=min((o.matrix_world@mathutils.Vector(c)).z for o in (body,head,tail,*legs.values()) for c in o.bound_box)
body.location.z -= minz

def new_action(o,n):
    if o.animation_data is None:o.animation_data_create()
    a=bpy.data.actions.new(n);a.use_fake_user=True;o.animation_data.action=a;return a
def push(o,t):
    ad=o.animation_data;act=ad.action;tr=ad.nla_tracks.new();tr.name=t
    tr.strips.new(act.name,int(act.frame_range[0]),act);ad.action=None
def kz(o,f,z):o.location.z=z;o.keyframe_insert('location',index=2,frame=f)
def krx(o,f,d):o.rotation_euler[0]=math.radians(d);o.keyframe_insert('rotation_euler',index=0,frame=f)
BZ=body.location.z
new_action(body,"body_idle")
for f,z in [(1,BZ),(24,BZ+0.012),(48,BZ)]: kz(body,f,z)
push(body,"idle")
new_action(head,"head_idle")
for f,d in [(1,0),(24,6),(48,0)]: krx(head,f,d)
push(head,"idle")
AMP=18.0
for nm,sgn in [("LegFL",1),("LegBR",1),("LegFR",-1),("LegBL",-1)]:
    new_action(legs[nm],nm+"_walk")
    for f,p in [(1,1),(11,-1),(21,1)]: krx(legs[nm],f,sgn*p*AMP)
    push(legs[nm],"walk")
new_action(body,"body_walk")
for f,z in [(1,BZ),(6,BZ+0.015),(11,BZ),(16,BZ+0.015),(21,BZ)]: kz(body,f,z)
push(body,"walk")

repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."));models=os.path.join(repo,"models");os.makedirs(models,exist_ok=True)
out=os.path.join(models,"mob_pig.glb")
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_yup=True,
    export_apply=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_optimize_animation_size=True)
print("[voxel] export OK ->",out); print("[voxel] clips: idle / walk")
