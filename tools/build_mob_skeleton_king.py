# -*- coding: utf-8 -*-
# VOXEL WORLD - 敵性ボス：巨大スケルトン王（王冠／ボロ外套／大剣）【迫力ボス第2弾】
# Blender 5.1 / headless: blender --background --python tools/build_mob_skeleton_king.py [-- --render]
#   出力: models/mob_skeleton_king.glb （Y-up/足元z=0/正面+Y(→ゲームで-Z)/身長約3.4m/2MB以下）
#   アニメ: idle / walk / attack / heavy（敵性骨格・クリップ名統一・frame1中立rest）
#   骨格契約(golem/dragon準拠・不変): Body / ArmL / ArmR(=大剣を持つ) / LegL / LegR
# 方針(司令塔): 不死の王の威圧感。巨躯の骨格・鋭い頭蓋に冷光の眼・棘付き黄金の王冠＋宝玉・
#   ボロボロの王衣(深紅×金縁)・右手に大剣。attack=大剣の横薙ぎ / heavy=大上段からの叩き付け。
#   既存skeletonの骨質感(subsurf1+decimate)を踏襲して軽量。

import bpy, os, math, mathutils, sys
V=mathutils.Vector
scene=bpy.context.scene; scene.render.fps=24
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for blk in (bpy.data.meshes,bpy.data.materials,bpy.data.objects,bpy.data.actions):
    for it in list(blk):
        try: blk.remove(it)
        except Exception: pass

def mat(n,rgb,r=0.6,me=0.0,emis=None,es=4.0):
    m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*rgb,1.0);b.inputs["Roughness"].default_value=r;b.inputs["Metallic"].default_value=me
    if emis is not None:
        b.inputs["Emission Color"].default_value=(*emis,1.0); b.inputs["Emission Strength"].default_value=es
    return m
M_BONE =mat("Bone",(0.90,0.89,0.82),0.55); M_BONE2=mat("Bone2",(0.76,0.74,0.64),0.6)
M_SOCKET=mat("Socket",(0.03,0.04,0.04),0.4)
M_GLOW =mat("Glow",(0.45,0.95,1.0),0.2,emis=(0.35,0.9,1.0),es=7.0)     # 眼窩の冷光
M_GOLD =mat("Gold",(0.95,0.74,0.22),0.30,me=0.9); M_GOLD2=mat("Gold2",(0.78,0.58,0.15),0.35,me=0.9)
M_GEM  =mat("Gem",(0.85,0.10,0.45),0.2,emis=(0.95,0.12,0.5),es=6.0)    # 王冠の宝玉
M_CLOAK=mat("Cloak",(0.32,0.06,0.14),0.85); M_CLOAK2=mat("Cloak2",(0.20,0.04,0.09),0.9)  # 深紅の王衣
M_STEEL=mat("Steel",(0.62,0.64,0.70),0.30,me=0.85); M_STEEL2=mat("Steel2",(0.30,0.31,0.35),0.4,me=0.7)
M_RUNE =mat("Rune",(0.5,0.95,1.0),0.25,emis=(0.4,0.9,1.0),es=4.5)      # 刃のルーン光
M_HILT =mat("Hilt",(0.18,0.13,0.09),0.7)

def sphere(g,n,loc,s,m,segs=16,rings=10):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs,ring_count=rings,location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.data.materials.append(m);g.append(o);return o
def cyl(g,n,loc,r,d,m,verts=12,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d,location=loc)
    o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);g.append(o);return o
def cube(g,n,loc,s,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.rotation_euler=rot;o.data.materials.append(m);g.append(o);return o
def cone(g,n,loc,r,d,m,verts=6,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r,radius2=0.0,depth=d,location=loc)
    o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);g.append(o);return o

