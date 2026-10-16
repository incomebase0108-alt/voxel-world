# -*- coding: utf-8 -*-
# VOXEL WORLD - 序章NPC：飼い主（わたし）= keeper（中年男性・1FのLDKにいる人）
# blender --background --python tools/build_npc_keeper.py
#   出力: models/npc_keeper.glb （Y-up / 足元原点 / 正面 -Z / 身長約1.70m / 1ブロック≒1m）
#   アニメ: idle / walk / sit（人型と骨格・クリップ名統一。歩きは任意だが既存NPC同等に付与）
#   骨格契約: Body / ArmL / ArmR / LegL / LegR（player/villager 準拠）
# 方針: さくらが“逆らえる”側＝威圧的でなく生活感のある中年男性。少しぽっちゃり、
#   くたびれたカーディガン＋部屋着ズボン＋スリッパ、短く薄めの髪、穏やかで気の良い顔。
#   ※頭上はネームプレート用にクリア（髪より上に物を置かない）。

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
M_SKIN =mat("Skin",(0.86,0.68,0.56),0.55)
M_CARD =mat("Cardigan",(0.45,0.50,0.58))      # くすんだ青灰のカーディガン（生活感）
M_SHIRT=mat("Shirt",(0.88,0.87,0.83))         # 中の白シャツ
M_PANTS=mat("Pants",(0.34,0.33,0.36))         # 部屋着の灰ズボン
M_HAIR =mat("Hair",(0.26,0.22,0.18))          # 白髪混じりの暗茶
M_BROW =mat("Brow",(0.30,0.25,0.20))
M_EYE  =mat("Eye",(0.10,0.09,0.10))
M_MOUTH=mat("Mouth",(0.55,0.34,0.32))
M_SLIP =mat("Slipper",(0.40,0.30,0.26))       # スリッパ（在宅感）
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
# 胴：カーディガン＋中のシャツ＋少しぽっちゃりのお腹（生活感）
cube(BODY,"Torso",(0,0,1.08),(0.30,0.20,0.34),M_CARD)
cube(BODY,"ShirtV",(0,0.155,1.12),(0.07,0.04,0.26),M_SHIRT)      # 前合わせの白シャツ
sphere(BODY,"Belly",(0,0.12,0.92),(0.235,0.175,0.205),M_CARD)    # ぽっこりお腹
sphere(BODY,"ShoulderL",(0.29,0,1.36),(0.115,0.12,0.115),M_CARD)
sphere(BODY,"ShoulderR",(-0.29,0,1.36),(0.115,0.12,0.115),M_CARD)
# 首・頭・穏やかな顔
cyl(BODY,"Neck",(0,0,1.48),0.075,0.11,M_SKIN)
sphere(BODY,"Head",(0,0,1.62),(0.135,0.145,0.155),M_SKIN,segs=24,rings=18)
sphere(BODY,"Jowl",(0,0.10,1.55),(0.10,0.07,0.08),M_SKIN,segs=14,rings=10)  # 少したるんだ頬（中年感）
FY=0.135
sphere(BODY,"EyeL",(0.052,FY,1.645),(0.022,0.018,0.024),M_EYE,segs=12,rings=10)
sphere(BODY,"EyeR",(-0.052,FY,1.645),(0.022,0.018,0.024),M_EYE,segs=12,rings=10)
cube(BODY,"BrowL",(0.052,FY+0.005,1.685),(0.035,0.012,0.012),M_BROW,rot=(0,0,math.radians(-4)))
cube(BODY,"BrowR",(-0.052,FY+0.005,1.685),(0.035,0.012,0.012),M_BROW,rot=(0,0,math.radians(4)))
sphere(BODY,"Nose",(0,FY+0.03,1.61),(0.024,0.034,0.03),M_SKIN,segs=12,rings=10)
cube(BODY,"Mouth",(0,FY,1.55),(0.045,0.012,0.012),M_MOUTH)
# 髪：短く薄め（生え際後退気味）＝サイド＋後頭部中心、頭頂は控えめ
sphere(BODY,"HairBack",(0,-0.05,1.66),(0.145,0.135,0.15),M_HAIR,segs=20,rings=14)
for sx in (1,-1):
    sphere(BODY,"HairSide%d"%sx,(0.115*sx,0.02,1.60),(0.045,0.10,0.10),M_HAIR,segs=12,rings=9)
