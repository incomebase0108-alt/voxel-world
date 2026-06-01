# -*- coding: utf-8 -*-
# VOXEL WORLD - 敵性モブ第二弾：ゾンビ（人型・敵性）
# Blender 5.1 / headless: blender --background --python tools/build_mob_zombie.py
#   出力: models/mob_zombie.glb （Y-up / 足元原点 / 正面 -Z / 身長約1.85m / 1ブロック≒1m）
#   アニメ: idle / walk / attack（player・敵性と骨格/クリップ名を統一）
# 方針: player と同じ「胴(body)配下に腕(肩)・脚(股関節)を階層化」リグ。
#   ゾンビ要素: 病的な緑肌・破れた暗色服・前に突き出した腕(ジオメトリに焼込)・光る目・猫背気味。
#   subsurf1+decimate で軽量(<1MB)。1号機の戦闘/スポーンAIが player と同骨格で効く。

import bpy, os, math, mathutils

bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for blk in (bpy.data.meshes,bpy.data.materials,bpy.data.objects,bpy.data.actions):
    for it in list(blk):
        try: blk.remove(it)
        except Exception: pass
scene=bpy.context.scene; scene.render.fps=24

def mat(n,rgb,r=0.7,me=0.0):
    m=bpy.data.materials.new(n); m.use_nodes=True; b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*rgb,1.0); b.inputs["Roughness"].default_value=r; b.inputs["Metallic"].default_value=me; return m
M_SKIN=mat("ZSkin",(0.46,0.56,0.40)); M_CLOTH=mat("ZCloth",(0.20,0.26,0.23),0.8)
M_EYE=mat("ZEye",(1.0,0.86,0.18),0.2); M_HAIR=mat("ZHair",(0.14,0.13,0.10)); M_MOUTH=mat("ZMouth",(0.10,0.06,0.06))
M_DARK=mat("ZDark",(0.12,0.16,0.14),0.85)

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
# 胴（破れた服）。やや猫背に見せるため上部をわずかに前傾配置
cube(BODY,"Torso",(0,0.02,1.16),(0.28,0.17,0.30),M_CLOTH)
sphere(BODY,"Chest",(0,-0.12,1.30),(0.24,0.10,0.16),M_CLOTH)
sphere(BODY,"ShoulderL",(0.27,0.02,1.42),(0.10,0.11,0.10),M_CLOTH)
sphere(BODY,"ShoulderR",(-0.27,0.02,1.42),(0.10,0.11,0.10),M_CLOTH)
# 破れ（裾の暗いギザ）
for i,x in enumerate((-0.18,-0.06,0.06,0.18)):
    cube(BODY,"Rag%d"%i,(x,0.0,0.86),(0.05,0.16,0.06),M_DARK,rot=(math.radians(12),0,0))
# 首・頭（前傾）
cyl(BODY,"Neck",(0,0.04,1.54),0.08,0.12,M_SKIN)
sphere(BODY,"Head",(0,0.06,1.70),(0.135,0.15,0.16),M_SKIN,segs=24,rings=16)
sphere(BODY,"Jaw",(0,0.05,1.62),(0.11,0.11,0.09),M_SKIN)
FY=0.14
sphere(BODY,"EyeL",(0.055,FY+0.04,1.72),(0.03,0.022,0.032),M_EYE,segs=12,rings=10)
sphere(BODY,"EyeR",(-0.055,FY+0.04,1.72),(0.03,0.022,0.032),M_EYE,segs=12,rings=10)
cube(BODY,"BrowL",(0.055,FY+0.03,1.76),(0.04,0.02,0.01),M_HAIR)
cube(BODY,"BrowR",(-0.055,FY+0.03,1.76),(0.04,0.02,0.01),M_HAIR)
cube(BODY,"Mouth",(0,FY+0.05,1.61),(0.05,0.02,0.025),M_MOUTH)  # 開いた口
sphere(BODY,"Hair",(0,0.02,1.77),(0.15,0.155,0.12),M_HAIR,segs=20,rings=14)

# 腕（肩ピボット z=1.42）。後で前方へ倒してジオメトリに焼く＝突き出し姿勢
def arm(g,s):
    x=0.32*s
    cyl(g,"Upper",(x,0,1.28),0.08,0.32,M_SKIN,rot=(0,math.radians(6*s),0))
    cyl(g,"Fore",(x+0.02*s,0,0.96),0.07,0.32,M_SKIN,rot=(0,math.radians(8*s),0))
    sphere(g,"Hand",(x+0.03*s,0,0.78),(0.075,0.06,0.085),M_SKIN)
