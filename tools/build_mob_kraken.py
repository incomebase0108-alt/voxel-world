# -*- coding: utf-8 -*-
# VOXEL WORLD - 海のボス：クラーケン（巨大頭足類）【海ボス第1弾・方向確認フェーズ】
# blender --background --python tools/build_mob_kraken.py [-- --render]
#   出力: models/mob_kraken.glb （Y-up/足元z=0/正面+Y(→ゲームで-Z)/高さ約6m/2MB以下）
#   アニメ: idle / walk(=泳ぎ/移動) / attack(=触手の叩きつけ) / heavy(=触手で絡めとる大技)
#   骨格契約(dragon/golem準拠・不変): Body / ArmL / ArmR / LegL / LegR
#     ArmL/ArmR = 海面へ突き出る前方の大触手2本（叩きつけ担当）
#     LegL/LegR = 後方／側面の大触手2本（遊泳の推進・うねり）
#     Body      = 大頭部(マントル)＋眼(発光)＋嘴＋waterlineに垂れる短触手6本（計10本相当の威圧）
# 方針(司令塔): 黒紫〜深海色の巨大タコ/イカ。海面から触手が突き出る威圧感。
#   発光=眼・吸盤の先端(深海の生物発光・シアン)。角張った肌(bevel+flat)で軽量。

import bpy, os, math, mathutils
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
M_SKIN =mat("Skin",(0.21,0.09,0.31))              # マントル主色：黒紫
M_SKIN2=mat("Skin2",(0.13,0.06,0.20))             # 暗部
M_BELLY=mat("Belly",(0.31,0.22,0.36),0.85)        # 腹/明るい面
M_TENT =mat("Tent",(0.25,0.10,0.33))              # 触手 表
M_TENT2=mat("Tent2",(0.16,0.07,0.23))             # 触手 裏/影
M_SUC  =mat("Sucker",(0.80,0.71,0.67),0.8)        # 吸盤(淡)
M_BEAK =mat("Beak",(0.06,0.05,0.08),0.5)          # 嘴(ほぼ黒)
M_EYE  =mat("Eye",(0.6,0.96,1.0),0.2,emis=(0.55,0.95,1.0),es=7.5)   # 眼：シアンの生物発光(主役)
M_GLOW =mat("Glow",(0.35,0.92,0.88),0.3,emis=(0.30,0.90,0.85),es=4.5) # 吸盤の先端/嘴の灯り(深海テール)

def cube(g,n,loc,s,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.rotation_euler=rot;o.data.materials.append(m);g.append(o);return o
def sphere(g,n,loc,s,m,segs=10,rings=7):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs,ring_count=rings,location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.data.materials.append(m);g.append(o);return o
def cone(g,n,loc,r,d,m,verts=6,rot=(0,0,0),r2=0.0):
    bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r,radius2=r2,depth=d,location=loc)
    o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);g.append(o);return o

BODY=[];ARML=[];ARMR=[];LEGL=[];LEGR=[]

# === 触手ジェネレータ：base から outdir 方向へ伸び up で反り curl で先端が巻く ===
#   球の連なり(低ポリ・flat)＝深海生物の節。下面に吸盤、先端側に発光吸盤＋光る先端。
def tentacle(group, name, base, outdir, up, length, segs, r0,
             curl=1.0, droop=0.0, sucker_every=2, mt=M_TENT, mt2=M_TENT2):
    pts=[]
    for i in range(segs):
        t=i/(segs-1)
        horiz=length*(0.70*t+0.18*t*t)
        vert =length*(up*t) - curl*length*max(0.0,t-0.55)**2 - droop*length*(t**2)
        x=base[0]+outdir[0]*horiz
        y=base[1]+outdir[1]*horiz
        z=base[2]+vert
        r=r0*(1.0-0.60*t)+0.06         # 先端を細らせ過ぎず＝節が途切れない
        pts.append((x,y,z,r))
    # 連続した肉として読ませる：隣接球が必ず重なる密度＋接線方向へ少し伸長
    for i,(x,y,z,r) in enumerate(pts):
        o=sphere(group,"%s_s%d"%(name,i),(x,y,z),(r,r,r),mt if i%2==0 else mt2,segs=7,rings=4)
        # 接線方向(次の節へ)に1.35倍伸ばして隙間を橋渡し
        if i<len(pts)-1:
            nx,ny,nz,_=pts[i+1]; d=V((nx-x,ny-y,nz-z))
            if d.length>1e-4:
                o.rotation_mode='QUATERNION'
                o.rotation_quaternion=d.to_track_quat('Z','Y')
                o.scale=(r,r,r*1.35)
    # 吸盤：下面に淡く密着（中ほど少数）＋先端のみ発光
    for i,(x,y,z,r) in enumerate(pts):
        if 0<i<segs-2 and i%sucker_every==0:
            sphere(group,"%s_suc%d"%(name,i),(x,y,z-r*0.58),(r*0.30,r*0.30,r*0.16),M_SUC,segs=6,rings=4)
    x,y,z,r=pts[-1]
    sphere(group,"%s_tip"%name,(x,y,z),(r*1.18,r*1.18,r*1.18),M_GLOW,segs=8,rings=6)  # 光る先端(主発光)
    sphere(group,"%s_sucT"%name,(pts[-2][0],pts[-2][1],pts[-2][2]-pts[-2][3]*0.5),
           (r*0.34,r*0.34,r*0.18),M_GLOW,segs=6,rings=4)                              # 先端寄りの発光吸盤
    return pts

