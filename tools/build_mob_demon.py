# -*- coding: utf-8 -*-
# VOXEL WORLD - 敵性ボス：デーモン（魔系・マグマの悪魔）【迫力ボス第3弾】
# Blender 5.1 / headless: blender --background --python tools/build_mob_demon.py [-- --render]
#   出力: models/mob_demon.glb （Y-up/足元z=0/正面+Y(→ゲームで-Z)/身長約3.5m/2MB以下）
#   アニメ: idle / walk / attack / heavy（敵性骨格・クリップ名統一・frame1中立rest）
#   骨格契約(golem/dragon/skeleton_king準拠・不変): Body / ArmL / ArmR / LegL / LegR
# 方針(司令塔): ボス三系統の「魔系」。生物(ドラゴン)/アンデッド(スケ王)/岩(ゴーレム)と別物。
#   黒曜石/炭の肌＋溶岩(マグマ)の発光亀裂・湾曲した大角・蝙蝠翼(Body)・割れ蹄の逆関節脚・尾・鉤爪。
#   直立二足の鉤爪近接型。attack=爪の薙ぎ / heavy=両腕の叩き付け。subsurf1+decimateで軽量。

import bpy, os, math, mathutils, sys
V=mathutils.Vector
scene=bpy.context.scene; scene.render.fps=24
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for blk in (bpy.data.meshes,bpy.data.materials,bpy.data.objects,bpy.data.actions):
    for it in list(blk):
        try: blk.remove(it)
        except Exception: pass

def mat(n,rgb,r=0.7,me=0.0,emis=None,es=4.0):
    m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*rgb,1.0);b.inputs["Roughness"].default_value=r;b.inputs["Metallic"].default_value=me
    if emis is not None:
        b.inputs["Emission Color"].default_value=(*emis,1.0); b.inputs["Emission Strength"].default_value=es
    return m
M_SKIN =mat("Skin",(0.21,0.16,0.17),0.7)          # 黒曜石/炭の肌（黒つぶれ回避で少し明るく）
M_SKIN2=mat("Skin2",(0.14,0.10,0.11),0.76)         # 影部
M_MAGMA=mat("Magma",(1.0,0.32,0.05),0.2,emis=(1.0,0.30,0.04),es=10.0)   # 溶岩の発光亀裂・目・口
M_MAGMA2=mat("Magma2",(1.0,0.55,0.12),0.25,emis=(1.0,0.5,0.10),es=6.5)
M_HORN =mat("Horn",(0.24,0.18,0.16),0.42)          # 角：黒光り（暗背景で読めるよう中明度）
M_HORNT=mat("HornT",(0.38,0.27,0.21),0.4)          # 角の根（明）
M_WING =mat("Wing",(0.15,0.08,0.09),0.7)           # 翼の骨
M_MEMB =mat("Memb",(0.24,0.07,0.08),0.8)           # 翼膜：黒赤
M_MEMB2=mat("Memb2",(0.16,0.05,0.06),0.85)
M_CLAW =mat("Claw",(0.07,0.06,0.06),0.4)           # 鉤爪・蹄：黒
M_HOOF =mat("Hoof",(0.06,0.05,0.05),0.45)

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
# 正面=+Y（顔側）。肩ピボット z=2.70 / 股ピボット z=1.66
# ===== 胴（筋肉質・逆三角の上体・前傾の重心）=====
cube(BODY,"Torso",(0,-0.05,2.10),(0.42,0.32,0.46),M_SKIN)
sphere(BODY,"Chest",(0,-0.16,2.34),(0.44,0.26,0.30),M_SKIN)
sphere(BODY,"PecL",(0.18,-0.26,2.30),(0.17,0.14,0.15),M_SKIN)
sphere(BODY,"PecR",(-0.18,-0.26,2.30),(0.17,0.14,0.15),M_SKIN)
sphere(BODY,"Abs",(0,-0.20,1.92),(0.26,0.16,0.22),M_SKIN2)
sphere(BODY,"Waist",(0,-0.04,1.70),(0.24,0.18,0.16),M_SKIN2)
# 胸の溶岩核＋走る亀裂（魔系の核）
sphere(BODY,"Core",(0,-0.34,2.18),(0.14,0.08,0.14),M_MAGMA)
cube(BODY,"CrackV",(0,-0.34,1.92),(0.03,0.02,0.34),M_MAGMA)
cube(BODY,"CrackH",(0,-0.34,2.30),(0.26,0.02,0.025),M_MAGMA2)
for sgn in (1,-1):
    cube(BODY,"CrackArm%d"%sgn,(0.24*sgn,-0.28,2.06),(0.02,0.02,0.24),M_MAGMA,rot=(0,math.radians(24*sgn),0))
    cube(BODY,"CrackAb%d"%sgn,(0.12*sgn,-0.30,1.84),(0.02,0.02,0.16),M_MAGMA2)
