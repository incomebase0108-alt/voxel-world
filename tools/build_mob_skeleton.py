# -*- coding: utf-8 -*-
# VOXEL WORLD - 敵性モブ第三弾：スケルトン（遠距離型・弓持ち人型）
# Blender 5.1 / headless: blender --background --python tools/build_mob_skeleton.py
#   出力: models/mob_skeleton.glb （Y-up / 足元原点 / 正面 -Z / 身長約1.8m / 1ブロック≒1m）
#   アニメ: idle / walk / attack（敵性＝player/zombie と骨格・クリップ名統一）
# 方針: 骨色の人型。頭蓋＋眼窩・肋骨・細い骨の四肢・左手に弓。attack=弓を引く（右腕を後方へ引く）。
#   1号機の戦闘AIが「遠距離攻撃」を割り当てられる骨格で。subsurf1+decimateで軽量(<1MB)。

import bpy, os, math, mathutils

bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for blk in (bpy.data.meshes,bpy.data.materials,bpy.data.objects,bpy.data.actions):
    for it in list(blk):
        try: blk.remove(it)
        except Exception: pass
scene=bpy.context.scene; scene.render.fps=24

def mat(n,rgb,r=0.6,me=0.0):
    m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*rgb,1.0);b.inputs["Roughness"].default_value=r;b.inputs["Metallic"].default_value=me;return m
M_BONE=mat("Bone",(0.90,0.89,0.82),0.55); M_SOCKET=mat("Socket",(0.04,0.05,0.05),0.4)
M_BOW=mat("Bow",(0.35,0.22,0.10),0.6); M_STRING=mat("Str",(0.85,0.85,0.80),0.5)

def sphere(g,n,loc,s,m,segs=16,rings=10):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs,ring_count=rings,location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.data.materials.append(m);g.append(o);return o
def cyl(g,n,loc,r,d,m,verts=12,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d,location=loc)
    o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);g.append(o);return o
