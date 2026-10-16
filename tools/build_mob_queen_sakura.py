# -*- coding: utf-8 -*-
# VOXEL WORLD - 最終ボス：巨大チンチラの女王さくら（mob_queen_sakura）【方向確認フェーズ】
# blender --background --python tools/build_mob_queen_sakura.py [-- --render]
#   出力: models/mob_queen_sakura.glb （Y-up/足元z=0/正面+Y(→ゲーム-Z)/高さ約7m/2MB以下）
#   アニメ: idle / walk(ぴょんぴょん) / attack(前足で叩く) / heavy(体を反って前方へ放つ大技)
#   骨格契約(dragon/golem準拠・不変): Body / ArmL(左前足) / ArmR(右前足) / LegL / LegR(後足)
# 方針(司令塔): 全ボス最大(6〜8m)。ふわふわ灰色の毛・大きな丸い耳・まんまる赤(ピンク発光)の目・
#   小さな手足・ふさふさ尻尾。女王の風格＝小さな金の王冠(発光)＋首元のミニマント＋威厳ある表情。
#   ★最重要: 「可愛くて強そう」。ボスだが愛嬌がある。
# 発光: 王冠=金色 / 目=ピンク。

import bpy, os, math, mathutils, random
V=mathutils.Vector
scene=bpy.context.scene; scene.render.fps=24
random.seed(3)
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
FUR  =mat("Fur",(0.72,0.73,0.78))                 # ふわふわ灰色（明るめ＝可愛い）
FUR2 =mat("Fur2",(0.60,0.61,0.67))                # 毛の陰
FUR3 =mat("Fur3",(0.82,0.83,0.87))               # ハイライト毛
BELLY=mat("Belly",(0.94,0.95,0.97),0.9)          # 腹・口元・内耳の白
EARIN=mat("EarIn",(0.98,0.80,0.84),0.85)         # 内耳のピンク
NOSE =mat("Nose",(0.98,0.62,0.70),0.7)           # 鼻ピンク
EYE  =mat("Eye",(1.0,0.30,0.44),0.2,emis=(1.0,0.34,0.48),es=4.0)   # まんまる目：赤〜ピンク発光
EYEHI=mat("EyeHi",(1.0,0.97,0.99),0.1,emis=(1.0,0.97,0.99),es=4.0) # 目のハイライト
PAW  =mat("Paw",(0.40,0.41,0.46),0.8)            # 手足の肉球側
WHISK=mat("Whisk",(0.93,0.93,0.95),0.5)          # ひげ
GOLD =mat("Gold",(0.95,0.78,0.25),0.3,me=0.9,emis=(1.0,0.80,0.28),es=3.2)  # 王冠：金の発光
GEMR =mat("CrownGem",(0.95,0.18,0.30),0.2,emis=(1.0,0.22,0.34),es=3.0)
MANT =mat("Mantle",(0.62,0.10,0.16),0.8)         # ミニマント（深紅）
MANT2=mat("Mantle2",(0.50,0.08,0.13),0.82)
ERMINE=mat("Ermine",(0.95,0.95,0.96),0.85)       # マントの白い縁（アーミン）

def cube(g,n,loc,s,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.rotation_euler=rot;o.data.materials.append(m);g.append(o);return o
def sphere(g,n,loc,s,m,segs=14,rings=9):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs,ring_count=rings,location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.data.materials.append(m);g.append(o);return o
def ico(g,n,loc,s,m,subd=2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subd,location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.data.materials.append(m);g.append(o);return o
def cone(g,n,loc,r,d,m,verts=8,rot=(0,0,0),r2=0.0):
    bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r,radius2=r2,depth=d,location=loc)
    o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);g.append(o);return o

BODY=[];ARML=[];ARMR=[];LEGL=[];LEGR=[]
# 正面=+Y（顔側）。座り気味のぽっちゃり体型で「ぷにっと可愛い」。全高 約7m。