arm(ARML,1); arm(ARMR,-1)
# 脚（股関節 z=0.84）
def leg(g,s):
    x=0.11*s
    cyl(g,"Thigh",(x,0,0.62),0.10,0.42,M_DARK)
    cyl(g,"Shin",(x,0,0.22),0.085,0.36,M_DARK)
    cube(g,"Foot",(x,0.05,0.05),(0.095,0.16,0.06),M_DARK)
leg(LEGL,1); leg(LEGR,-1)

def join(group,name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in group: o.select_set(True)
    bpy.context.view_layer.objects.active=group[0]; bpy.ops.object.join()
    o=bpy.context.active_object;o.name=name;return o
body=join(BODY,"Body");armL=join(ARML,"ArmL");armR=join(ARMR,"ArmR");legL=join(LEGL,"LegL");legR=join(LEGR,"LegR")

def set_origin(o,p):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    scene.cursor.location=p;bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
set_origin(body,(0,0,0))
set_origin(armL,(0.30,0,1.42)); set_origin(armR,(-0.30,0,1.42))
set_origin(legL,(0.11,0,0.84)); set_origin(legR,(-0.11,0,0.84))

# 腕を前方へ倒して焼き込み（ゾンビの突き出し）: X回転 -58°（前=+Y方向へ）
for a in (armL,armR):
    bpy.ops.object.select_all(action='DESELECT');a.select_set(True);bpy.context.view_layer.objects.active=a
    a.rotation_euler[0]=math.radians(-58); bpy.ops.object.transform_apply(location=False,rotation=True,scale=False)

# ジオメトリ確定（subsurf1+decimate）
for o in (body,armL,armR,legL,legR):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    sm=o.modifiers.new("S",'SUBSURF');sm.levels=1;sm.render_levels=1
    bpy.ops.object.shade_smooth();bpy.ops.object.modifier_apply(modifier=sm.name)
    d=o.modifiers.new("D",'DECIMATE');d.decimate_type='COLLAPSE';d.ratio=0.45
    bpy.ops.object.modifier_apply(modifier=d.name);bpy.ops.object.shade_smooth()

def parent(c,p):
    bpy.ops.object.select_all(action='DESELECT');c.select_set(True);p.select_set(True)
    bpy.context.view_layer.objects.active=p;bpy.ops.object.parent_set(type='OBJECT',keep_transform=True)
for limb in (armL,armR,legL,legR): parent(limb,body)

# アニメ
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

# idle: ゆっくり不気味に揺れる（胴の左右傾き＋腕の微揺れ）
new_action(body,"body_idle")
for f,d in [(1,-3),(30,3),(60,-3)]: kry(body,f,d)
push(body,"idle")
for a in (armL,armR):
    new_action(a,a.name+"_idle")
    for f,d in [(1,0),(30,8),(60,0)]: krx(a,f,d)   # 前後に少し
    push(a,"idle")
# walk: 引きずる歩行（脚は控えめ、胴が左右に揺れる、腕は前で少し上下）
new_action(body,"body_walk")
for f,z in [(1,BZ),(8,BZ+0.015),(16,BZ),(24,BZ+0.015),(32,BZ)]: kz(body,f,z)
push(body,"walk")
for lg,sgn in [(legL,1),(legR,-1)]:
    new_action(lg,lg.name+"_walk")
    for f,p in [(1,1),(16,-1),(32,1)]: krx(lg,f,sgn*p*14)
    push(lg,"walk")
for a,sgn in [(armL,1),(armR,-1)]:
    new_action(a,a.name+"_walk")
    for f,p in [(1,1),(16,-1),(32,1)]: krx(a,f,sgn*p*6)
    push(a,"walk")
# attack: 両腕を振り下ろす（前方へ）＋胴前傾
new_action(body,"body_attack")
for f,d in [(1,0),(8,-12),(16,0)]: krx(body,f,d)
push(body,"attack")
for a in (armL,armR):
    new_action(a,a.name+"_attack")
    for f,d in [(1,0),(5,28),(9,-35),(16,0)]: krx(a,f,d)  # 振り上げ→振り下ろし
    push(a,"attack")

repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."));models=os.path.join(repo,"models");os.makedirs(models,exist_ok=True)
out=os.path.join(models,"mob_zombie.glb")
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_yup=True,
    export_apply=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_optimize_animation_size=True)
zs=[]
for o in (body,armL,armR,legL,legR):
    for v in o.bound_box: zs.append((o.matrix_world@mathutils.Vector(v)).z)
print("[voxel] export OK ->",out)
print("[voxel] height(Z) ~= %.2f m (feet %.3f)"%(max(zs),min(zs)))
print("[voxel] clips: idle / walk / attack")