# ===== マントル（大頭部・イカ/タコ複合）：Bodyの主塊 z≈1.5〜3.6 =====
sphere(BODY,"Mantle",(0,0.05,2.55),(0.98,1.10,1.05),M_SKIN,segs=14,rings=9)          # 主ドーム
sphere(BODY,"MantleTop",(0,-0.05,3.15),(0.66,0.78,0.74),M_SKIN2,segs=12,rings=8)     # 後上の盛り
cone (BODY,"MantleTip",(0,-0.22,3.62),0.40,0.7,M_SKIN2,verts=10,rot=(math.radians(-22),0,0)) # イカの尖り
sphere(BODY,"Brow",(0,0.55,2.95),(0.80,0.42,0.34),M_SKIN,segs=12,rings=8)            # 眉庇の張り
sphere(BODY,"Cheek",(0,0.70,2.10),(0.78,0.62,0.52),M_BELLY,segs=12,rings=8)          # 前下の頬/口元の張り
# マントルの鰭（イカのヒレ・左右）
for sgn in (1,-1):
    cone(BODY,"Fin%d"%sgn,(0.92*sgn,-0.10,3.05),0.42,0.9,M_SKIN2,verts=6,
         rot=(math.radians(90),0,math.radians(64*sgn)),r2=0.05)
# マントルの縦皺（質感）
for sgn in (1,-1):
    for j,zz in enumerate((2.85,2.45,2.05)):
        sphere(BODY,"Wr%d_%d"%(sgn,j),(0.60*sgn,0.62-0.06*j,zz),(0.16,0.10,0.22),M_SKIN2,segs=8,rings=6)

# ===== 眼（発光・大きい＝海の王者の威圧）＋瞳 =====
for sgn in (1,-1):
    sphere(BODY,"Eye%d"%sgn,(0.62*sgn,0.86,2.42),(0.26,0.20,0.24),M_EYE,segs=14,rings=10)
    sphere(BODY,"Pupil%d"%sgn,(0.70*sgn,1.02,2.40),(0.10,0.07,0.13),M_BEAK,segs=10,rings=7) # 横長瞳
    sphere(BODY,"Lid%d"%sgn,(0.62*sgn,0.80,2.62),(0.30,0.16,0.12),M_SKIN,segs=10,rings=7)   # 上瞼の庇

# ===== 嘴（口・触手の付け根中央の下）＝発光する喉 =====
sphere(BODY,"Maw",(0,0.30,1.55),(0.34,0.30,0.30),M_BEAK,segs=12,rings=8)
cone (BODY,"BeakU",(0,0.50,1.50),0.16,0.30,M_BEAK,verts=6,rot=(math.radians(110),0,0))
cone (BODY,"BeakL",(0,0.46,1.40),0.14,0.24,M_BEAK,verts=6,rot=(math.radians(70),0,0))
sphere(BODY,"MawGlow",(0,0.36,1.48),(0.16,0.12,0.12),M_GLOW,segs=8,rings=6)
# 触手の付け根の冠（肩）
sphere(BODY,"Crown",(0,0.0,1.55),(0.95,0.95,0.55),M_SKIN,segs=14,rings=8)