def cube(g,n,loc,s,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.rotation_euler=rot;o.data.materials.append(m);g.append(o);return o

BODY=[];ARML=[];ARMR=[];LEGL=[];LEGR=[]
# 脊椎・骨盤・肋骨（胴）
cyl(BODY,"Spine",(0,0,1.15),0.035,0.46,M_BONE)
sphere(BODY,"Pelvis",(0,0,0.92),(0.14,0.10,0.10),M_BONE)
for i,z in enumerate((1.06,1.16,1.26,1.36)):   # 肋骨リング
    cyl(BODY,"Rib%d"%i,(0,-0.02,z),0.13-0.005*i,0.025,M_BONE,verts=16,rot=(math.radians(90),0,0))
sphere(BODY,"ShoulderL",(0.20,0,1.42),(0.06,0.07,0.06),M_BONE)
sphere(BODY,"ShoulderR",(-0.20,0,1.42),(0.06,0.07,0.06),M_BONE)
cyl(BODY,"Collar",(0,0,1.42),0.18,0.022,M_BONE,verts=12,rot=(0,math.radians(90),0))
# 首・頭蓋
cyl(BODY,"Neck",(0,0,1.52),0.04,0.08,M_BONE)
sphere(BODY,"Skull",(0,0.01,1.64),(0.115,0.13,0.13),M_BONE,segs=22,rings=16)
sphere(BODY,"Jaw",(0,0.03,1.57),(0.09,0.08,0.06),M_BONE)
FY=0.10
sphere(BODY,"SocketL",(0.05,FY+0.02,1.66),(0.035,0.03,0.035),M_SOCKET,segs=12,rings=10)
sphere(BODY,"SocketR",(-0.05,FY+0.02,1.66),(0.035,0.03,0.035),M_SOCKET,segs=12,rings=10)
cube(BODY,"NoseHole",(0,FY+0.04,1.61),(0.015,0.02,0.02),M_SOCKET)
for i,x in enumerate((-0.03,0.0,0.03)):  # 歯
    cube(BODY,"Tooth%d"%i,(x,FY+0.03,1.55),(0.012,0.012,0.012),M_BONE)

# 腕（肩 z=1.42）。細い骨。左手に弓。
def arm(g,s,with_bow=False):
    x=0.22*s
    cyl(g,"Upper",(x,0,1.28),0.035,0.30,M_BONE)
    sphere(g,"ElbowB",(x,0,1.12),(0.04,0.04,0.04),M_BONE)
    cyl(g,"Fore",(x,0,0.96),0.03,0.28,M_BONE)
    sphere(g,"HandB",(x,0,0.80),(0.05,0.04,0.05),M_BONE)
    if with_bow:
        # 弓（前方=+Y に構える縦長の弧）＋弦
        cyl(g,"Bow",(x+0.03*s,0.10,0.96),0.012,0.46,M_BOW,verts=10,rot=(0,0,0))
        cube(g,"BowTipT",(x+0.03*s,0.07,1.17),(0.012,0.05,0.012),M_BOW,rot=(math.radians(28),0,0))
        cube(g,"BowTipB",(x+0.03*s,0.07,0.75),(0.012,0.05,0.012),M_BOW,rot=(math.radians(-28),0,0))
        cyl(g,"String",(x+0.03*s,0.045,0.96),0.004,0.44,M_STRING,verts=6)
arm(ARML,1,with_bow=True); arm(ARMR,-1)
# 脚（股関節 z=0.84）。細い骨。
def leg(g,s):
    x=0.08*s
    cyl(g,"Femur",(x,0,0.62),0.04,0.42,M_BONE)
    sphere(g,"KneeB",(x,0,0.40),(0.045,0.045,0.045),M_BONE)
    cyl(g,"Tibia",(x,0,0.22),0.035,0.36,M_BONE)
    cube(g,"FootB",(x,0.05,0.04),(0.06,0.13,0.05),M_BONE)
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
set_origin(armL,(0.20,0,1.42)); set_origin(armR,(-0.20,0,1.42))
set_origin(legL,(0.08,0,0.84)); set_origin(legR,(-0.08,0,0.84))

# 左腕（弓持ち）を前方へ構える＝-50°焼込／右腕は軽く前へ-25°
for a,ang in ((armL,-50),(armR,-25)):
    bpy.ops.object.select_all(action='DESELECT');a.select_set(True);bpy.context.view_layer.objects.active=a
    a.rotation_euler[0]=math.radians(ang); bpy.ops.object.transform_apply(location=False,rotation=True,scale=False)

for o in (body,armL,armR,legL,legR):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    sm=o.modifiers.new("S",'SUBSURF');sm.levels=1;sm.render_levels=1
    bpy.ops.object.shade_smooth();bpy.ops.object.modifier_apply(modifier=sm.name)
    d=o.modifiers.new("D",'DECIMATE');d.decimate_type='COLLAPSE';d.ratio=0.5
    bpy.ops.object.modifier_apply(modifier=d.name);bpy.ops.object.shade_smooth()

def parent(c,p):
    bpy.ops.object.select_all(action='DESELECT');c.select_set(True);p.select_set(True)
    bpy.context.view_layer.objects.active=p;bpy.ops.object.parent_set(type='OBJECT',keep_transform=True)
for limb in (armL,armR,legL,legR): parent(limb,body)

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

# idle: ゆらり＋頭わずか
new_action(body,"body_idle")
for f,d in [(1,-2),(30,2),(60,-2)]: kry(body,f,d)
push(body,"idle")
new_action(armR,"armR_idle")
for f,d in [(1,0),(30,6),(60,0)]: krx(armR,f,d)
push(armR,"idle")
# walk: 脚交互＋胴上下＋腕わずか
new_action(body,"body_walk")
for f,z in [(1,BZ),(8,BZ+0.018),(16,BZ),(24,BZ+0.018),(32,BZ)]: kz(body,f,z)
push(body,"walk")
for lg,sgn in [(legL,1),(legR,-1)]:
    new_action(lg,lg.name+"_walk")
    for f,p in [(1,1),(16,-1),(32,1)]: krx(lg,f,sgn*p*18)
    push(lg,"walk")
new_action(armR,"armR_walk")
for f,p in [(1,1),(16,-1),(32,1)]: krx(armR,f,p*8)
push(armR,"walk")
# attack: 弓を引く（右腕を後方へ引く→放つ）。左腕(弓)は構え保持。
new_action(armR,"armR_attack")
for f,d in [(1,0),(7,38),(12,38),(15,-10),(20,0)]: krx(armR,f,d)  # 引き絞り→保持→放ち→戻り
push(armR,"attack")
new_action(body,"body_attack")
for f,d in [(1,0),(10,4),(20,0)]: kry(body,f,d)                    # わずかに身構え
push(body,"attack")

repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."));models=os.path.join(repo,"models");os.makedirs(models,exist_ok=True)
out=os.path.join(models,"mob_skeleton.glb")
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_yup=True,
    export_apply=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_optimize_animation_size=True)
zs=[]
for o in (body,armL,armR,legL,legR):
    for v in o.bound_box: zs.append((o.matrix_world@mathutils.Vector(v)).z)
print("[voxel] export OK ->",out)
print("[voxel] height(Z) ~= %.2f m (feet %.3f)"%(max(zs),min(zs)))
print("[voxel] clips: idle / walk / attack")
