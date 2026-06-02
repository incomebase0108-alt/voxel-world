# -*- coding: utf-8 -*-
# VOXEL WORLD - NPC：村人（中立・人型・取引/会話用）
# blender --background --python tools/build_npc_villager.py
#   出力: models/npc_villager.glb （Y-up / 足元原点 / 正面 -Z / 身長約1.75m / 1ブロック≒1m）
#   アニメ: idle / walk（人型と骨格・クリップ名統一。敵性ではないので attack なし）
# 方針: 茶のチュニック＋前掛け、穏やかな顔、簡素な髪。player/zombie と同リグ骨格。

import bpy, os, math, mathutils
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for blk in (bpy.data.meshes,bpy.data.materials,bpy.data.objects,bpy.data.actions):
    for it in list(blk):
        try: blk.remove(it)
        except Exception: pass
scene=bpy.context.scene; scene.render.fps=24
def mat(n,rgb,r=0.7):
    m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*rgb,1.0);b.inputs["Roughness"].default_value=r;return m
M_SKIN=mat("Skin",(0.85,0.65,0.51),0.5); M_TUNIC=mat("Tunic",(0.46,0.34,0.22)); M_APRON=mat("Apron",(0.62,0.55,0.42))
M_PANTS=mat("Pants",(0.30,0.28,0.30)); M_HAIR=mat("Hair",(0.22,0.15,0.08)); M_EYE=mat("Eye",(0.06,0.06,0.08))
M_MOUTH=mat("Mouth",(0.55,0.30,0.28)); M_BELT=mat("Belt",(0.28,0.18,0.10)); M_SHOE=mat("Shoe",(0.20,0.14,0.10))
def sphere(g,n,loc,s,m,segs=18,rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs,ring_count=rings,location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.data.materials.append(m);g.append(o);return o
def cyl(g,n,loc,r,d,m,verts=14,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d,location=loc)
    o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);g.append(o);return o