BODY=[];ARML=[];ARMR=[];LEGL=[];LEGR=[]
# 正面=+Y（顔側）。肩ピボット z=2.62 / 股ピボット z=1.58
# ===== 脊椎・骨盤・巨大な肋骨（胴）=====
cyl(BODY,"Spine",(0,0,2.10),0.07,0.95,M_BONE)
sphere(BODY,"Pelvis",(0,0,1.62),(0.26,0.18,0.18),M_BONE)
cube(BODY,"Sternum",(0,-0.20,2.20),(0.05,0.04,0.28),M_BONE2)
for i,z in enumerate((1.96,2.12,2.28,2.44)):          # 肋骨リング（前湾）
    r=0.27-0.018*i
    cyl(BODY,"Rib%d"%i,(0,-0.03,z),r,0.05,M_BONE,verts=18,rot=(math.radians(90),0,0))
    cube(BODY,"RibFront%d"%i,(0,-0.20,z),(0.16,0.05,0.04),M_BONE2)
sphere(BODY,"ShoulderL",(0.40,0,2.62),(0.12,0.13,0.12),M_BONE)
sphere(BODY,"ShoulderR",(-0.40,0,2.62),(0.12,0.13,0.12),M_BONE)
cyl(BODY,"Collar",(0,-0.02,2.60),0.34,0.05,M_BONE,verts=12,rot=(0,math.radians(90),0))
# 肩のスパイク装甲（王の威厳）
for sgn in (1,-1):
    cone(BODY,"ShoulderSpike%d"%sgn,(0.46*sgn,0,2.78),0.14,0.30,M_BONE2,verts=5,rot=(0,math.radians(14*sgn),0))

# ===== ボロボロの王衣（肩〜背〜長い裾・深紅×金縁）=====
cube(BODY,"Cloak",(0,0.30,2.20),(0.46,0.05,0.55),M_CLOAK,rot=(math.radians(-6),0,0))
cube(BODY,"CloakMid",(0,0.34,1.55),(0.40,0.05,0.45),M_CLOAK2,rot=(math.radians(-10),0,0))
cube(BODY,"CloakCollar",(0,0.06,2.66),(0.30,0.10,0.12),M_GOLD2,rot=(math.radians(-18),0,0))  # 金の襟
# 裾のラグ（不揃いに垂れる）
for i,x in enumerate((-0.34,-0.18,-0.02,0.16,0.32)):
    h=0.30 if i%2==0 else 0.20
    cube(BODY,"CloakRag%d"%i,(x,0.36,0.95-(0.04 if i%2 else 0)),(0.075,0.04,h),M_CLOAK2,rot=(math.radians(-12),0,0))
# 金の縦縁
for sgn in (1,-1):
    cube(BODY,"CloakTrim%d"%sgn,(0.30*sgn,0.28,1.85),(0.025,0.045,0.55),M_GOLD2,rot=(math.radians(-8),0,0))

# ===== 首・頭蓋（鋭い）=====
cyl(BODY,"Neck",(0,0,2.74),0.07,0.14,M_BONE)
sphere(BODY,"Skull",(0,0.02,2.94),(0.22,0.26,0.26),M_BONE,segs=24,rings=16)
cube(BODY,"BrowRidge",(0,0.20,3.02),(0.22,0.06,0.05),M_BONE2)
sphere(BODY,"CheekL",(0.13,0.14,2.88),(0.07,0.09,0.09),M_BONE2,segs=10,rings=8)
sphere(BODY,"CheekR",(-0.13,0.14,2.88),(0.07,0.09,0.09),M_BONE2,segs=10,rings=8)
cube(BODY,"Jaw",(0,0.12,2.80),(0.16,0.16,0.08),M_BONE2)
FY=0.18
sphere(BODY,"SocketL",(0.09,FY+0.02,2.95),(0.075,0.07,0.075),M_SOCKET,segs=12,rings=10)
sphere(BODY,"SocketR",(-0.09,FY+0.02,2.95),(0.075,0.07,0.075),M_SOCKET,segs=12,rings=10)
sphere(BODY,"GlowL",(0.09,FY+0.06,2.95),(0.040,0.035,0.040),M_GLOW,segs=10,rings=8)  # 冷光の眼
sphere(BODY,"GlowR",(-0.09,FY+0.06,2.95),(0.040,0.035,0.040),M_GLOW,segs=10,rings=8)
cube(BODY,"NoseHole",(0,FY+0.06,2.86),(0.028,0.045,0.045),M_SOCKET)
for i,x in enumerate((-0.06,-0.02,0.02,0.06)):  # 歯
    cube(BODY,"Tooth%d"%i,(x,FY+0.05,2.78),(0.022,0.026,0.022),M_BONE)

