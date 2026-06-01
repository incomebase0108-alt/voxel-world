# -*- coding: utf-8 -*-
# VOXEL WORLD - 敵性モブ第四弾：ゴーレム（大型ボス級・人型）
# Blender 5.1 / headless: blender --background --python tools/build_mob_golem.py
#   出力: models/mob_golem.glb （Y-up / 足元原点 / 正面 -Z / 身長約2.8m / 1ブロック≒1m）
#   アニメ: idle / walk / attack / heavy（敵性＝player/zombie と骨格・クリップ名統一＋強攻撃）
# 方針: 石の大型人型。岩肌＋ひび＋胸に光る核。巨大な腕と拳、太く短い脚、ゴツい頭。
#   subsurf1+decimateで軽量(<2MB)。1号機の戦闘AIに乗る骨格（body配下に腕=肩/脚=股関節）。

import bpy, os, math, mathutils

bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for blk in (bpy.data.meshes,bpy.data.materials,bpy.data.objects,bpy.data.actions):
    for it in list(blk):
        try: blk.remove(it)
        except Exception: pass
scene=bpy.context.scene; scene.render.fps=24

def mat(n,rgb,r=0.85,me=0.0):
    m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*rgb,1.0);b.inputs["Roughness"].default_value=r;b.inputs["Metallic"].default_value=me;return m
M_ROCK=mat("Rock",(0.40,0.42,0.40)); M_ROCK2=mat("Rock2",(0.30,0.32,0.31)); M_CORE=mat("Core",(1.0,0.5,0.12),0.25)
M_CRACK=mat("Crack",(0.15,0.10,0.08),0.6)

def cube(g,n,loc,s,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.rotation_euler=rot;o.data.materials.append(m);g.append(o);return o
def sphere(g,n,loc,s,m,segs=16,rings=10):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs,ring_count=rings,location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.data.materials.append(m);g.append(o);return o

BODY=[];ARML=[];ARMR=[];LEGL=[];LEGR=[]
# 胴（ゴツい岩塊）。中心高め。胸に光る核。
cube(BODY,"Torso",(0,0,1.75),(0.42,0.32,0.50),M_ROCK)
cube(BODY,"Belly",(0,-0.05,1.30),(0.38,0.30,0.26),M_ROCK2)
sphere(BODY,"Core",(0,-0.30,1.85),(0.12,0.06,0.12),M_CORE)        # 光る核
cube(BODY,"CrackV",(0,-0.31,1.55),(0.03,0.02,0.30),M_CRACK)       # 胸のひび
# 肩（巨大）
cube(BODY,"ShoulderL",(0.46,0,2.05),(0.20,0.22,0.18),M_ROCK)
cube(BODY,"ShoulderR",(-0.46,0,2.05),(0.20,0.22,0.18),M_ROCK)
# 頭（ゴツい・低い首）＋光る目
cube(BODY,"Head",(0,0.0,2.35),(0.22,0.22,0.20),M_ROCK)
cube(BODY,"Brow",(0,0.18,2.42),(0.22,0.06,0.05),M_ROCK2)
sphere(BODY,"EyeL",(0.09,0.19,2.36),(0.04,0.02,0.03),M_CORE,segs=10,rings=8)
sphere(BODY,"EyeR",(-0.09,0.19,2.36),(0.04,0.02,0.03),M_CORE,segs=10,rings=8)

# 腕（肩ピボット z=2.05）。巨大な岩腕＋拳。
def arm(g,s):
    x=0.52*s
    cube(g,"Upper",(x,0,1.70),(0.16,0.18,0.34),M_ROCK)
    cube(g,"Fore",(x,0.02,1.25),(0.17,0.18,0.32),M_ROCK2)
    sphere(g,"Fist",(x,0.04,0.98),(0.20,0.18,0.18),M_ROCK)
    cube(g,"Knuckle",(x,0.18,0.98),(0.18,0.05,0.16),M_ROCK2)
arm(ARML,1); arm(ARMR,-1)
# 脚（股関節 z=1.05）。太く短い。
def leg(g,s):
    x=0.20*s
    cube(g,"Thigh",(x,0,0.72),(0.20,0.22,0.46),M_ROCK)
    cube(g,"Shin",(x,0.01,0.30),(0.21,0.22,0.34),M_ROCK2)
    cube(g,"Foot",(x,0.10,0.07),(0.22,0.34,0.14),M_ROCK)
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
set_origin(body,(0,0,0))
set_origin(armL,(0.46,0,2.05)); set_origin(armR,(-0.46,0,2.05))
set_origin(legL,(0.20,0,1.05)); set_origin(legR,(-0.20,0,1.05))

# ゴーレムは石。subsurfで丸めず、軽いベベルで角を立てたままフラット陰影＝硬い岩肌。
for o in (body,armL,armR,legL,legR):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)  # 結合で残ったscaleを焼く
    bv=o.modifiers.new("B",'BEVEL'); bv.width=0.012; bv.segments=1
    bpy.ops.object.modifier_apply(modifier=bv.name)
    bpy.ops.object.shade_flat()   # 角張った岩肌（ブロック調はゴーレムでは正解）