def cube(g,n,loc,s,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.rotation_euler=rot;o.data.materials.append(m);g.append(o);return o

BODY=[];ARML=[];ARMR=[];LEGL=[];LEGR=[]
# 胴（チュニック）＋前掛け＋帯
cube(BODY,"Torso",(0,0,1.12),(0.27,0.17,0.32),M_TUNIC)
cube(BODY,"Apron",(0,-0.16,1.02),(0.20,0.03,0.26),M_APRON)
cube(BODY,"Belt",(0,0,0.92),(0.29,0.18,0.05),M_BELT)
sphere(BODY,"ShoulderL",(0.26,0,1.40),(0.10,0.11,0.10),M_TUNIC)
sphere(BODY,"ShoulderR",(-0.26,0,1.40),(0.10,0.11,0.10),M_TUNIC)
# 首・頭・穏やかな顔・髪
cyl(BODY,"Neck",(0,0,1.52),0.07,0.10,M_SKIN)
sphere(BODY,"Head",(0,0,1.66),(0.13,0.14,0.15),M_SKIN,segs=24,rings=18)
FY=0.13
sphere(BODY,"EyeL",(0.05,FY,1.68),(0.022,0.018,0.024),M_EYE,segs=12,rings=10)
sphere(BODY,"EyeR",(-0.05,FY,1.68),(0.022,0.018,0.024),M_EYE,segs=12,rings=10)
sphere(BODY,"Nose",(0,FY+0.02,1.64),(0.02,0.03,0.025),M_SKIN,segs=12,rings=10)
cube(BODY,"Mouth",(0,FY,1.585),(0.04,0.012,0.012),M_MOUTH)
sphere(BODY,"Hair",(0,-0.02,1.73),(0.145,0.15,0.12),M_HAIR,segs=20,rings=14)
cube(BODY,"HairF",(0,FY-0.01,1.74),(0.13,0.03,0.04),M_HAIR)   # 前髪
# 腕（肩 z=1.40）：チュニック袖＋肌の前腕＋手
def arm(g,s):
    x=0.30*s
    cyl(g,"Sleeve",(x,0,1.28),0.075,0.30,M_TUNIC)
    cyl(g,"Fore",(x,0,0.98),0.06,0.28,M_SKIN)
    sphere(g,"Hand",(x,0,0.80),(0.065,0.05,0.075),M_SKIN)
arm(ARML,1); arm(ARMR,-1)
# 脚（股関節 z=0.84）：ズボン＋靴
def leg(g,s):
    x=0.10*s
    cyl(g,"Thigh",(x,0,0.62),0.09,0.42,M_PANTS)
    cyl(g,"Shin",(x,0,0.22),0.075,0.36,M_PANTS)
    cube(g,"Shoe",(x,0.05,0.04),(0.085,0.15,0.06),M_SHOE)
leg(LEGL,1); leg(LEGR,-1)

def join(group,name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in group:o.select_set(True)
    bpy.context.view_layer.objects.active=group[0];bpy.ops.object.join()
    o=bpy.context.active_object;o.name=name;return o
body=join(BODY,"Body");armL=join(ARML,"ArmL");armR=join(ARMR,"ArmR");legL=join(LEGL,"LegL");legR=join(LEGR,"LegR")
def set_origin(o,p):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    scene.cursor.location=p;bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
set_origin(body,(0,0,0)); set_origin(armL,(0.28,0,1.40)); set_origin(armR,(-0.28,0,1.40))
set_origin(legL,(0.10,0,0.84)); set_origin(legR,(-0.10,0,0.84))
for o in (body,armL,armR,legL,legR):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    sm=o.modifiers.new("S",'SUBSURF');sm.levels=1;sm.render_levels=1
    bpy.ops.object.shade_smooth();bpy.ops.object.modifier_apply(modifier=sm.name)
    d=o.modifiers.new("D",'DECIMATE');d.decimate_type='COLLAPSE';d.ratio=0.45
    bpy.ops.object.modifier_apply(modifier=d.name);bpy.ops.object.shade_smooth()
def parent(c,p):
    bpy.ops.object.select_all(action='DESELECT');c.select_set(True);p.select_set(True)
    bpy.context.view_layer.objects.active=p;bpy.ops.object.parent_set(type='OBJECT',keep_transform=True)
for limb in (armL,armR,legL,legR): parent(limb,body)
bpy.context.view_layer.update()
minz=min((o.matrix_world@mathutils.Vector(c)).z for o in (body,armL,armR,legL,legR) for c in o.bound_box)
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
for f,z in [(1,BZ),(30,BZ+0.012),(60,BZ)]: kz(body,f,z)
push(body,"idle")
for a,sgn in [(armL,1),(armR,-1)]:
    new_action(a,a.name+"_idle")
    for f,d in [(1,0),(30,5*sgn),(60,0)]: krx(a,f,d)
    push(a,"idle")
LA=20.0; AA=14.0
# walk: frame1=0 中立始点で一往復（glTFのrestが正しい立ち姿になるよう全クリップframe1中立）
new_action(legL,"LegL_walk")
for f,d in [(1,0),(8,LA),(16,0),(24,-LA),(32,0)]: krx(legL,f,d)
push(legL,"walk")
new_action(legR,"LegR_walk")
for f,d in [(1,0),(8,-LA),(16,0),(24,LA),(32,0)]: krx(legR,f,d)
push(legR,"walk")
new_action(armL,"ArmL_walk")
for f,d in [(1,0),(8,-AA),(16,0),(24,AA),(32,0)]: krx(armL,f,d)
push(armL,"walk")
new_action(armR,"ArmR_walk")
for f,d in [(1,0),(8,AA),(16,0),(24,-AA),(32,0)]: krx(armR,f,d)
push(armR,"walk")
new_action(body,"body_walk")
for f,z in [(1,BZ),(8,BZ+0.018),(16,BZ),(24,BZ+0.018),(32,BZ)]: kz(body,f,z)
push(body,"walk")
# 生活AI用 sit/work/talk（townsfolkと統一・全てframe1中立）
for lg in (legL,legR):
    new_action(lg,lg.name+"_sit")
    for f,d in [(1,0),(15,74),(40,75)]: krx(lg,f,d)
    push(lg,"sit")
new_action(body,"body_sit")
for f,z in [(1,BZ),(15,BZ-0.42),(40,BZ-0.42)]: kz(body,f,z)
push(body,"sit")
new_action(armR,"ArmR_work")
for f,d in [(1,0),(8,-55),(16,0),(24,-55),(32,0)]: krx(armR,f,d)
push(armR,"work")
new_action(body,"body_work")
for f,z in [(1,BZ),(8,BZ-0.012),(16,BZ),(24,BZ-0.012),(32,BZ)]: kz(body,f,z)
push(body,"work")
new_action(armR,"ArmR_talk")
for f,d in [(1,0),(20,-24),(40,0)]: krx(armR,f,d)
push(armR,"talk")
new_action(armL,"ArmL_talk")
for f,d in [(1,0),(25,20),(50,0)]: krx(armL,f,d)
push(armL,"talk")
new_action(body,"body_talk")
for f,z in [(1,BZ),(30,BZ+0.008),(60,BZ)]: kz(body,f,z)
push(body,"talk")

scene.frame_set(1)   # rest=frame1（全クリップ中立）でノード基準姿勢を確定
repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."));models=os.path.join(repo,"models");os.makedirs(models,exist_ok=True)
out=os.path.join(models,"npc_villager.glb")
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_yup=True,
    export_apply=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_optimize_animation_size=True)
print("[voxel] export OK ->",out); print("[voxel] clips: idle / walk / sit / work / talk")