# ===== 棘付き黄金の王冠＋宝玉 =====
cyl(BODY,"CrownBand",(0,0.02,3.14),0.245,0.13,M_GOLD,verts=16)
# 前面5本・後面に低い棘
for i,ang in enumerate((-46,-23,0,23,46)):
    a=math.radians(ang)
    cx=0.245*math.sin(a); cy=0.245*math.cos(a)+0.02
    h=0.34 if i==2 else (0.26 if i in (1,3) else 0.20)
    cone(BODY,"CrownSpike%d"%i,(cx,cy,3.24+h*0.3),0.05,h,M_GOLD,verts=5)
for i,ang in enumerate((150,180,210)):
    a=math.radians(ang)
    cube(BODY,"CrownBack%d"%i,(0.245*math.sin(a),0.245*math.cos(a)+0.02,3.22),(0.04,0.04,0.12),M_GOLD2)
sphere(BODY,"CrownGem",(0,0.27,3.18),(0.05,0.04,0.05),M_GEM,segs=10,rings=8)   # 額の宝玉

# ===== 腕（肩 z=2.62）巨大な骨腕。ArmR=大剣 =====
def arm(g,sgn):
    x=0.42*sgn
    cyl(g,"Upper",(x,0,2.30),0.075,0.55,M_BONE)
    sphere(g,"Elbow",(x,0,2.00),(0.09,0.09,0.09),M_BONE)
    cyl(g,"Fore",(x,0.02,1.70),0.065,0.52,M_BONE)
    sphere(g,"Hand",(x,0.03,1.42),(0.10,0.09,0.10),M_BONE)
    # 指の骨（握り）
    for i,fx in enumerate((-0.05,0.0,0.05)):
        cube(g,"Finger%d_%d"%(sgn,i),(x+fx,0.10,1.40),(0.018,0.08,0.018),M_BONE2,rot=(math.radians(40),0,0))
arm(ARML,1); arm(ARMR,-1)
# ArmL：威嚇の鉤手（やや前へ開く）— 追加の爪
for i,fx in enumerate((-0.05,0.0,0.05)):
    cone(ARML,"ClawL%d"%i,(0.42+fx,0.18,1.34),0.02,0.10,M_BONE2,verts=4,rot=(math.radians(70),0,0))

# ===== 大剣（ArmR群：右手 z≈1.42 から上へ立てて構える）=====
xr=-0.42
cyl(ARMR,"SwGrip",(xr,0.12,1.62),0.035,0.42,M_HILT,verts=10)               # 握り
sphere(ARMR,"SwPommel",(xr,0.12,1.38),(0.07,0.07,0.07),M_GOLD2,segs=10,rings=8) # 柄頭
cube(ARMR,"SwGuard",(xr,0.12,1.86),(0.30,0.07,0.05),M_GOLD2)               # 鍔（広い十字鍔）
cube(ARMR,"SwGuardGem",(xr,0.16,1.86),(0.05,0.04,0.05),M_GEM)             # 鍔の宝玉
cube(ARMR,"SwBlade",(xr,0.12,2.78),(0.11,0.035,0.92),M_STEEL)             # 刃（長大）
cube(ARMR,"SwEdge",(xr,0.14,2.78),(0.025,0.02,0.90),M_RUNE)               # 刃のルーン光（中央線）
cone(ARMR,"SwTip",(xr,0.12,3.78),0.11,0.30,M_STEEL,verts=4,rot=(0,0,math.radians(45)))  # 切先