# ===== 毛玉ヘルパー：本体の輪郭に沿ってふわふわの起伏を足す =====
def fuzz(g, center, rad, n, sscale, mats):
    # 豪奢な毛皮：滑らかな小粒タフト(subd=2)を密に重ねて“ふわふわ”に（岩塊感を排除）
    cx,cy,cz=center
    for i in range(n):
        a=random.uniform(0,2*math.pi); b=random.uniform(-0.5,1.0)
        rr=rad*random.uniform(0.90,1.05)
        x=cx+math.cos(a)*rr*0.92; y=cy+math.sin(a)*rr*0.55*math.cos(b); z=cz+math.sin(b)*rr
        s=sscale*random.uniform(0.62,1.0)
        ico(g,"Fuzz",(x,y,z),(s,s*0.9,s*1.05),random.choice(mats),subd=2)

# ===== 胴（ぽっちゃり洋ナシ型）z≈1.2〜4.2 =====
sphere(BODY,"Belly",(0,0.18,2.4),(1.85,1.70,1.95),FUR,segs=20,rings=14)     # 下半身（大きい）
sphere(BODY,"BellyW",(0,0.78,2.2),(1.30,1.05,1.30),BELLY,segs=18,rings=12)  # 白い腹
sphere(BODY,"Chest",(0,0.30,3.7),(1.45,1.35,1.45),FUR,segs=20,rings=14)     # 上半身
sphere(BODY,"ChestW",(0,0.85,3.55),(0.92,0.80,0.95),BELLY,segs=16,rings=11) # 白い胸
fuzz(BODY,(0,0.0,2.6),2.0,46,0.24,[FUR,FUR2,FUR3])                          # 体のもふもふ起伏（密・小粒）
fuzz(BODY,(0,0.0,3.7),1.5,30,0.22,[FUR,FUR3])

# ===== 頭（大きい・丸い＝マスコット比率で顔を主役に）z≈3.6〜6.2 =====
sphere(BODY,"Head",(0,0.45,5.1),(1.75,1.62,1.62),FUR,segs=24,rings=16)
# 白い口元（マズル）：目より下＆控えめ＝目を隠さない
sphere(BODY,"Muzzle",(0,1.55,4.55),(0.86,0.58,0.62),BELLY,segs=18,rings=12)
sphere(BODY,"Cheek1",(0.92,1.30,4.62),(0.50,0.48,0.48),FUR3,segs=12,rings=8) # ぷくぷく頬
sphere(BODY,"Cheek2",(-0.92,1.30,4.62),(0.50,0.48,0.48),FUR3,segs=12,rings=8)
fuzz(BODY,(0,-0.2,5.2),1.70,34,0.24,[FUR,FUR3,FUR2])                        # 頭のもふ(後ろ寄り・密)
fuzz(BODY,(0,0.30,5.0),1.62,16,0.20,[FUR3,FUR])                             # 頬まわりの柔毛

# 大きな丸い耳（チンチラ＝丸耳）左右・高め。内耳ピンク。
for sgn in (1,-1):
    ico(BODY,"Ear%d"%sgn,(1.22*sgn,0.10,6.45),(0.82,0.40,0.88),FUR,subd=2)
    ico(BODY,"EarIn%d"%sgn,(1.22*sgn,0.30,6.45),(0.56,0.24,0.62),EARIN,subd=2)
    fuzz(BODY,(1.22*sgn,0.0,6.55),0.78,7,0.18,[FUR3,FUR])

# まんまるの目（ピンク発光・大粒＝可愛い）：顔の前面に出す（マズルより前）
for sgn in (1,-1):
    sphere(BODY,"Eye%d"%sgn,(0.64*sgn,1.66,5.25),(0.44,0.42,0.48),EYE,segs=18,rings=12)
    sphere(BODY,"EyeHi%d"%sgn,(0.76*sgn,1.92,5.46),(0.13,0.11,0.14),EYEHI,segs=10,rings=7)
    sphere(BODY,"EyeHi2%d"%sgn,(0.54*sgn,1.88,5.10),(0.07,0.07,0.08),EYEHI,segs=8,rings=6)
    cube(BODY,"Lash%d"%sgn,(0.64*sgn,1.78,5.62),(0.42,0.07,0.05),FUR2,rot=(math.radians(20),0,0))  # まつ毛
# 鼻＆口（小さく可愛い・マズル前面）＋ひげ
sphere(BODY,"Nose",(0,2.02,4.78),(0.20,0.15,0.15),NOSE,segs=12,rings=8)
cube(BODY,"Mouth",(0,1.98,4.58),(0.12,0.05,0.06),NOSE)
for sgn in (1,-1):
    for k,zz in enumerate((4.80,4.70,4.60)):
        cube(BODY,"Whisk%d_%d"%(sgn,k),(0.70*sgn,1.80,zz),(0.66,0.014,0.014),WHISK,rot=(0,0,math.radians(-12*sgn+(k-1)*6)))