# ===== Body内の短触手6本（waterlineに垂れる＝触手の塊感／計10本相当）=====
#   前2・後2はArm/Legの主触手に任せ、こちらは下へ垂れて海面の渦を作る。
body_tents=[
    ("BT_f",  ( 0.20,0.78,1.35), ( 0.20, 0.62), 0.22, 1.7),   # 前
    ("BT_fl", ( 0.62,0.55,1.35), ( 0.55, 0.45), 0.20, 1.7),   # 前左
    ("BT_fr", (-0.62,0.55,1.35), (-0.55, 0.45), 0.20, 1.7),   # 前右
    ("BT_l",  ( 0.80,0.0, 1.40), ( 0.78, 0.05), 0.22, 1.8),   # 真横左
    ("BT_r",  (-0.80,0.0, 1.40), (-0.78, 0.05), 0.22, 1.8),   # 真横右
    ("BT_b",  ( 0.0,-0.65,1.40), ( 0.0,-0.80), 0.22, 1.7),    # 後中央
]
for nm,base,od,r0,ln in body_tents:
    tentacle(BODY,nm,base,od,up=0.18,length=ln,segs=7,r0=r0,curl=0.30,droop=0.95,sucker_every=3)

# ===== ArmL / ArmR：前方の大触手（海面へ反り立つ・叩きつけ担当）=====
#   pivot=付け根 (±0.5,0.45,1.45)。up大で高く反り、先端がわずかに巻く。威圧の rest。
def front_arm(g,sgn):
    tentacle(g,"Arm%d"%sgn,(0.5*sgn,0.45,1.45),(0.34*sgn,0.42),
             up=1.02,length=4.1,segs=12,r0=0.34,curl=0.95,droop=0.0,sucker_every=2)
front_arm(ARML,1); front_arm(ARMR,-1)

# ===== LegL / LegR：後方／側面の大触手（遊泳の推進・うねり）=====
def back_arm(g,sgn):
    tentacle(g,"Leg%d"%sgn,(0.52*sgn,-0.30,1.30),(0.50*sgn,-0.52),
             up=0.55,length=3.4,segs=11,r0=0.30,curl=0.55,droop=0.45,sucker_every=2)
back_arm(LEGL,1); back_arm(LEGR,-1)

# ===== 結合・原点・軽量化（dragon準拠）=====
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
set_origin(armL,(0.5,0.45,1.45));  set_origin(armR,(-0.5,0.45,1.45))
set_origin(legL,(0.52,-0.30,1.30)); set_origin(legR,(-0.52,-0.30,1.30))
for o in (body,armL,armR,legL,legR):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    bv=o.modifiers.new("B",'BEVEL'); bv.width=0.012; bv.segments=1
    bpy.ops.object.modifier_apply(modifier=bv.name)
    bpy.ops.object.shade_flat()
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
def kry(o,f,d):o.rotation_euler[1]=math.radians(d);o.keyframe_insert('rotation_euler',index=1,frame=f)
def krz(o,f,d):o.rotation_euler[2]=math.radians(d);o.keyframe_insert('rotation_euler',index=2,frame=f)
BZ=body.location.z

# idle: 漂う呼吸（体の上下）＋全触手のゆらゆら（前腕=前後うねり/後脚=横うねり）
new_action(body,"body_idle")
for f,z in [(1,BZ),(45,BZ+0.10),(90,BZ)]: kz(body,f,z)
push(body,"idle")
for a,sgn in [(armL,1),(armR,-1)]:
    new_action(a,a.name+"_idle")
    for f,d in [(1,0),(30,7),(60,-5),(90,0)]: krx(a,f,d)     # 前後にゆらり
    push(a,"idle")
for lg,sgn in [(legL,1),(legR,-1)]:
    new_action(lg,lg.name+"_idle")
    for f,d in [(1,0),(45,sgn*10),(90,0)]: krz(lg,f,d)        # 横へうねり
    push(lg,"idle")

# walk(=泳ぎ): 体の前後ピッチ＋上下＋後脚の推進あおり＋前腕は半畳み流し
new_action(body,"body_walk")
for f,z in [(1,BZ),(12,BZ+0.12),(24,BZ),(36,BZ+0.12),(48,BZ)]: kz(body,f,z)
for f,d in [(1,0),(24,-8),(48,0)]: krx(body,f,d)
push(body,"walk")
for lg,sgn in [(legL,1),(legR,-1)]:
    new_action(lg,lg.name+"_walk")
    for f,d in [(1,0),(12,28),(24,0),(36,28),(48,0)]: krx(lg,f,d)   # 後ろへあおって推進
    push(lg,"walk")
for a,sgn in [(armL,1),(armR,-1)]:
    new_action(a,a.name+"_walk")
    for f,d in [(1,0),(24,12),(48,0)]: krx(a,f,d)
    push(a,"walk")