# ===== 脚（股 z=1.58）巨大な骨脚 =====
def leg(g,sgn):
    x=0.16*sgn
    cyl(g,"Femur",(x,0,1.18),0.085,0.78,M_BONE)
    sphere(g,"Knee",(x,0,0.76),(0.09,0.09,0.09),M_BONE)
    cyl(g,"Tibia",(x,0.02,0.42),0.07,0.68,M_BONE)
    cube(g,"Foot",(x,0.12,0.07),(0.12,0.26,0.10),M_BONE2)
    for i,fx in enumerate((-0.06,0.0,0.06)):   # 足指
        cube(g,"FToe%d_%d"%(sgn,i),(x+fx,0.26,0.05),(0.03,0.08,0.04),M_BONE2)
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
set_origin(armL,(0.40,0,2.62)); set_origin(armR,(-0.40,0,2.62))
set_origin(legL,(0.16,0,1.58)); set_origin(legR,(-0.16,0,1.58))
# 骨は丸み：subsurf1+decimate（軽量・skeleton準拠）。金属/王冠も同処理でOK
for o in (body,armL,armR,legL,legR):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    sm=o.modifiers.new("S",'SUBSURF');sm.levels=1;sm.render_levels=1
    bpy.ops.object.shade_smooth();bpy.ops.object.modifier_apply(modifier=sm.name)
    d=o.modifiers.new("D",'DECIMATE');d.decimate_type='COLLAPSE';d.ratio=0.5
    bpy.ops.object.modifier_apply(modifier=d.name);bpy.ops.object.shade_smooth()
def parent(c,p):
    bpy.ops.object.select_all(action='DESELECT');c.select_set(True);p.select_set(True)
    bpy.context.view_layer.objects.active=p;bpy.ops.object.parent_set(type='OBJECT',keep_transform=True)
for limb in (armL,armR,legL,legR): parent(limb,body)
bpy.context.view_layer.update()
minz=min((o.matrix_world@V(c)).z for o in (body,armL,armR,legL,legR) for c in o.bound_box)
body.location.z-=minz

# ---- アニメ（frame1中立rest）----
def new_action(o,n):
    if o.animation_data is None:o.animation_data_create()
    a=bpy.data.actions.new(n);a.use_fake_user=True;o.animation_data.action=a;return a
def push(o,t):
    ad=o.animation_data;act=ad.action;tr=ad.nla_tracks.new();tr.name=t
    tr.strips.new(act.name,int(act.frame_range[0]),act);ad.action=None
def kz(o,f,z):o.location.z=z;o.keyframe_insert('location',index=2,frame=f)
def krx(o,f,d):o.rotation_euler[0]=math.radians(d);o.keyframe_insert('rotation_euler',index=0,frame=f)
def krz(o,f,d):o.rotation_euler[2]=math.radians(d);o.keyframe_insert('rotation_euler',index=2,frame=f)
def kry(o,f,d):o.rotation_euler[1]=math.radians(d);o.keyframe_insert('rotation_euler',index=1,frame=f)
BZ=body.location.z

# idle: 重い揺らぎ＋大剣を担ぐ右腕の微動
new_action(body,"body_idle")
for f,d in [(1,-1.5),(40,1.5),(80,-1.5)]: kry(body,f,d)
push(body,"idle")
new_action(armR,"armR_idle")
for f,d in [(1,0),(40,4),(80,0)]: krx(armR,f,d)
push(armR,"idle")
new_action(armL,"armL_idle")
for f,d in [(1,0),(40,-5),(80,0)]: krx(armL,f,d)
push(armL,"idle")

# walk: 脚交互＋胴上下＋腕の振り
new_action(body,"body_walk")
for f,z in [(1,BZ),(10,BZ+0.04),(20,BZ),(30,BZ+0.04),(40,BZ)]: kz(body,f,z)
push(body,"walk")
for lg,sgn in [(legL,1),(legR,-1)]:
    new_action(lg,lg.name+"_walk")
    for f,d in [(1,0),(10,sgn*20),(20,0),(30,-sgn*20),(40,0)]: krx(lg,f,d)
    push(lg,"walk")
