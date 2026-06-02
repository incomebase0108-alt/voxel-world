# -*- coding: utf-8 -*-
# VOXEL WORLD - 敵性ボス：ドラゴン（ワイバーン型）【迫力ボス第1弾】
# blender --background --python tools/build_mob_dragon.py
#   出力: models/mob_dragon.glb （Y-up/足元z=0/正面+Y(→ゲームで-Z)/身長約3.8m/2MB以下）
#   アニメ: idle / walk / attack / heavy（敵性骨格・クリップ名統一・frame1中立rest）
#   骨格契約(golem準拠・不変): Body / ArmL(=左翼) / ArmR(=右翼) / LegL / LegR(=後脚)
# 方針(司令塔): ボス級の威圧感。長い首と牙の頭部・発光する喉と眼(火炎の予兆)・背棘・
#   蝙蝠状の大翼(Arm=翼)・鉤爪の後脚・節のある尾。角張った鱗肌(subsurf無し+bevel/flat)で軽量。
#   ArmL/ArmR を翼に割当て、attack=噛みつき(体の前傾)、heavy=両翼の煽り(ウイングバフェット)。

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
M_SCALE =mat("Scale",(0.50,0.11,0.09))            # 主鱗：深紅（明度確保で黒つぶれ回避）
M_SCALE2=mat("Scale2",(0.34,0.08,0.07))           # 背側：やや暗い
M_BELLY =mat("Belly",(0.62,0.48,0.32),0.85)       # 腹：骨色のうろこ板
M_HORN  =mat("Horn",(0.88,0.82,0.66),0.6)         # 角・牙・棘の骨色
M_MEMB  =mat("Memb",(0.56,0.16,0.13),0.8)         # 翼膜：くすんだ赤
M_MEMB2 =mat("Memb2",(0.42,0.11,0.10),0.85)       # 翼膜の影
M_CLAW  =mat("Claw",(0.10,0.09,0.09),0.5)         # 鉤爪・黒
M_GLOW  =mat("Glow",(1.0,0.5,0.10),0.25,emis=(1.0,0.45,0.08),es=6.5)  # 喉/眼の発光(火の予兆)
M_GLOW2 =mat("Glow2",(1.0,0.65,0.18),0.3,emis=(1.0,0.6,0.15),es=4.0)

def cube(g,n,loc,s,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.rotation_euler=rot;o.data.materials.append(m);g.append(o);return o
def sphere(g,n,loc,s,m,segs=12,rings=8):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs,ring_count=rings,location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.data.materials.append(m);g.append(o);return o
def cone(g,n,loc,r,d,m,verts=4,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r,radius2=0.0,depth=d,location=loc)
    o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);g.append(o);return o

BODY=[];WINGL=[];WINGR=[];LEGL=[];LEGR=[]
# 正面=+Y（頭側）/ 背側=-Y は尾。golem同様 export_yup で glTF Y-up・ゲームで正面-Z。
# 翼ピボット z=2.45（肩根） / 後脚ピボット z=0.98

# ===== 胴（前傾の重心・厚い胸） =====
cube(BODY,"Torso",(0,-0.05,1.78),(0.40,0.52,0.40),M_SCALE)
cube(BODY,"Chest",(0,0.18,1.92),(0.38,0.30,0.36),M_SCALE)
cube(BODY,"Belly",(0,0.10,1.50),(0.34,0.40,0.28),M_BELLY)
# 腹板の横筋（骨色うろこ）
for i,yy in enumerate((-0.10,0.10,0.30)):
    cube(BODY,"BellyRib%d"%i,(0,yy,1.40),(0.30,0.05,0.05),M_BELLY)

# ===== 首（前上方へ伸びる4節）→ 頭 =====
neck_pts=[(0,0.34,2.18,0.20),(0,0.52,2.48,0.18),(0,0.66,2.82,0.16),(0,0.74,3.16,0.15)]
for i,(x,y,z,s) in enumerate(neck_pts):
    cube(BODY,"Neck%d"%i,(x,y,z),(s,s+0.05,s),M_SCALE)
# 首背の棘（たてがみ状）
for i,(x,y,z,_) in enumerate(neck_pts):
    cone(BODY,"NeckSpike%d"%i,(0,y-0.10,z+0.14),0.05,0.20,M_HORN,verts=4,rot=(math.radians(-40),0,0))
# のどの発光（火の予兆）
sphere(BODY,"Throat",(0,0.62,2.62),(0.10,0.16,0.10),M_GLOW)