# 出っ歯（げっ歯類の前歯・愛嬌）
cube(BODY,"Tooth",(0,2.00,4.46),(0.12,0.06,0.09),BELLY)

# ===== 王冠（小さめ・金の発光・頭頂やや前）＝女王の証 =====
cz=6.6; cy0=0.38
import math as _m
bpy.ops.mesh.primitive_cylinder_add(vertices=22,radius=0.74,depth=0.32,location=(0,cy0,cz))
o=bpy.context.active_object;o.name="CrownBand";o.data.materials.append(GOLD);BODY.append(o)
for i in range(10):                                  # 王冠の山（尖り）＋宝石（大きく荘厳に）
    a=2*_m.pi*i/10; x=0.74*_m.cos(a); y=cy0+0.74*_m.sin(a)
    cone(BODY,"CrSpire%d"%i,(x,y,cz+0.36),0.11,0.36,GOLD,verts=6)
    ico(BODY,"CrGem%d"%i,(x,y,cz+0.18),(0.07,0.07,0.08),GEMR,subd=1)
ico(BODY,"CrownTop",(0,cy0,cz+0.62),(0.16,0.16,0.18),GOLD,subd=1)        # 頂飾り
ico(BODY,"CrownTopGem",(0,cy0,cz+0.80),(0.10,0.10,0.11),GEMR,subd=1)

# ===== 首元のミニマント（深紅＋白縁・肩を覆う）=====
for sgn in (1,-1):
    cube(BODY,"Mantle%d"%sgn,(0.95*sgn,-0.55,4.05),(0.55,0.30,0.75),MANT if sgn>0 else MANT2,rot=(math.radians(8),0,math.radians(-12*sgn)))
cube(BODY,"MantleBack",(0,-1.05,4.0),(1.15,0.22,0.85),MANT2)
# 白いアーミンの縁（肩まわり）
for sgn in (1,-1):
    sphere(BODY,"Erm%d"%sgn,(0.7*sgn,0.55,4.5),(0.42,0.34,0.30),ERMINE,segs=12,rings=8)
sphere(BODY,"ErmF",(0,0.95,4.45),(0.55,0.34,0.30),ERMINE,segs=14,rings=9)
cube(BODY,"Clasp",(0,1.10,4.5),(0.12,0.10,0.12),GOLD)                     # 金の留め具

# ===== ふさふさ尻尾（背面-Y・立ち上がる）=====
tail=[(0,-1.7,2.2,0.55),(0,-2.2,2.9,0.60),(0,-2.4,3.7,0.62),(0,-2.2,4.4,0.55),(0,-1.7,4.9,0.42)]
for i,(x,y,z,r) in enumerate(tail):
    sphere(BODY,"Tail%d"%i,(x,y,z),(r,r,r*1.1),FUR if i%2==0 else FUR2,segs=12,rings=8)
    fuzz(BODY,(x,y,z),r*1.1,5,0.22,[FUR,FUR3,FUR2])

# ===== 前足（ArmL/ArmR）小さくぷにっと。pivot=肩 z=3.7 =====
def arm(g,sgn):
    x=1.25*sgn
    sphere(g,"Shoulder",(x,0.35,3.55),(0.5,0.5,0.55),FUR,segs=12,rings=8)
    sphere(g,"UpperArm",(x+0.1*sgn,0.55,3.0),(0.34,0.34,0.42),FUR2,segs=12,rings=8)
    sphere(g,"Paw",(x+0.12*sgn,0.85,2.55),(0.32,0.34,0.30),FUR,segs=12,rings=8)
    sphere(g,"PawPad",(x+0.12*sgn,1.05,2.45),(0.22,0.16,0.20),PAW,segs=10,rings=7)
    for k,fx in enumerate((-0.12,0.0,0.12)):                     # 小さな指
        sphere(g,"Finger%d"%k,(x+0.12*sgn+fx,1.18,2.45),(0.07,0.09,0.07),BELLY,segs=8,rings=6)
    fuzz(g,(x,0.5,3.2),0.5,8,0.2,[FUR,FUR3])