for a,sgn in [(armL,1),(armR,-1)]:
    new_action(a,a.name+"_walk")
    for f,d in [(1,0),(10,sgn*10),(20,0),(30,-sgn*10),(40,0)]: krx(a,f,d)
    push(a,"walk")

# attack: 大剣の横薙ぎ（右腕をZ回転で振り抜く）＋体の捻り
new_action(armR,"armR_attack")
for f,d in [(1,0),(6,35),(13,-70),(20,0)]: krz(armR,f,d)
push(armR,"attack")
new_action(body,"body_attack")
for f,d in [(1,0),(6,8),(13,-6),(20,0)]: kry(body,f,d)
push(body,"attack")

# heavy: 大上段からの叩き付け（右腕を振り上げ→前へ叩き付け）＋体の沈み込み
new_action(armR,"armR_heavy")
for f,d in [(1,0),(10,-115),(18,35),(26,0)]: krx(armR,f,d)
push(armR,"heavy")
new_action(body,"body_heavy")
for f,z in [(1,BZ),(10,BZ+0.06),(18,BZ-0.05),(26,BZ)]: kz(body,f,z)
push(body,"heavy")
new_action(armL,"armL_heavy")
for f,d in [(1,0),(10,18),(18,-12),(26,0)]: krx(armL,f,d)
push(armL,"heavy")
scene.frame_set(1)

repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."));models=os.path.join(repo,"models");os.makedirs(models,exist_ok=True)
out=os.path.join(models,"mob_skeleton_king.glb")
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_yup=True,
    export_apply=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_optimize_animation_size=True)
zs=[(o.matrix_world@V(v)).z for o in (body,armL,armR,legL,legR) for v in o.bound_box]
sz=os.path.getsize(out)
print("[voxel] skeleton_king export -> %.3fMB  H%.2fm  clips: idle/walk/attack/heavy"%(sz/1048576, max(zs)))

# ---- プレビュー描画（暗背景・失敗してもexport完了済み）----
try:
    if "--render" in sys.argv:
        scene.frame_set(1)
        try: scene.render.engine='BLENDER_EEVEE_NEXT'
        except Exception: scene.render.engine='BLENDER_EEVEE'
        scene.render.resolution_x=780; scene.render.resolution_y=940
        world=bpy.data.worlds.new("W"); scene.world=world; world.use_nodes=True
        world.node_tree.nodes["Background"].inputs[0].default_value=(0.05,0.055,0.07,1)
        world.node_tree.nodes["Background"].inputs[1].default_value=1.2
        bpy.ops.object.light_add(type='SUN',location=(3,-5,6)); sun=bpy.context.active_object
        sun.data.energy=4.5; sun.rotation_euler=(math.radians(52),0,math.radians(35))
        bpy.ops.object.light_add(type='AREA',location=(-3.5,-3,3.5)); fill=bpy.context.active_object
        fill.data.energy=280; fill.data.color=(0.5,0.7,1.0); fill.data.size=4.0
        def shot(name,cam_loc,cam_rot):
            bpy.ops.object.camera_add(location=cam_loc,rotation=cam_rot)
            cam=bpy.context.active_object; scene.camera=cam; cam.data.lens=44
            scene.render.filepath=os.path.join(repo,"tools",name)
            bpy.ops.render.render(write_still=True)
            bpy.data.objects.remove(cam,do_unlink=True)
        shot("hero_mob_skeleton_king_front.png",(0,6.4,2.0),(math.radians(85),0,math.radians(180)))
        shot("hero_mob_skeleton_king_3q.png",(4.4,4.6,2.5),(math.radians(80),0,math.radians(136)))
        print("[voxel] skeleton_king preview rendered")
except Exception as e:
    print("[voxel] preview render skipped:", e)