# ===== 頭（顎・牙・角・光る眼） =====
cube(BODY,"Head",(0,0.86,3.30),(0.20,0.26,0.18),M_SCALE)
cube(BODY,"Snout",(0,1.08,3.24),(0.15,0.18,0.12),M_SCALE)
cube(BODY,"Jaw",(0,1.04,3.12),(0.14,0.17,0.06),M_SCALE2)        # 下顎
cube(BODY,"MouthGlow",(0,1.02,3.18),(0.11,0.12,0.04),M_GLOW2)   # 口内の灯り
# 牙（上下各2）
for sgn in (1,-1):
    cone(BODY,"FangU%d"%sgn,(0.07*sgn,1.16,3.18),0.022,0.12,M_HORN,verts=4,rot=(math.radians(160),0,0))
    cone(BODY,"FangL%d"%sgn,(0.07*sgn,1.12,3.10),0.020,0.10,M_HORN,verts=4,rot=(math.radians(20),0,0))
# 眼（発光）＋眉庇
for sgn in (1,-1):
    sphere(BODY,"Eye%d"%sgn,(0.13*sgn,0.92,3.36),(0.045,0.03,0.04),M_GLOW,segs=10,rings=7)
    cube(BODY,"Brow%d"%sgn,(0.13*sgn,0.88,3.42),(0.07,0.07,0.04),M_SCALE2,rot=(math.radians(-16),0,0))
# 後ろへ伸びる2対の角
for sgn in (1,-1):
    cone(BODY,"Horn%d"%sgn,(0.12*sgn,0.74,3.50),0.05,0.34,M_HORN,verts=4,rot=(math.radians(48),0,math.radians(12*sgn)))
    cone(BODY,"HornB%d"%sgn,(0.16*sgn,0.66,3.40),0.035,0.22,M_HORN,verts=4,rot=(math.radians(58),0,math.radians(22*sgn)))
# 鼻孔の煙(暗い小球)
for sgn in (1,-1):
    sphere(BODY,"Nostril%d"%sgn,(0.05*sgn,1.18,3.27),(0.02,0.02,0.02),M_SCALE2,segs=8,rings=6)

# ===== 背棘（胴→尾） =====
for i,(yy,zz,ss) in enumerate([(0.10,2.20,0.22),(-0.10,2.12,0.24),(-0.32,1.98,0.22),(-0.52,1.80,0.18)]):
    cone(BODY,"BackSpike%d"%i,(0,yy,zz+0.10),0.06,ss,M_HORN,verts=4,rot=(math.radians(-65),0,0))

# ===== 尾（-Yへ伸び下降→先端上反り・5節＋尾棘） =====
tail_pts=[(0,-0.45,1.66,0.30),(0,-0.78,1.46,0.26),(0,-1.08,1.26,0.21),(0,-1.34,1.12,0.16),(0,-1.56,1.10,0.11)]
for i,(x,y,z,s) in enumerate(tail_pts):
    cube(BODY,"Tail%d"%i,(x,y,z),(s,s+0.08,s),M_SCALE)
# 尾先の棘（左右＋上）
cone(BODY,"TailSpikeT",(0,-1.68,1.18,),0.06,0.26,M_HORN,verts=4,rot=(math.radians(-30),0,0))
for sgn in (1,-1):
    cone(BODY,"TailSpike%d"%sgn,(0.07*sgn,-1.62,1.06),0.04,0.18,M_HORN,verts=4,rot=(math.radians(70),0,math.radians(30*sgn)))

# ===== 翼（ArmL/ArmR）：肩根 z=2.45。前縁骨は外＆上へ、膜は下へ垂れる縦セイル =====
#   蝙蝠状の大翼。raise spread の威圧ポーズ。Yフラップ(kry)で羽ばたき/煽り。
def wing(g,sgn):
    bx=0.30*sgn
    # 前縁の骨（肩→外＆上へ伸びる3節）
    cube(g,"WUpper",(bx+0.22*sgn,-0.05,2.58),(0.24,0.09,0.09),M_SCALE2,rot=(0,math.radians(-28*sgn),0))
    cube(g,"WFore", (bx+0.62*sgn,-0.08,2.98),(0.30,0.08,0.08),M_SCALE2,rot=(0,math.radians(-42*sgn),0))
    cube(g,"WSpar", (bx+1.00*sgn,-0.12,3.46),(0.34,0.06,0.06),M_SCALE2,rot=(0,math.radians(-54*sgn),0))
    # 翼端の爪（前縁の鉤）
    cone(g,"WClaw",(bx+1.30*sgn,-0.12,3.92),0.05,0.22,M_CLAW,verts=4,rot=(math.radians(90),0,math.radians(-60*sgn)))
    # 膜を支える指骨（前縁から下後方へ垂れる3本）
    for i,(tx,tz) in enumerate([(0.50,2.78),(0.82,2.46),(1.04,2.12)]):
        cube(g,"WFinger%d"%i,(bx+tx*sgn,-0.30,tz),(0.05,0.05,0.52),M_SCALE2,rot=(math.radians(22),0,math.radians(-18*sgn)))
    # 翼膜（縦のセイル＝大X×薄Y×大Z。前縁の下に扇状3枚で大きな翼面）
    memb=[(0.42,-0.26,2.78,0.50,0.66),(0.78,-0.28,2.46,0.46,0.58),(1.02,-0.30,2.14,0.38,0.48)]
    for i,(mx,my,mz,hx,hz) in enumerate(memb):
        cube(g,"WMemb%d"%i,(bx+mx*sgn,my,mz),(hx,0.012,hz),M_MEMB if i<2 else M_MEMB2,
             rot=(math.radians(8),math.radians(-38*sgn),0))