arm(ARML,1); arm(ARMR,-1)

# ===== 後足（LegL/LegR）座り姿勢で前に投げ出す。pivot=股 z=1.5 =====
def leg(g,sgn):
    x=1.05*sgn
    sphere(g,"Thigh",(x,0.5,1.5),(0.62,0.7,0.6),FUR,segs=14,rings=9)
    sphere(g,"Foot",(x,1.3,0.5),(0.34,0.55,0.34),FUR2,segs=12,rings=8)      # 前へ投げ出した足
    sphere(g,"Sole",(x,1.5,0.32),(0.28,0.40,0.16),PAW,segs=10,rings=7)
    for k,fx in enumerate((-0.14,0.0,0.14)):
        sphere(g,"Toe%d"%k,(x+fx,1.75,0.34),(0.08,0.10,0.08),BELLY,segs=8,rings=6)
    fuzz(g,(x,0.6,1.4),0.6,7,0.2,[FUR,FUR3])
leg(LEGL,1); leg(LEGR,-1)

# ===== 結合・原点・軽量化 =====
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
set_origin(armL,(1.25,0.35,3.55));  set_origin(armR,(-1.25,0.35,3.55))
set_origin(legL,(1.05,0.5,1.5));    set_origin(legR,(-1.05,0.5,1.5))
for o in (body,armL,armR,legL,legR):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    d=o.modifiers.new("D",'DECIMATE');d.decimate_type='COLLAPSE';d.ratio=0.42   # もふもふ多数→軽量化
    bpy.ops.object.modifier_apply(modifier=d.name)
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
def ky(o,f,y):o.location.y=y;o.keyframe_insert('location',index=1,frame=f)
def krx(o,f,d):o.rotation_euler[0]=math.radians(d);o.keyframe_insert('rotation_euler',index=0,frame=f)
def krz(o,f,d):o.rotation_euler[2]=math.radians(d);o.keyframe_insert('rotation_euler',index=2,frame=f)
def ksc(o,f,s):o.scale=(s,s,s);o.keyframe_insert('scale',frame=f)
BZ=body.location.z

# idle: もふもふ揺れ（体の上下＋わずかに膨らむ呼吸）＋耳ピクピク（前足/後足は微動）
new_action(body,"body_idle")
for f,z in [(1,BZ),(45,BZ+0.10),(90,BZ)]: kz(body,f,z)
push(body,"idle")
for a,sgn in [(armL,1),(armR,-1)]:
    new_action(a,a.name+"_idle")
    for f,d in [(1,0),(30,-6),(60,4),(90,0)]: krx(a,f,d)
    push(a,"idle")
for lg,sgn in [(legL,1),(legR,-1)]:                 # 後足はほぼ静止（座り）。わずかに
    new_action(lg,lg.name+"_idle")
    for f,d in [(1,0),(45,sgn*3),(90,0)]: krz(lg,f,d)
    push(lg,"idle")

# walk: ぴょんぴょん跳ねる（体を大きく上下＋着地で潰れ＋前傾）＋手足を畳む
new_action(body,"body_walk")
for f,z in [(1,BZ),(8,BZ+0.6),(15,BZ+0.05),(20,BZ),(28,BZ+0.6),(35,BZ+0.05),(40,BZ)]: kz(body,f,z)
for f,d in [(1,0),(8,-8),(15,4),(20,0),(28,-8),(35,4),(40,0)]: krx(body,f,d)
push(body,"walk")
for a,sgn in [(armL,1),(armR,-1)]:
    new_action(a,a.name+"_walk")
    for f,d in [(1,0),(8,-26),(20,0),(28,-26),(40,0)]: krx(a,f,d)   # 跳躍中は前足を畳む
    push(a,"walk")
for lg,sgn in [(legL,1),(legR,-1)]:
    new_action(lg,lg.name+"_walk")
    for f,d in [(1,0),(8,40),(15,-10),(20,0),(28,40),(35,-10),(40,0)]: krx(lg,f,d)  # 蹴り出し
    push(lg,"walk")