# 肩のスパイク装甲（黒角の塊）
for sgn in (1,-1):
    sphere(BODY,"Shoulder%d"%sgn,(0.40*sgn,0,2.66),(0.20,0.20,0.18),M_SKIN)
    cone(BODY,"ShSpikeA%d"%sgn,(0.46*sgn,-0.02,2.86),0.10,0.34,M_HORN,verts=5,rot=(0,math.radians(20*sgn),0))
    cone(BODY,"ShSpikeB%d"%sgn,(0.40*sgn,-0.18,2.76),0.07,0.22,M_HORN,verts=5,rot=(math.radians(-30),math.radians(16*sgn),0))

# ===== 首・頭（悪魔面・湾曲した大角・発光する眼と口）=====
cyl(BODY,"Neck",(0,-0.02,2.74),0.13,0.16,M_SKIN2)
sphere(BODY,"Head",(0,0.0,2.96),(0.22,0.24,0.24),M_SKIN)
cube(BODY,"Brow",(0,0.18,3.04),(0.23,0.07,0.07),M_SKIN2,rot=(math.radians(-16),0,0))   # 張り出した眉
cube(BODY,"Snout",(0,0.20,2.88),(0.15,0.16,0.10),M_SKIN)
cube(BODY,"Jaw",(0,0.16,2.80),(0.15,0.16,0.06),M_SKIN2)
cube(BODY,"MawGlow",(0,0.20,2.84),(0.11,0.10,0.035),M_MAGMA)    # 口内の溶岩光
for sgn in (1,-1):   # 牙
    cone(BODY,"Fang%d"%sgn,(0.07*sgn,0.24,2.83),0.022,0.10,M_HORNT,verts=4,rot=(math.radians(160),0,0))
# 発光する眼（吊り上がり）＋眼窩の影
for sgn in (1,-1):
    sphere(BODY,"Socket%d"%sgn,(0.10*sgn,0.16,2.99),(0.07,0.05,0.06),M_SKIN2,segs=10,rings=8)
    sphere(BODY,"Eye%d"%sgn,(0.10*sgn,0.205,3.00),(0.050,0.038,0.046),M_MAGMA,segs=10,rings=8)
# 湾曲した大角（円柱ベースで太さ維持＝先細りで消えない。根→後方へ反り→太い先端カール）＋眉の副角
for sgn in (1,-1):
    cyl(BODY,"HornA%d"%sgn,(0.17*sgn,0.06,3.20),0.135,0.36,M_HORNT,verts=10,rot=(math.radians(24),0,math.radians(22*sgn)))  # 根：極太・上外へ
    cyl(BODY,"HornB%d"%sgn,(0.31*sgn,-0.04,3.50),0.110,0.34,M_HORNT,verts=10,rot=(math.radians(54),0,math.radians(26*sgn))) # 中：後ろへ反り
    cone(BODY,"HornC%d"%sgn,(0.42*sgn,-0.25,3.54),0.105,0.34,M_HORN,verts=10,rot=(math.radians(98),0,math.radians(16*sgn))) # 先：太い先端カール
    cone(BODY,"HornMini%d"%sgn,(0.085*sgn,0.18,3.10),0.05,0.18,M_HORN,verts=6,rot=(math.radians(18),0,math.radians(8*sgn))) # 眉の副角

# ===== 蝙蝠翼（Body・背から半開きに広げる威圧シルエット）=====
def wing_body(sgn):
    bx=0.30*sgn
    # 前縁の骨（背→外へ広く・控えめな上昇＝頭上に細く突き出さない）
    cube(BODY,"WUp%d"%sgn,(bx+0.28*sgn,0.18,2.66),(0.30,0.08,0.08),M_WING,rot=(0,math.radians(-46*sgn),0))
    cube(BODY,"WFr%d"%sgn,(bx+0.78*sgn,0.20,2.92),(0.34,0.07,0.07),M_WING,rot=(0,math.radians(-62*sgn),0))
    cube(BODY,"WSp%d"%sgn,(bx+1.24*sgn,0.22,3.06),(0.32,0.05,0.05),M_WING,rot=(0,math.radians(-72*sgn),0))
    cone(BODY,"WClaw%d"%sgn,(bx+1.58*sgn,0.22,3.24),0.055,0.22,M_CLAW,verts=4,rot=(math.radians(90),0,math.radians(-78*sgn)))
    # 指骨（膜を支える・後縁へ垂れる）
    for i,(tx,tz) in enumerate([(0.62,2.66),(0.98,2.34),(1.24,2.04)]):
        cube(BODY,"WFg%d_%d"%(sgn,i),(bx+tx*sgn,0.40,tz),(0.05,0.05,0.50),M_WING,rot=(math.radians(20),0,math.radians(-26*sgn)))
    # 翼膜（縦のセイル3枚・黒赤・前縁の下を広く覆う）
    memb=[(0.52,2.70,0.58,0.62),(0.96,2.40,0.52,0.56),(1.26,2.10,0.42,0.46)]
    for i,(mx,mz,hx,hz) in enumerate(memb):
        cube(BODY,"WMb%d_%d"%(sgn,i),(bx+mx*sgn,0.42,mz),(hx,0.012,hz),M_MEMB if i<2 else M_MEMB2,
             rot=(math.radians(8),math.radians(-54*sgn),0))