cube(BODY,"HairTop",(0,-0.04,1.745),(0.115,0.12,0.03),M_HAIR)    # 頭頂の薄い毛
# 腕（肩 z=1.36）：カーディガン袖＋肌の前腕＋手。少し下げてリラックス。
def arm(g,s):
    x=0.31*s
    cyl(g,"Sleeve",(x,0,1.22),0.082,0.32,M_CARD)
    cyl(g,"Fore",(x,0.02,0.92),0.063,0.30,M_SKIN,rot=(math.radians(6),0,0))
    sphere(g,"Hand",(x,0.04,0.75),(0.07,0.055,0.08),M_SKIN)
arm(ARML,1); arm(ARMR,-1)
# 脚（股関節 z=0.82）：部屋着ズボン＋スリッパ
def leg(g,s):
    x=0.11*s
    cyl(g,"Thigh",(x,0,0.60),0.10,0.44,M_PANTS)
    cyl(g,"Shin",(x,0,0.20),0.082,0.36,M_PANTS)
    cube(g,"Slipper",(x,0.06,0.035),(0.092,0.16,0.05),M_SLIP)
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
set_origin(body,(0,0,0)); set_origin(armL,(0.29,0,1.36)); set_origin(armR,(-0.29,0,1.36))
set_origin(legL,(0.11,0,0.82)); set_origin(legR,(-0.11,0,0.82))
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
# idle：ゆったりした呼吸＋腕の小さな揺れ（のんびりした生活感）
new_action(body,"body_idle")
for f,z in [(1,BZ),(36,BZ+0.012),(72,BZ)]: kz(body,f,z)
push(body,"idle")
for a,sgn in [(armL,1),(armR,-1)]:
    new_action(a,a.name+"_idle")
    for f,d in [(1,0),(36,4*sgn),(72,0)]: krx(a,f,d)
    push(a,"idle")
# walk（既存NPC同等・frame1中立）
LA=18.0; AA=12.0
new_action(legL,"LegL_walk")
for f,d in [(1,0),(8,LA),(16,0),(24,-LA),(32,0)]: krx(legL,f,d)
push(legL,"walk")
new_action(legR,"LegR_walk")
for f,d in [(1,0),(8,-LA),(16,0),(24,LA),(32,0)]: krx(legR,f,d)
push(legR,"walk")
for a,sgn in [(armL,-1),(armR,1)]:
    new_action(a,a.name+"_walk")
    for f,d in [(1,0),(8,AA*sgn),(16,0),(24,-AA*sgn),(32,0)]: krx(a,f,d)
    push(a,"walk")
new_action(body,"body_walk")
for f,z in [(1,BZ),(8,BZ+0.016),(16,BZ),(24,BZ+0.016),(32,BZ)]: kz(body,f,z)
push(body,"walk")
# sit（ソファでくつろぐ・frame1中立）
for lg in (legL,legR):
    new_action(lg,lg.name+"_sit")
    for f,d in [(1,0),(15,72),(40,73)]: krx(lg,f,d)
    push(lg,"sit")
new_action(body,"body_sit")
for f,z in [(1,BZ),(15,BZ-0.40),(40,BZ-0.40)]: kz(body,f,z)
push(body,"sit")

scene.frame_set(1)
repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."));models=os.path.join(repo,"models");os.makedirs(models,exist_ok=True)
out=os.path.join(models,"npc_keeper.glb")
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_yup=True,
    export_apply=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_optimize_animation_size=True)
print("[voxel] export OK ->",out); print("[voxel] clips: idle / walk / sit")