wing(WINGL,1); wing(WINGR,-1)

# ===== 後脚（LegL/LegR）：股ピボット z=0.98。太腿→脛→鉤爪足 =====
def leg(g,sgn):
    x=0.22*sgn
    cube(g,"Thigh",(x,-0.06,0.70),(0.18,0.22,0.46),M_SCALE)
    cube(g,"Shin",(x,0.06,0.30),(0.15,0.18,0.34),M_SCALE2)
    cube(g,"Foot",(x,0.18,0.07),(0.17,0.30,0.12),M_SCALE2)
    # 3本の鉤爪（前向き）＋蹴爪（後向き）
    for i,fx in enumerate((-0.08,0.0,0.08)):
        cone(g,"Toe%d_%d"%(sgn,i),(x+fx,0.36,0.05),0.035,0.16,M_CLAW,verts=4,rot=(math.radians(80),0,0))
    cone(g,"Spur%d"%sgn,(x,-0.02,0.10),0.03,0.12,M_CLAW,verts=4,rot=(math.radians(-80),0,0))
leg(LEGL,1); leg(LEGR,-1)

def join(group,name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in group:o.select_set(True)
    bpy.context.view_layer.objects.active=group[0];bpy.ops.object.join()
    o=bpy.context.active_object;o.name=name;return o
body=join(BODY,"Body");wingL=join(WINGL,"ArmL");wingR=join(WINGR,"ArmR");legL=join(LEGL,"LegL");legR=join(LEGR,"LegR")
def set_origin(o,p):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    scene.cursor.location=p;bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
set_origin(body,(0,0,0))
set_origin(wingL,(0.30,-0.05,2.45)); set_origin(wingR,(-0.30,-0.05,2.45))
set_origin(legL,(0.22,0,0.98)); set_origin(legR,(-0.22,0,0.98))
# 角張った鱗肌：bevelで角を立ててflat（軽量・golem準拠）
for o in (body,wingL,wingR,legL,legR):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    bv=o.modifiers.new("B",'BEVEL'); bv.width=0.015; bv.segments=1
    bpy.ops.object.modifier_apply(modifier=bv.name)
    bpy.ops.object.shade_flat()
def parent(c,p):
    bpy.ops.object.select_all(action='DESELECT');c.select_set(True);p.select_set(True)
    bpy.context.view_layer.objects.active=p;bpy.ops.object.parent_set(type='OBJECT',keep_transform=True)
for limb in (wingL,wingR,legL,legR): parent(limb,body)
bpy.context.view_layer.update()
minz=min((o.matrix_world@V(c)).z for o in (body,wingL,wingR,legL,legR) for c in o.bound_box)
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
BZ=body.location.z

# idle: 重い呼吸＋翼の緩やかな上下＋尾の余韻（体の微ピッチ）
new_action(body,"body_idle")
for f,z in [(1,BZ),(40,BZ+0.04),(80,BZ)]: kz(body,f,z)
push(body,"idle")
for w,sgn in [(wingL,1),(wingR,-1)]:
    new_action(w,w.name+"_idle")
    for f,d in [(1,0),(40,sgn*8),(80,0)]: kry(w,f,d)   # 翼を軽く畳む/開く
    push(w,"idle")

# walk: 後脚の踏み出し＋体の上下＋翼を半畳み
new_action(body,"body_walk")
for f,z in [(1,BZ),(10,BZ+0.05),(20,BZ),(30,BZ+0.05),(40,BZ)]: kz(body,f,z)
push(body,"walk")
for lg,sgn in [(legL,1),(legR,-1)]:
    new_action(lg,lg.name+"_walk")
    for f,d in [(1,0),(10,sgn*22),(20,0),(30,-sgn*22),(40,0)]: krx(lg,f,d)
    push(lg,"walk")
for w,sgn in [(wingL,1),(wingR,-1)]:
    new_action(w,w.name+"_walk")
    for f,d in [(1,0),(20,sgn*14),(40,0)]: kry(w,f,d)
    push(w,"walk")

# attack: 首・体の前傾＝噛みつき（体ピッチ前）＋翼を軽く張る
new_action(body,"body_attack")
for f,d in [(1,0),(7,-22),(13,4),(20,0)]: krx(body,f,d)   # 前へ突き込み→戻し
push(body,"attack")
for w,sgn in [(wingL,1),(wingR,-1)]:
    new_action(w,w.name+"_attack")
    for f,d in [(1,0),(7,sgn*20),(20,0)]: kry(w,f,d)      # 翼を張って威嚇
    push(w,"attack")

# heavy: 両翼の大煽り（ウイングバフェット）＋体を反らす
new_action(wingL,"ArmL_heavy")
for f,d in [(1,0),(9,55),(17,-35),(26,0)]: kry(wingL,f,d)
push(wingL,"heavy")
new_action(wingR,"ArmR_heavy")
for f,d in [(1,0),(9,-55),(17,35),(26,0)]: kry(wingR,f,d)
push(wingR,"heavy")
new_action(body,"body_heavy")
for f,d in [(1,0),(9,12),(17,-8),(26,0)]: krx(body,f,d)   # のけ反り→押し出し
push(body,"heavy")
scene.frame_set(1)

repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."));models=os.path.join(repo,"models");os.makedirs(models,exist_ok=True)
out=os.path.join(models,"mob_dragon.glb")
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_yup=True,
    export_apply=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_optimize_animation_size=True)