def parent(c,p):
    bpy.ops.object.select_all(action='DESELECT');c.select_set(True);p.select_set(True)
    bpy.context.view_layer.objects.active=p;bpy.ops.object.parent_set(type='OBJECT',keep_transform=True)
for limb in (armL,armR,legL,legR): parent(limb,body)

# 接地スナップ：rest（アニメ前）で最下点を z=0 に合わせる（body=rootを持ち上げ、子も追従）
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

# idle: 重い呼吸（ゆっくり大きめ）
new_action(body,"body_idle")
for f,z in [(1,BZ),(40,BZ+0.03),(80,BZ)]: kz(body,f,z)
push(body,"idle")
for a in (armL,armR):
    new_action(a,a.name+"_idle")
    for f,d in [(1,0),(40,5),(80,0)]: krx(a,f,d)
    push(a,"idle")
# walk: 重い踏みしめ（脚大きめ・胴の上下大きめ・ゆっくり）
new_action(body,"body_walk")
for f,z in [(1,BZ),(10,BZ+0.04),(20,BZ),(30,BZ+0.04),(40,BZ)]: kz(body,f,z)
push(body,"walk")
for lg,sgn in [(legL,1),(legR,-1)]:
    new_action(lg,lg.name+"_walk")
    for f,p in [(1,1),(20,-1),(40,1)]: krx(lg,f,sgn*p*20)
    push(lg,"walk")
for a,sgn in [(armL,1),(armR,-1)]:
    new_action(a,a.name+"_walk")
    for f,p in [(1,1),(20,-1),(40,1)]: krx(a,f,sgn*p*10)
    push(a,"walk")
# attack: 右腕の横薙ぎ（振り上げ→振り下ろし）
new_action(armR,"armR_attack")
for f,d in [(1,0),(6,40),(12,-55),(20,0)]: krx(armR,f,d)
push(armR,"attack")
new_action(body,"body_attack")
for f,d in [(1,0),(12,-6),(20,0)]: krx(body,f,d)
push(body,"attack")
# heavy: 両腕を振り上げて地面叩き（強攻撃）＋胴を沈める
new_action(armL,"armL_heavy");
for f,d in [(1,0),(10,75),(18,-70),(26,0)]: krx(armL,f,d)
push(armL,"heavy")
new_action(armR,"armR_heavy")
for f,d in [(1,0),(10,75),(18,-70),(26,0)]: krx(armR,f,d)
push(armR,"heavy")
new_action(body,"body_heavy")
for f,z in [(1,BZ),(10,BZ+0.05),(18,BZ-0.04),(26,BZ)]: kz(body,f,z)
push(body,"heavy")

repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."));models=os.path.join(repo,"models");os.makedirs(models,exist_ok=True)
out=os.path.join(models,"mob_golem.glb")
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_yup=True,
    export_apply=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_optimize_animation_size=True)
zs=[]
for o in (body,armL,armR,legL,legR):
    for v in o.bound_box: zs.append((o.matrix_world@mathutils.Vector(v)).z)
print("[voxel] export OK ->",out)
print("[voxel] height(Z) ~= %.2f m (feet %.3f)"%(max(zs),min(zs)))
print("[voxel] clips: idle / walk / attack / heavy")
