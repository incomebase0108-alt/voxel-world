# -*- coding: utf-8 -*-
# VOXEL WORLD - 序章NPC：内縁の妻 = wife（2Fでさくらを見守る・さくら大好きの女性）
# blender --background --python tools/build_npc_wife.py
#   出力: models/npc_wife.glb （Y-up / 足元原点 / 正面 -Z / 身長約1.62m / 1ブロック≒1m）
#   アニメ: idle / walk（穏やかな idle が映える。歩きは任意だが既存NPC同等に付与）
#   骨格契約: Body / ArmL / ArmR / LegL / LegR（player/villager 準拠）
# 方針: 優しい雰囲気の女性。長めの髪・大きめの穏やかな目・ほんのり頬・やわらかい配色。
#   両手を体の前でそっと重ねた“見守る”立ち姿（近づくとハート演出が映える）。
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
M_SKIN =mat("Skin",(0.93,0.76,0.66),0.5)
M_TOP  =mat("Top",(0.96,0.80,0.82))          # やわらかな桜色のカーディガン
M_INNER=mat("Inner",(0.98,0.96,0.94))        # 中の生成りインナー
M_SKIRT=mat("Skirt",(0.55,0.45,0.52))        # くすみ藤色のスカート
M_HAIR =mat("Hair",(0.34,0.24,0.18))         # 温かみのある栗色
M_BROW =mat("Brow",(0.36,0.26,0.20))
M_EYE  =mat("Eye",(0.16,0.10,0.08))          # 柔らかな茶の瞳
M_HI   =mat("Hi",(1.0,1.0,1.0),0.1)          # 瞳ハイライト
M_MOUTH=mat("Mouth",(0.80,0.40,0.40))
M_BLUSH=mat("Blush",(0.99,0.74,0.74),0.6)    # ほんのり頬
M_SHOE =mat("Shoe",(0.40,0.30,0.34))
def sphere(g,n,loc,s,m,segs=18,rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs,ring_count=rings,location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.data.materials.append(m);g.append(o);return o
def cyl(g,n,loc,r,d,m,verts=14,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d,location=loc)
    o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);g.append(o);return o
def cone(g,n,loc,r1,r2,d,m,verts=20,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r1,radius2=r2,depth=d,location=loc)
    o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);g.append(o);return o