# attack: 前足で叩く（両前足を振り上げ→振り下ろし）＋体を軽く前傾
new_action(body,"body_attack")
for f,d in [(1,0),(7,-10),(13,3),(22,0)]: krx(body,f,d)
push(body,"attack")
for a,sgn in [(armL,1),(armR,-1)]:
    new_action(a,a.name+"_attack")
    for f,d in [(1,0),(5,-58),(11,30),(16,18),(22,0)]: krx(a,f,d)   # 振り上げ→叩き下ろし
    push(a,"attack")

# heavy: おしっこ攻撃＝体を大きく反らし前方へ放つポーズ（後足で踏ん張り→反り→前へ突き出す）
#   品よく「反って→前傾でリリース→戻し」。前足は万歳、尻尾は持ち上がる想定の体反り。
new_action(body,"body_heavy")
for f,d in [(1,0),(12,26),(20,24),(30,-30),(40,-6),(52,0)]: krx(body,f,d)  # 後ろへ反る→前へ放つ
for f,z in [(1,BZ),(12,BZ+0.25),(30,BZ-0.15),(52,BZ)]: kz(body,f,z)
push(body,"heavy")
for a,sgn in [(armL,1),(armR,-1)]:
    new_action(a,a.name+"_heavy")
    for f,d in [(1,0),(12,-70),(30,-40),(52,0)]: krx(a,f,d)         # 万歳→
    push(a,"heavy")
for lg,sgn in [(legL,1),(legR,-1)]:
    new_action(lg,lg.name+"_heavy")
    for f,d in [(1,0),(12,-18),(30,10),(52,0)]: krx(lg,f,d)         # 踏ん張り
    push(lg,"heavy")
scene.frame_set(1)

repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."));models=os.path.join(repo,"models");os.makedirs(models,exist_ok=True)
out=os.path.join(models,"mob_queen_sakura.glb")
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_yup=True,
    export_apply=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_optimize_animation_size=True)
zs=[(o.matrix_world@V(v)).z for o in (body,armL,armR,legL,legR) for v in o.bound_box]
xs=[(o.matrix_world@V(v)).x for o in (body,armL,armR,legL,legR) for v in o.bound_box]
print("[voxel] queen_sakura export -> %.3fMB  H%.2fm  W%.2fm  clips: idle/walk/attack/heavy"
      %(os.path.getsize(out)/1048576, max(zs), max(xs)-min(xs)))

# ---- プレビュー（-- --render 時のみ・可愛さが映える明るめ背景）----
try:
    import sys
    if "--render" in sys.argv:
        scene.frame_set(1)
        try: scene.render.engine='BLENDER_EEVEE_NEXT'
        except Exception: scene.render.engine='BLENDER_EEVEE'
        scene.render.resolution_x=820; scene.render.resolution_y=1000
        world=bpy.data.worlds.new("W"); scene.world=world; world.use_nodes=True
        world.node_tree.nodes["Background"].inputs[0].default_value=(0.20,0.19,0.25,1)   # 適正露出の舞台
        world.node_tree.nodes["Background"].inputs[1].default_value=0.9
        bpy.ops.object.light_add(type='SUN',location=(3,-5,8)); sun=bpy.context.active_object
        sun.data.energy=4.0; sun.rotation_euler=(math.radians(52),0,math.radians(28))
        bpy.ops.object.light_add(type='AREA',location=(-3.5,-3,6)); fill=bpy.context.active_object
        fill.data.energy=320; fill.data.color=(1.0,0.78,0.88); fill.data.size=7.0
        def shot(name,cam_loc,look):
            bpy.ops.object.camera_add(location=cam_loc)
            cam=bpy.context.active_object; scene.camera=cam; cam.data.lens=50
            e=bpy.data.objects.new("E",None); scene.collection.objects.link(e); e.location=look
            cam.constraints.new('TRACK_TO').target=e
            scene.render.filepath=os.path.join(repo,"tools",name)
            bpy.ops.render.render(write_still=True)
            bpy.data.objects.remove(cam,do_unlink=True); bpy.data.objects.remove(e,do_unlink=True)
        # 顔を主役に：やや上半身寄りを狙う
        shot("hero_mob_queen_sakura_front.png",(0,11.0,4.6),(0,0,4.4))
        shot("hero_mob_queen_sakura_3q.png",  (7.5,7.5,5.0),(0,0,4.2))
        print("[voxel] queen_sakura preview rendered")
except Exception as e:
    print("[voxel] preview render skipped:", e)