wing_body(1); wing_body(-1)

# ===== 尾（-Yへ伸び下降→先端の溶岩スペード）=====
for i,(y,z,s) in enumerate([(-0.42,1.82,0.16),(-0.70,1.58,0.13),(-0.92,1.36,0.10),(-1.08,1.20,0.08)]):
    cube(BODY,"Tail%d"%i,(0,y,z),(s,s+0.06,s),M_SKIN2)
cone(BODY,"TailSpade",(0,-1.20,1.12),0.10,0.30,M_HORN,verts=4,rot=(math.radians(120),0,0))
cube(BODY,"TailGlow",(0,-1.14,1.16),(0.03,0.10,0.03),M_MAGMA2,rot=(math.radians(30),0,0))

# ===== 腕（肩 z=2.70）筋肉質・鉤爪 =====
def arm(g,sgn):
    x=0.46*sgn
    cyl(g,"Upper",(x,-0.02,2.36),0.13,0.52,M_SKIN,rot=(0,math.radians(6*sgn),0))
    sphere(g,"Elbow",(x,0,2.06),(0.12,0.12,0.12),M_SKIN2)
    cyl(g,"Fore",(x,0.03,1.74),0.115,0.50,M_SKIN,rot=(0,math.radians(8*sgn),0))
    cube(g,"ForeSpike",(x,-0.10,1.78),(0.04,0.05,0.22),M_HORN,rot=(math.radians(20),0,0))  # 前腕の棘
    cube(g,"CrackFore%d"%sgn,(x,0.12,1.74),(0.02,0.02,0.22),M_MAGMA)
    sphere(g,"Hand",(x,0.04,1.44),(0.13,0.11,0.13),M_SKIN2)
    # 4本の鉤爪（前向き）
    for i,fx in enumerate((-0.09,-0.03,0.03,0.09)):
        cone(g,"Claw%d_%d"%(sgn,i),(x+fx,0.18,1.40),0.028,0.20,M_CLAW,verts=4,rot=(math.radians(72),0,0))
arm(ARML,1); arm(ARMR,-1)

# ===== 脚（股 z=1.66）逆関節・割れ蹄 =====
def leg(g,sgn):
    x=0.20*sgn
    cyl(g,"Thigh",(x,0.04,1.28),0.16,0.54,M_SKIN,rot=(math.radians(14),0,0))     # 太腿（前へ）
    sphere(g,"Knee",(x,0.16,1.00),(0.12,0.12,0.12),M_SKIN2)
    cyl(g,"Shank",(x,0.02,0.66),0.12,0.60,M_SKIN,rot=(math.radians(-26),0,0))    # 脛（後ろへ＝逆関節）
    sphere(g,"Hock",(x,-0.10,0.36),(0.10,0.10,0.10),M_SKIN2)
    cyl(g,"Pastern",(x,0.0,0.22),0.08,0.30,M_SKIN2,rot=(math.radians(30),0,0))   # 蹄上
    cube(g,"CrackLeg%d"%sgn,(x,0.16,1.06),(0.02,0.02,0.20),M_MAGMA2)
    # 割れ蹄（2つに分かれた前向きの蹄）
    for i,fx in enumerate((-0.05,0.05)):
        cube(g,"Hoof%d_%d"%(sgn,i),(x+fx,0.12,0.06),(0.05,0.12,0.10),M_HOOF)
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
set_origin(armL,(0.46,0,2.70)); set_origin(armR,(-0.46,0,2.70))
set_origin(legL,(0.20,0,1.66)); set_origin(legR,(-0.20,0,1.66))
# 筋肉の丸み：subsurf1+decimate（軽量）
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
BZ=body.location.z

# idle: 重い呼吸＋腕の微動
new_action(body,"body_idle")
for f,z in [(1,BZ),(40,BZ+0.04),(80,BZ)]: kz(body,f,z)
push(body,"idle")
for a,sgn in [(armL,1),(armR,-1)]:
    new_action(a,a.name+"_idle")
    for f,d in [(1,0),(40,5*sgn),(80,0)]: krx(a,f,d)
    push(a,"idle")