# attack: 前腕2本を前下へ叩きつけ（高速の振り下ろし→戻し）＋体の前傾
new_action(body,"body_attack")
for f,d in [(1,0),(8,-14),(16,3),(24,0)]: krx(body,f,d)
push(body,"attack")
for a,sgn in [(armL,1),(armR,-1)]:
    new_action(a,a.name+"_attack")
    for f,d in [(1,0),(4,18),(10,-72),(16,-58),(24,0)]: krx(a,f,d)  # 振り上げ→叩きつけ→戻し
    push(a,"attack")

# heavy: 前腕を高く掲げ内側へ薙ぐ＝絡めとり大技。体は反って沈み込む。
new_action(body,"body_heavy")
for f,z in [(1,BZ),(10,BZ+0.18),(20,BZ-0.10),(34,BZ)]: kz(body,f,z)
for f,d in [(1,0),(10,10),(20,-6),(34,0)]: krx(body,f,d)
push(body,"heavy")
new_action(armL,"ArmL_heavy")
for f in [1,10,20,34]: pass
for f,d in [(1,0),(10,-28),(20,8),(34,0)]: krx(armL,f,d)     # 掲げる→振り
for f,d in [(1,0),(10,0),(20,-40),(34,0)]: krz(armL,f,d)     # 内側へ薙ぐ
push(armL,"heavy")
new_action(armR,"ArmR_heavy")
for f,d in [(1,0),(10,-28),(20,8),(34,0)]: krx(armR,f,d)
for f,d in [(1,0),(10,0),(20,40),(34,0)]: krz(armR,f,d)
push(armR,"heavy")
for lg,sgn in [(legL,1),(legR,-1)]:
    new_action(lg,lg.name+"_heavy")
    for f,d in [(1,0),(14,sgn*22),(34,0)]: krz(lg,f,d)        # 後脚は踏ん張り横へ
    push(lg,"heavy")
scene.frame_set(1)

repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."));models=os.path.join(repo,"models");os.makedirs(models,exist_ok=True)
out=os.path.join(models,"mob_kraken.glb")
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_yup=True,
    export_apply=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_optimize_animation_size=True)
zs=[(o.matrix_world@V(v)).z for o in (body,armL,armR,legL,legR) for v in o.bound_box]
xs=[(o.matrix_world@V(v)).x for o in (body,armL,armR,legL,legR) for v in o.bound_box]
ys=[(o.matrix_world@V(v)).y for o in (body,armL,armR,legL,legR) for v in o.bound_box]
sz=os.path.getsize(out)
print("[voxel] kraken export -> %.3fMB  H%.2fm  W%.2fm  D%.2fm  clips: idle/walk/attack/heavy"
      %(sz/1048576, max(zs), max(xs)-min(xs), max(ys)-min(ys)))

# ---- プレビュー（-- --render 時のみ・暗い海背景で発光が映える）----
try:
    import sys
    if "--render" in sys.argv:
        scene.frame_set(1)
        try: scene.render.engine='BLENDER_EEVEE_NEXT'
        except Exception: scene.render.engine='BLENDER_EEVEE'
        scene.render.resolution_x=820; scene.render.resolution_y=980
        world=bpy.data.worlds.new("W"); scene.world=world; world.use_nodes=True
        world.node_tree.nodes["Background"].inputs[0].default_value=(0.015,0.03,0.06,1)  # 深海の藍
        world.node_tree.nodes["Background"].inputs[1].default_value=0.9
        bpy.ops.object.light_add(type='SUN',location=(3,-5,7)); sun=bpy.context.active_object
        sun.data.energy=3.6; sun.rotation_euler=(math.radians(54),0,math.radians(30)); sun.data.color=(0.7,0.85,1.0)
        bpy.ops.object.light_add(type='AREA',location=(-3.5,-3,4)); fill=bpy.context.active_object
        fill.data.energy=320; fill.data.color=(0.25,0.7,1.0); fill.data.size=5.0
        def shot(name,cam_loc,cam_rot):
            bpy.ops.object.camera_add(location=cam_loc,rotation=cam_rot)
            cam=bpy.context.active_object; scene.camera=cam; cam.data.lens=40
            scene.render.filepath=os.path.join(repo,"tools",name)
            bpy.ops.render.render(write_still=True)
            bpy.data.objects.remove(cam,do_unlink=True)
        shot("hero_mob_kraken_front.png",(0,9.5,3.2),(math.radians(84),0,math.radians(180)))
        shot("hero_mob_kraken_3q.png",  (6.8,6.8,3.8),(math.radians(80),0,math.radians(135)))
        print("[voxel] kraken preview rendered: tools/hero_mob_kraken_front.png /_3q.png")
except Exception as e:
    print("[voxel] preview render skipped:", e)
