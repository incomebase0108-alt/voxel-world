# -*- coding: utf-8 -*-
# VOXEL WORLD - 敵性ボス：ゴーレム【迫力アップ作り込み版】
# blender --background --python tools/build_mob_golem.py
#   出力: models/mob_golem.glb （Y-up/足元z=0/正面-Z/身長約3.1m/2MB以下）
#   アニメ: idle / walk / attack / heavy（敵性骨格・クリップ名統一・frame1中立rest）
# 方針(司令塔): ボスらしい威圧感・重厚感。巨躯・層状の岩装甲＋肩/背の棘・発光する亀裂と核・
#   ゴツい眉と顎・巨大な拳。角張ったフラット岩肌(subsurf無し+bevel)。重い前傾の構え。

import bpy, os, math, mathutils
V=mathutils.Vector
scene=bpy.context.scene; scene.render.fps=24
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for blk in (bpy.data.meshes,bpy.data.materials,bpy.data.objects,bpy.data.actions):
    for it in list(blk):
        try: blk.remove(it)
        except Exception: pass

def mat(n,rgb,r=0.85,me=0.0,emis=None,es=4.0):
    m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*rgb,1.0);b.inputs["Roughness"].default_value=r;b.inputs["Metallic"].default_value=me
    if emis is not None:
        b.inputs["Emission Color"].default_value=(*emis,1.0); b.inputs["Emission Strength"].default_value=es
    return m
M_ROCK=mat("Rock",(0.40,0.42,0.40)); M_ROCK2=mat("Rock2",(0.30,0.32,0.31)); M_ROCK3=mat("Rock3",(0.24,0.26,0.26))
M_CORE=mat("Core",(1.0,0.55,0.12),0.25,emis=(1.0,0.5,0.12),es=6.0)
M_CRACK=mat("Crack",(1.0,0.45,0.10),0.4,emis=(1.0,0.4,0.08),es=4.5)   # 発光する亀裂
M_MOSS=mat("Moss",(0.30,0.40,0.22),0.9)

def cube(g,n,loc,s,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.rotation_euler=rot;o.data.materials.append(m);g.append(o);return o
def sphere(g,n,loc,s,m,segs=14,rings=10):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs,ring_count=rings,location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.data.materials.append(m);g.append(o);return o
def cone(g,n,loc,r,d,m,verts=4,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r,radius2=0.0,depth=d,location=loc)
    o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);g.append(o);return o

BODY=[];ARML=[];ARMR=[];LEGL=[];LEGR=[]
# ===== 胴（巨大な岩塊・前傾の重心）=====
cube(BODY,"Torso",(0,0,1.95),(0.50,0.38,0.56),M_ROCK)
cube(BODY,"Chest",(0,-0.10,2.05),(0.46,0.30,0.34),M_ROCK2)
cube(BODY,"Belly",(0,-0.04,1.42),(0.42,0.34,0.30),M_ROCK2)
# 発光する核（胸の中心）＋走る亀裂
sphere(BODY,"Core",(0,-0.34,2.05),(0.14,0.07,0.14),M_CORE)
cube(BODY,"CrackV",(0,-0.36,1.65),(0.035,0.02,0.40),M_CRACK)
cube(BODY,"CrackH",(0,-0.36,1.95),(0.30,0.02,0.03),M_CRACK)
cube(BODY,"CrackA",(0.22,-0.30,1.78),(0.02,0.02,0.22),M_CRACK,rot=(0,math.radians(28),0))
cube(BODY,"CrackB",(-0.22,-0.30,1.78),(0.02,0.02,0.22),M_CRACK,rot=(0,math.radians(-28),0))
# 肩（巨大・層状の岩装甲＋棘）
for sgn in (1,-1):
    cube(BODY,"Shoulder%d"%sgn,(0.54*sgn,0,2.28),(0.26,0.28,0.22),M_ROCK)
    cube(BODY,"ShoulderP%d"%sgn,(0.56*sgn,0,2.40),(0.22,0.24,0.10),M_ROCK2)
    cone(BODY,"Spike%d"%sgn,(0.60*sgn,0,2.55),0.13,0.34,M_ROCK3,verts=4,rot=(0,math.radians(10*sgn),0))  # 肩の棘
# 背の棘（3本）
for i,zz in enumerate((1.55,1.85,2.15)):
    cone(BODY,"BackSpike%d"%i,(0,0.34,zz),0.10,0.30,M_ROCK3,verts=4,rot=(math.radians(-70),0,0))
# 首・頭（低い首・ゴツい頭・光る目・張り出した眉）
cube(BODY,"Neck",(0,0,2.42),(0.16,0.16,0.10),M_ROCK2)
cube(BODY,"Head",(0,0.0,2.66),(0.27,0.26,0.24),M_ROCK)
cube(BODY,"Brow",(0,0.22,2.74),(0.28,0.08,0.07),M_ROCK2,rot=(math.radians(-12),0,0))   # 張り出し眉
cube(BODY,"Jaw",(0,0.10,2.50),(0.22,0.16,0.08),M_ROCK2)
sphere(BODY,"EyeL",(0.11,0.23,2.66),(0.05,0.025,0.04),M_CORE,segs=10,rings=8)
sphere(BODY,"EyeR",(-0.11,0.23,2.66),(0.05,0.025,0.04),M_CORE,segs=10,rings=8)
# 苔（風化感）
sphere(BODY,"Moss1",(0.30,0.20,2.20),(0.12,0.06,0.10),M_MOSS,segs=8,rings=6)
sphere(BODY,"Moss2",(-0.26,0.10,1.55),(0.10,0.06,0.12),M_MOSS,segs=8,rings=6)