def cube(g,n,loc,s,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.rotation_euler=rot;o.data.materials.append(m);g.append(o);return o

BODY=[];ARML=[];ARMR=[];LEGL=[];LEGR=[]
# 胴：細身のカーディガン＋インナー、腰からふんわりスカート
cube(BODY,"Torso",(0,0,1.02),(0.22,0.15,0.30),M_TOP)
cube(BODY,"Inner",(0,0.14,1.04),(0.075,0.03,0.22),M_INNER)        # 胸元の生成り
cone(BODY,"Skirt",(0,0,0.60),0.30,0.20,0.40,M_SKIRT)             # ふんわりスカート（下広がり）
sphere(BODY,"ShoulderL",(0.225,0,1.26),(0.085,0.09,0.085),M_TOP)
sphere(BODY,"ShoulderR",(-0.225,0,1.26),(0.085,0.09,0.085),M_TOP)
# 首・頭・やさしい顔
cyl(BODY,"Neck",(0,0,1.38),0.058,0.10,M_SKIN)
sphere(BODY,"Head",(0,0,1.50),(0.125,0.135,0.145),M_SKIN,segs=24,rings=18)
FY=0.125
for sx in (1,-1):
    sphere(BODY,"Eye%d"%sx,(0.05*sx,FY,1.50),(0.028,0.024,0.030),M_EYE,segs=14,rings=11)   # 大きめの穏やかな目
    sphere(BODY,"Hi%d"%sx,(0.062*sx,FY+0.03,1.525),(0.010,0.010,0.011),M_HI,segs=8,rings=6) # ハイライト
    cube(BODY,"Brow%d"%sx,(0.05*sx,FY+0.003,1.545),(0.03,0.011,0.009),M_BROW,rot=(0,0,math.radians(-3*sx)))
    sphere(BODY,"Blush%d"%sx,(0.082*sx,FY-0.01,1.475),(0.028,0.018,0.022),M_BLUSH,segs=10,rings=8)
sphere(BODY,"Nose",(0,FY+0.02,1.485),(0.016,0.022,0.02),M_SKIN,segs=10,rings=8)
cube(BODY,"Mouth",(0,FY,1.45),(0.03,0.011,0.012),M_MOUTH)
# 髪：肩までの長め。後頭部の大きな束＋前髪＋左右に流れるサイド
sphere(BODY,"HairBack",(0,-0.06,1.52),(0.155,0.155,0.17),M_HAIR,segs=22,rings=16)
sphere(BODY,"HairLow",(0,-0.10,1.34),(0.135,0.10,0.14),M_HAIR,segs=18,rings=12)   # 肩までの毛先
for sx in (1,-1):
    sphere(BODY,"HairSide%d"%sx,(0.125*sx,0.02,1.44),(0.05,0.13,0.11),M_HAIR,segs=12,rings=10)
cube(BODY,"Bang",(0,FY-0.005,1.575),(0.125,0.035,0.05),M_HAIR)   # ふんわり前髪
# 腕（肩 z=1.26）：前で手をそっと重ねる“見守る”姿。袖＝桜色／前腕＝肌。
def arm(g,s):
    x=0.225*s
    cyl(g,"Sleeve",(x-0.015*s,0.03,1.10),0.055,0.24,M_TOP,rot=(math.radians(8),0,math.radians(16*s)))
    cyl(g,"Fore",(x-0.10*s,0.13,0.96),0.044,0.22,M_SKIN,rot=(math.radians(30),0,math.radians(34*s)))
    sphere(g,"Hand",(x-0.17*s,0.185,0.92),(0.05,0.045,0.055),M_SKIN)
arm(ARML,1); arm(ARMR,-1)
# 脚（股関節 z=0.80）：スカート下・細めのタイツ＋フラットシューズ
def leg(g,s):
    x=0.085*s
    cyl(g,"Thigh",(x,0,0.58),0.075,0.40,M_SKIN)
    cyl(g,"Shin",(x,0,0.22),0.058,0.36,M_SKIN)
    cube(g,"Shoe",(x,0.05,0.035),(0.07,0.13,0.05),M_SHOE)
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
set_origin(body,(0,0,0)); set_origin(armL,(0.225,0,1.26)); set_origin(armR,(-0.225,0,1.26))
set_origin(legL,(0.085,0,0.80)); set_origin(legR,(-0.085,0,0.80))
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
# idle：とても穏やかなゆっくりした呼吸＋手元のかすかな揺れ（見守る雰囲気）
new_action(body,"body_idle")
for f,z in [(1,BZ),(40,BZ+0.010),(80,BZ)]: kz(body,f,z)
push(body,"idle")
for a,sgn in [(armL,1),(armR,-1)]:
    new_action(a,a.name+"_idle")
    for f,d in [(1,0),(40,3*sgn),(80,0)]: krx(a,f,d)
    push(a,"idle")
# walk（既存NPC同等・frame1中立）
LA=15.0; AA=9.0
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
for f,z in [(1,BZ),(8,BZ+0.012),(16,BZ),(24,BZ+0.012),(32,BZ)]: kz(body,f,z)
push(body,"walk")

scene.frame_set(1)
repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."));models=os.path.join(repo,"models");os.makedirs(models,exist_ok=True)
out=os.path.join(models,"npc_wife.glb")
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_yup=True,
    export_apply=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_optimize_animation_size=True)
print("[voxel] export OK ->",out); print("[voxel] clips: idle / walk")