zs=[(o.matrix_world@V(v)).z for o in (body,wingL,wingR,legL,legR) for v in o.bound_box]
xs=[(o.matrix_world@V(v)).x for o in (wingL,wingR) for v in o.bound_box]
sz=os.path.getsize(out)
print("[voxel] dragon export -> %.3fMB  H%.2fm  wingspan%.2fm  clips: idle/walk/attack/heavy"
      %(sz/1048576, max(zs), max(xs)-min(xs)))

# ---- プレビュー描画（暗背景・発光が映える / 失敗しても export は完了済み）----
try:
    import sys
    do_render = "--render" in sys.argv
    if do_render:
        scene.frame_set(1)
        try: scene.render.engine='BLENDER_EEVEE_NEXT'
        except Exception: scene.render.engine='BLENDER_EEVEE'
        scene.render.resolution_x=780; scene.render.resolution_y=920
        scene.render.film_transparent=False
        world=bpy.data.worlds.new("W"); scene.world=world; world.use_nodes=True
        world.node_tree.nodes["Background"].inputs[0].default_value=(0.05,0.055,0.07,1)
        world.node_tree.nodes["Background"].inputs[1].default_value=1.3
        # ライト（強めのキー＋暖色フィルで発光と鱗を立たせる）
        bpy.ops.object.light_add(type='SUN',location=(3,-5,6)); sun=bpy.context.active_object
        sun.data.energy=4.8; sun.rotation_euler=(math.radians(52),0,math.radians(35))
        bpy.ops.object.light_add(type='AREA',location=(-3.5,-3,3.5)); fill=bpy.context.active_object
        fill.data.energy=300; fill.data.color=(1.0,0.45,0.22); fill.data.size=4.0
        def shot(name,cam_loc,cam_rot):
            bpy.ops.object.camera_add(location=cam_loc,rotation=cam_rot)
            cam=bpy.context.active_object; scene.camera=cam; cam.data.lens=42
            scene.render.filepath=os.path.join(repo,"tools",name)
            bpy.ops.render.render(write_still=True)
            bpy.data.objects.remove(cam,do_unlink=True)
        # 正面（顔が+Y側。やや見上げ気味で頭〜翼端を収める）
        shot("hero_mob_dragon_front.png",(0,6.2,2.1),(math.radians(85),0,math.radians(180)))
        # 3/4（威圧の翼が見える角度）
        shot("hero_mob_dragon_3q.png",(4.4,4.4,2.6),(math.radians(80),0,math.radians(135)))
        print("[voxel] dragon preview rendered: tools/hero_mob_dragon_front.png /_3q.png")
except Exception as e:
    print("[voxel] preview render skipped:", e)