# ===== 腕（肩ピボット z=2.28）巨大な岩腕＋拳 =====
def arm(g,sgn):
    x=0.62*sgn
    cube(g,"Upper",(x,0,1.90),(0.20,0.22,0.40),M_ROCK)
    cube(g,"Fore",(x,0.03,1.36),(0.21,0.22,0.38),M_ROCK2)
    cube(g,"ForeCrack",(x,-0.18,1.40),(0.02,0.02,0.20),M_CRACK)
    sphere(g,"Fist",(x,0.05,1.02),(0.26,0.24,0.24),M_ROCK)
    cube(g,"Knuckle",(x,0.24,1.02),(0.24,0.06,0.20),M_ROCK2)
    cone(g,"FistSpike",(x,0.30,1.18),0.07,0.18,M_ROCK3,verts=4,rot=(math.radians(70),0,0))
arm(ARML,1); arm(ARMR,-1)
# ===== 脚（股ピボット z=1.10）太く短い =====
def leg(g,sgn):
    x=0.24*sgn
    cube(g,"Thigh",(x,0,0.74),(0.24,0.26,0.50),M_ROCK)
    cube(g,"Shin",(x,0.01,0.30),(0.25,0.26,0.36),M_ROCK2)
    cube(g,"Foot",(x,0.12,0.08),(0.26,0.40,0.16),M_ROCK)
    cube(g,"Toe%d"%sgn,(x,0.34,0.06),(0.24,0.10,0.10),M_ROCK2)
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
set_origin(armL,(0.54,0,2.28)); set_origin(armR,(-0.54,0,2.28))
set_origin(legL,(0.24,0,1.10)); set_origin(legR,(-0.24,0,1.10))
# 石＝subsurfで丸めず bevel で角を立てたフラット岩肌
for o in (body,armL,armR,legL,legR):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    bv=o.modifiers.new("B",'BEVEL'); bv.width=0.018; bv.segments=1
    bpy.ops.object.modifier_apply(modifier=bv.name)
    bpy.ops.object.shade_flat()
def parent(c,p):
    bpy.ops.object.select_all(action='DESELECT');c.select_set(True);p.select_set(True)
    bpy.context.view_layer.objects.active=p;bpy.ops.object.parent_set(type='OBJECT',keep_transform=True)
for limb in (armL,armR,legL,legR): parent(limb,body)
bpy.context.view_layer.update()
minz=min((o.matrix_world@V(c)).z for o in (body,armL,armR,legL,legR) for c in o.bound_box)
body.location.z-=minz

# ---- アニメ（frame1中立）----
def new_action(o,n):
    if o.animation_data is None:o.animation_data_create()
    a=bpy.data.actions.new(n);a.use_fake_user=True;o.animation_data.action=a;return a
def push(o,t):
    ad=o.animation_data;act=ad.action;tr=ad.nla_tracks.new();tr.name=t
    tr.strips.new(act.name,int(act.frame_range[0]),act);ad.action=None
def kz(o,f,z):o.location.z=z;o.keyframe_insert('location',index=2,frame=f)
def krx(o,f,d):o.rotation_euler[0]=math.radians(d);o.keyframe_insert('rotation_euler',index=0,frame=f)
BZ=body.location.z
# idle: 重い呼吸
new_action(body,"body_idle")
for f,z in [(1,BZ),(40,BZ+0.035),(80,BZ)]: kz(body,f,z)
push(body,"idle")
for a in (armL,armR):
    new_action(a,a.name+"_idle")
    for f,d in [(1,0),(40,5),(80,0)]: krx(a,f,d)
    push(a,"idle")
# walk: 重い踏みしめ（frame1=0）
new_action(body,"body_walk")
for f,z in [(1,BZ),(10,BZ+0.05),(20,BZ),(30,BZ+0.05),(40,BZ)]: kz(body,f,z)
push(body,"walk")
for lg,sgn in [(legL,1),(legR,-1)]:
    new_action(lg,lg.name+"_walk")
    for f,d in [(1,0),(10,sgn*20),(20,0),(30,-sgn*20),(40,0)]: krx(lg,f,d)
    push(lg,"walk")
for a,sgn in [(armL,1),(armR,-1)]:
    new_action(a,a.name+"_walk")
    for f,d in [(1,0),(10,sgn*10),(20,0),(30,-sgn*10),(40,0)]: krx(a,f,d)
    push(a,"walk")
# attack: 右腕の横薙ぎ
new_action(armR,"armR_attack")
for f,d in [(1,0),(6,40),(12,-55),(20,0)]: krx(armR,f,d)
push(armR,"attack")
new_action(body,"body_attack")
for f,d in [(1,0),(12,-6),(20,0)]: krx(body,f,d)
push(body,"attack")
# heavy: 両腕振り上げ→地面叩き
new_action(armL,"armL_heavy")
for f,d in [(1,0),(10,75),(18,-70),(26,0)]: krx(armL,f,d)
push(armL,"heavy")
new_action(armR,"armR_heavy")
for f,d in [(1,0),(10,75),(18,-70),(26,0)]: krx(armR,f,d)
push(armR,"heavy")
new_action(body,"body_heavy")
for f,z in [(1,BZ),(10,BZ+0.05),(18,BZ-0.04),(26,BZ)]: kz(body,f,z)
push(body,"heavy")
scene.frame_set(1)

repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."));models=os.path.join(repo,"models");os.makedirs(models,exist_ok=True)
out=os.path.join(models,"mob_golem.glb")
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_yup=True,
    export_apply=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_optimize_animation_size=True)
zs=[(o.matrix_world@V(v)).z for o in (body,armL,armR,legL,legR) for v in o.bound_box]
sz=os.path.getsize(out)
print("[voxel] golem export -> %.3fMB  H%.2fm  clips: idle/walk/attack/heavy"%(sz/1048576, max(zs)))