# walk: 脚交互＋胴上下＋腕振り
new_action(body,"body_walk")
for f,z in [(1,BZ),(10,BZ+0.05),(20,BZ),(30,BZ+0.05),(40,BZ)]: kz(body,f,z)
push(body,"walk")
for lg,sgn in [(legL,1),(legR,-1)]:
    new_action(lg,lg.name+"_walk")
    for f,d in [(1,0),(10,sgn*22),(20,0),(30,-sgn*22),(40,0)]: krx(lg,f,d)
    push(lg,"walk")
for a,sgn in [(armL,1),(armR,-1)]:
    new_action(a,a.name+"_walk")
    for f,d in [(1,0),(10,sgn*12),(20,0),(30,-sgn*12),(40,0)]: krx(a,f,d)
    push(a,"walk")
# attack: 右の鉤爪の薙ぎ（前へ振り下ろし→戻し）＋体の捻り
new_action(armR,"armR_attack")
for f,d in [(1,0),(5,-55),(11,30),(18,0)]: krx(armR,f,d)
push(armR,"attack")
new_action(body,"body_attack")
for f,d in [(1,0),(5,7),(11,-5),(18,0)]: krz(body,f,d)
push(body,"attack")
# heavy: 両腕の振り上げ→叩き付け＋体の沈み込み
for a in (armL,armR):
    new_action(a,a.name+"_heavy")
    for f,d in [(1,0),(10,-100),(18,40),(26,0)]: krx(a,f,d)
    push(a,"heavy")
new_action(body,"body_heavy")
for f,z in [(1,BZ),(10,BZ+0.06),(18,BZ-0.05),(26,BZ)]: kz(body,f,z)
push(body,"heavy")
scene.frame_set(1)

repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."));models=os.path.join(repo,"models");os.makedirs(models,exist_ok=True)
out=os.path.join(models,"mob_demon.glb")
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_yup=True,
    export_apply=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_optimize_animation_size=True)
zs=[(o.matrix_world@V(v)).z for o in (body,armL,armR,legL,legR) for v in o.bound_box]
xs=[(o.matrix_world@V(v)).x for o in (body,) for v in o.bound_box]
sz=os.path.getsize(out)
print("[voxel] demon export -> %.3fMB  H%.2fm  clips: idle/walk/attack/heavy"%(sz/1048576, max(zs)))

# ---- プレビュー描画（暗背景・マグマ発光が映える / 失敗してもexport完了済み）----
try:
    if "--render" in sys.argv:
        scene.frame_set(1)
        try: scene.render.engine='BLENDER_EEVEE_NEXT'
        except Exception: scene.render.engine='BLENDER_EEVEE'
        scene.render.resolution_x=780; scene.render.resolution_y=940
        world=bpy.data.worlds.new("W"); scene.world=world; world.use_nodes=True
        world.node_tree.nodes["Background"].inputs[0].default_value=(0.04,0.03,0.035,1)
        world.node_tree.nodes["Background"].inputs[1].default_value=1.0
        bpy.ops.object.light_add(type='SUN',location=(3,-5,6)); sun=bpy.context.active_object
        sun.data.energy=5.0; sun.rotation_euler=(math.radians(54),0,math.radians(34))
        bpy.ops.object.light_add(type='AREA',location=(-3.5,-3,2.0)); fill=bpy.context.active_object
        fill.data.energy=420; fill.data.color=(1.0,0.35,0.12); fill.data.size=5.0   # 下からの溶岩光
        bpy.ops.object.light_add(type='AREA',location=(-2.5,5,4.5)); rim=bpy.context.active_object
        rim.data.energy=400; rim.data.color=(0.6,0.7,1.0); rim.data.size=4.0        # 背後のリム（黒シルエットを縁取り）
        def shot(name,cam_loc,cam_rot):
            bpy.ops.object.camera_add(location=cam_loc,rotation=cam_rot)
            cam=bpy.context.active_object; scene.camera=cam; cam.data.lens=42
            scene.render.filepath=os.path.join(repo,"tools",name)
            bpy.ops.render.render(write_still=True)
            bpy.data.objects.remove(cam,do_unlink=True)
        shot("hero_mob_demon_front.png",(0,6.6,2.2),(math.radians(85),0,math.radians(180)))
        shot("hero_mob_demon_3q.png",(4.6,4.6,2.7),(math.radians(80),0,math.radians(135)))
        print("[voxel] demon preview rendered")
except Exception as e:
    print("[voxel] preview render skipped:", e)
