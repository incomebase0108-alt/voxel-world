# -*- coding: utf-8 -*-
# VOXEL WORLD - プレイヤーキャラ（ヒーロー作り込み版・本番）
# blender --background --python tools/build_player_hero.py
#   方向確認フェーズ: ライブ models/player.glb は上書きせず tools/_work/player_hero.glb に出力し
#   front/3q/idleプレビューを tools/ に描画。OK後に build_player.py へ反映して5色展開する。
#   方針(司令塔): ヒロイック・重厚・洗練。肩当て/胸甲/籠手/膝当て/丈高ブーツ/V字シルエット/
#   流れるマント。2MB以下維持(subsurf1+decimate)。PVARIANTパレット互換。frame1中立rest。

import bpy, os, math, mathutils
V=mathutils.Vector
scene=bpy.context.scene; scene.render.fps=24
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for blk in (bpy.data.meshes,bpy.data.materials,bpy.data.objects,bpy.data.actions):
    for it in list(blk):
        try: blk.remove(it)
        except Exception: pass

def mat(n,rgb,r=0.5,me=0.0):
    m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*rgb,1.0);b.inputs["Roughness"].default_value=r;b.inputs["Metallic"].default_value=me;return m

VARIANT=os.environ.get("PVARIANT","")
PALETTE={
 "":        dict(suit=(0.12,0.22,0.55), acc=(0.85,0.16,0.16), boot=(0.20,0.20,0.24), hair=(0.10,0.08,0.07)),
 "crimson": dict(suit=(0.55,0.10,0.12), acc=(0.92,0.78,0.30), boot=(0.10,0.10,0.12), hair=(0.10,0.08,0.07)),
 "azure":   dict(suit=(0.10,0.45,0.85), acc=(0.95,0.95,1.00), boot=(0.10,0.14,0.22), hair=(0.10,0.08,0.07)),
 "emerald": dict(suit=(0.10,0.50,0.28), acc=(0.92,0.78,0.20), boot=(0.10,0.18,0.12), hair=(0.10,0.08,0.07)),
 "gold":    dict(suit=(0.85,0.66,0.16), acc=(0.30,0.24,0.12), boot=(0.22,0.18,0.08), hair=(0.10,0.08,0.07)),
}
P=PALETTE.get(VARIANT,PALETTE[""])
SKIN=mat("Skin",(0.86,0.66,0.52),0.5); SUIT=mat("Suit",P["suit"],0.45); ACC=mat("Accent",P["acc"],0.35)
HAIR=mat("Hair",P["hair"],0.55); EYE=mat("Eye",(0.05,0.05,0.08),0.2); BELT=mat("Belt",(0.88,0.72,0.20),0.35,0.6)
BOOT=mat("Boot",P["boot"],0.45); ARMOR=mat("Armor",(0.78,0.80,0.84),0.3,0.9); ARMOR2=mat("Armor2",(0.62,0.64,0.69),0.35,0.9)
UNDER=mat("Under",(0.16,0.16,0.19),0.6)   # アンダースーツ（暗色・引き締め）

def sphere(g,n,loc,sc,m,segs=20,rings=14):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs,ring_count=rings,location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=sc;o.data.materials.append(m);g.append(o);return o
def cyl(g,n,loc,r,d,m,verts=16,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d,location=loc)
    o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);g.append(o);return o
def cube(g,n,loc,sc,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=sc;o.rotation_euler=rot;o.data.materials.append(m);g.append(o);return o

BODY=[];ARML=[];ARMR=[];LEGL=[];LEGR=[]

# ====== 胴：V字シルエット（広い胸郭→絞った腰）＋胸甲 ======
cube(BODY,"Torso",(0,0,1.20),(0.30,0.17,0.30),SUIT)            # 基部
sphere(BODY,"Chest",(0,-0.05,1.36),(0.32,0.20,0.20),ARMOR)     # 胸甲（広い胸板）
sphere(BODY,"PecL",(0.14,-0.14,1.34),(0.13,0.11,0.12),ARMOR)
sphere(BODY,"PecR",(-0.14,-0.14,1.34),(0.13,0.11,0.12),ARMOR)
cube(BODY,"Sternum",(0,-0.20,1.30),(0.025,0.03,0.18),ACC)       # 胸の中央ライン
sphere(BODY,"Emblem",(0,-0.22,1.40),(0.05,0.03,0.05),ACC)       # 胸の紋章
sphere(BODY,"Abs",(0,-0.14,1.02),(0.15,0.08,0.15),UNDER)        # 絞った腹（暗色）
sphere(BODY,"Waist",(0,0,0.96),(0.18,0.13,0.10),UNDER)          # くびれ
# 肩当て（パルドロン・層状の重厚な装甲）
for sgn in (1,-1):
    sphere(BODY,"Pauld%d"%sgn,(0.30*sgn,0,1.50),(0.16,0.17,0.13),ARMOR)
    sphere(BODY,"PauldT%d"%sgn,(0.31*sgn,0,1.57),(0.13,0.14,0.08),ARMOR2)
    cube(BODY,"PauldR%d"%sgn,(0.40*sgn,0,1.46),(0.04,0.15,0.08),ACC,rot=(math.radians(12*sgn),0,0))
# ベルト＋バックル＋サイドポーチ
cube(BODY,"Belt",(0,0,0.90),(0.30,0.18,0.06),BELT)
cube(BODY,"Buckle",(0,0.19,0.90),(0.06,0.03,0.06),ARMOR)
cube(BODY,"Pouch",(0.22,0.10,0.86),(0.05,0.05,0.07),BOOT)
cube(BODY,"Tasset",(0,0.0,0.80),(0.20,0.14,0.06),ARMOR2)        # 腰当て

# ====== 首・頭・顔（精悍な造形）======
cyl(BODY,"Neck",(0,0,1.60),0.08,0.12,SKIN)
sphere(BODY,"Head",(0,0,1.76),(0.128,0.145,0.16),SKIN,segs=30,rings=22)
cube(BODY,"Jaw",(0,-0.04,1.685),(0.105,0.10,0.07),SKIN)         # 角ばった顎（精悍）
FY=0.125
sphere(BODY,"EyeL",(0.052,FY,1.775),(0.026,0.018,0.028),EYE,segs=14,rings=10)
sphere(BODY,"EyeR",(-0.052,FY,1.775),(0.026,0.018,0.028),EYE,segs=14,rings=10)
cube(BODY,"BrowL",(0.056,FY-0.002,1.80),(0.04,0.02,0.01),HAIR,rot=(0,0,math.radians(-6)))
cube(BODY,"BrowR",(-0.056,FY-0.002,1.80),(0.04,0.02,0.01),HAIR,rot=(0,0,math.radians(6)))
sphere(BODY,"Nose",(0,FY+0.02,1.735),(0.022,0.04,0.03),SKIN,segs=14,rings=10)
cube(BODY,"Mouth",(0,FY+0.005,1.675),(0.04,0.012,0.009),mat("Lip",(0.62,0.40,0.36)))
# 髪（後ろへ流すボリューム・ヒロイック）
sphere(BODY,"Hair",(0,-0.03,1.83),(0.15,0.165,0.15),HAIR,segs=28,rings=20)
for i,x in enumerate((-0.10,-0.04,0.04,0.10)):
    cube(BODY,"HairSwept%d"%i,(x,-0.13,1.83),(0.03,0.10,0.06),HAIR,rot=(math.radians(-28),0,0))  # 後ろへ
cube(BODY,"HairFringe",(0,FY-0.02,1.86),(0.13,0.04,0.05),HAIR,rot=(math.radians(18),0,0))

# ====== マント（肩から流れる・大きめ）======
cube(BODY,"Cape",(0,-0.27,1.10),(0.34,0.015,0.56),ACC,rot=(math.radians(6),0,0))
cube(BODY,"CapeLow",(0,-0.32,0.70),(0.30,0.015,0.34),ACC,rot=(math.radians(14),0,0))
for sgn in (1,-1):                                              # 肩の留め具
    sphere(BODY,"Clasp%d"%sgn,(0.20*sgn,-0.10,1.52),(0.05,0.05,0.05),BELT)

# ====== 腕（肩ピボット z=1.46）：上腕＋籠手 ======
def arm(g,s):
    x=0.34*s
    sphere(g,"Delt",(x,0,1.42),(0.10,0.11,0.11),SUIT)
    cyl(g,"Upper",(x,0,1.28),0.082,0.32,UNDER,rot=(0,math.radians(8*s),0))
    sphere(g,"Elbow",(x+0.04*s,0,1.10),(0.07,0.07,0.07),UNDER)
    cyl(g,"Bracer",(x+0.06*s,0,0.95),0.078,0.30,ARMOR,rot=(0,math.radians(10*s),0))  # 籠手（装甲）
    cube(g,"BracerEdge",(x+0.06*s,-0.05,1.06),(0.07,0.03,0.03),ACC,rot=(0,math.radians(10*s),0))
    sphere(g,"Hand",(x+0.09*s,0,0.78),(0.072,0.06,0.085),BOOT)   # グローブ
    sphere(g,"Knuckle",(x+0.10*s,0.04,0.76),(0.05,0.04,0.05),ARMOR2)
arm(ARML,1); arm(ARMR,-1)

# ====== 脚（股ピボット z=0.84）：太腿＋膝当て＋丈高ブーツ ======
def leg(g,s):
    x=0.13*s
    cyl(g,"Thigh",(x,0,0.62),0.105,0.42,UNDER)
    sphere(g,"ThighMass",(x,-0.02,0.66),(0.115,0.12,0.17),UNDER)
    sphere(g,"Knee",(x,0.02,0.40),(0.09,0.09,0.09),ARMOR)        # 膝当て
    cube(g,"KneeGuard",(x,0.07,0.40),(0.08,0.04,0.07),ARMOR2)
    cyl(g,"Shin",(x,0,0.24),0.088,0.34,BOOT)                     # 丈高ブーツ（脛まで）
    sphere(g,"Calf",(x,-0.04,0.28),(0.092,0.10,0.14),BOOT)
    cube(g,"BootTop",(x,-0.02,0.40),(0.10,0.11,0.05),ACC)        # ブーツ上端の折返し
    cube(g,"Foot",(x,0.05,0.05),(0.10,0.18,0.07),BOOT)
    sphere(g,"Toe",(x,0.19,0.05),(0.095,0.07,0.055),BOOT)
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
set_origin(body,(0,0,0)); set_origin(armL,(0.30,0,1.46)); set_origin(armR,(-0.30,0,1.46))
set_origin(legL,(0.13,0,0.84)); set_origin(legR,(-0.13,0,0.84))
# subsurf1+decimate（容量に余裕があるので decimate 0.55 でディテール温存）
for o in (body,armL,armR,legL,legR):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    s=o.modifiers.new("Sub",'SUBSURF');s.levels=1;s.render_levels=1
    bpy.ops.object.shade_smooth();bpy.ops.object.modifier_apply(modifier=s.name)
    d=o.modifiers.new("Dec",'DECIMATE');d.decimate_type='COLLAPSE';d.ratio=0.55
    bpy.ops.object.modifier_apply(modifier=d.name);bpy.ops.object.shade_smooth()
def parent(c,p):
    bpy.ops.object.select_all(action='DESELECT');c.select_set(True);p.select_set(True)
    bpy.context.view_layer.objects.active=p;bpy.ops.object.parent_set(type='OBJECT',keep_transform=True)
for limb in (armL,armR,legL,legR): parent(limb,body)
bpy.context.view_layer.update()
minz=min((o.matrix_world@V(c)).z for o in (body,armL,armR,legL,legR) for c in o.bound_box)
body.location.z-=minz

# ---- アニメ（frame1中立・idle構え/walk/attack）----
def new_action(o,n):
    if o.animation_data is None:o.animation_data_create()
    a=bpy.data.actions.new(n);a.use_fake_user=True;o.animation_data.action=a;return a
def push(o,t):
    ad=o.animation_data;act=ad.action;tr=ad.nla_tracks.new();tr.name=t
    tr.strips.new(act.name,int(act.frame_range[0]),act);ad.action=None
def kz(o,f,z):o.location.z=z;o.keyframe_insert('location',index=2,frame=f)
def krx(o,f,d):o.rotation_euler[0]=math.radians(d);o.keyframe_insert('rotation_euler',index=0,frame=f)
BZ=body.location.z
new_action(body,"body_idle")
for f,z in [(1,BZ),(24,BZ+0.014),(48,BZ)]: kz(body,f,z)
for f in (1,48): krx(body,f,0)   # 体回転X=0の保持（見た目不変・退水時に直立へ確実に戻すため）
push(body,"idle")
for a,sgn in [(armL,1),(armR,-1)]:
    new_action(a,a.name+"_idle")
    for f,d in [(1,0),(24,4*sgn),(48,0)]: krx(a,f,d)
    push(a,"idle")
LA=16.0;AA=14.0
new_action(legL,"LegL_walk")
for f,d in [(1,0),(6,LA),(11,0),(16,-LA),(21,0)]: krx(legL,f,d)
push(legL,"walk")
new_action(legR,"LegR_walk")
for f,d in [(1,0),(6,-LA),(11,0),(16,LA),(21,0)]: krx(legR,f,d)
push(legR,"walk")
new_action(armL,"ArmL_walk")
for f,d in [(1,0),(6,-AA),(11,0),(16,AA),(21,0)]: krx(armL,f,d)
push(armL,"walk")
new_action(armR,"ArmR_walk")
for f,d in [(1,0),(6,AA),(11,0),(16,-AA),(21,0)]: krx(armR,f,d)
push(armR,"walk")
new_action(body,"body_walk")
for f,z in [(1,BZ),(6,BZ+0.02),(11,BZ),(16,BZ+0.02),(21,BZ)]: kz(body,f,z)
for f in (1,21): krx(body,f,0)   # 体回転X=0の保持（見た目不変・退水時に直立へ確実に戻すため）
push(body,"walk")
new_action(armR,"armR_attack")
for f,d in [(1,0),(4,32),(9,-85),(13,-18),(16,0)]: krx(armR,f,d)
push(armR,"attack")
new_action(armL,"armL_attack")
for f,d in [(1,0),(9,20),(16,0)]: krx(armL,f,d)
push(armL,"attack")
new_action(body,"body_attack")
for f,d in [(1,0),(9,-7),(16,0)]: krx(body,f,d)
push(body,"attack")

# ---- swim（水平姿勢のクロール：体前傾水平＋両腕の水かき＋バタ足。frame1=最終で継ぎ目なしループ）----
# 既存 idle/walk/attack は不変。骨格・ピボットも不変。体ピッチは Body 回転Xで表現（退水時 idle/walk が0へ戻す）。
SWP=-82.0   # 体ピッチ角(度)：頭は前方+Y・うつ伏せの水平姿勢
new_action(body,"body_swim")
for f,d in [(1,SWP),(12,SWP-4),(24,SWP),(36,SWP+4),(48,SWP)]: krx(body,f,d)   # ゆるやかな上下うねり
push(body,"swim")
new_action(armL,"ArmL_swim")
for f,d in [(1,0),(24,180),(48,360)]: krx(armL,f,d)        # 風車状の水かき（1回転/ループ）
push(armL,"swim")
new_action(armR,"ArmR_swim")
for f,d in [(1,180),(24,360),(48,540)]: krx(armR,f,d)      # 半周ずらし＝左右交互のクロール
push(armR,"swim")
for lg,sgn in [(legL,1),(legR,-1)]:
    new_action(lg,lg.name+"_swim")
    for f,d in [(1,0),(6,sgn*13),(12,0),(18,-sgn*13),(24,0),(30,sgn*13),(36,0),(42,-sgn*13),(48,0)]: krx(lg,f,d)  # バタ足
    push(lg,"swim")
scene.frame_set(1)

repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
models=os.path.join(repo,"models"); os.makedirs(models,exist_ok=True)
out=os.path.join(models, "player.glb" if not VARIANT else ("player_%s.glb"%VARIANT))
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(filepath=out,export_format="GLB",use_selection=True,export_yup=True,
    export_apply=True,export_animations=True,export_animation_mode="NLA_TRACKS",export_optimize_animation_size=True)
zs=[(o.matrix_world@V(v)).z for o in (body,armL,armR,legL,legR) for v in o.bound_box]
sz=os.path.getsize(out)
print("[voxel] export OK -> %s  %.3fMB  H%.2fm  clips: idle/walk/attack/swim"%(out, sz/1048576, max(zs)))

# ---- swim 姿勢の検証プレビュー（NLAで swim のみソロ。--render 時のみ・失敗してもexport完了済み）----
try:
    import sys
    if "--render" in sys.argv:
        for o in (body,armL,armR,legL,legR):
            if o.animation_data:
                for tr in o.animation_data.nla_tracks: tr.mute = (tr.name != "swim")
        try: scene.render.engine='BLENDER_EEVEE_NEXT'
        except Exception: scene.render.engine='BLENDER_EEVEE'
        scene.render.resolution_x=940; scene.render.resolution_y=620
        world=bpy.data.worlds.new("W"); scene.world=world; world.use_nodes=True
        world.node_tree.nodes["Background"].inputs[0].default_value=(0.06,0.10,0.16,1)
        world.node_tree.nodes["Background"].inputs[1].default_value=1.2
        bpy.ops.object.light_add(type='SUN',location=(3,-4,7)); sun=bpy.context.active_object
        sun.data.energy=4.2; sun.rotation_euler=(math.radians(55),0,math.radians(30))
        def shot(name,f,cam_loc,cam_rot):
            scene.frame_set(f)
            bpy.ops.object.camera_add(location=cam_loc,rotation=cam_rot)
            cam=bpy.context.active_object; scene.camera=cam; cam.data.lens=40
            scene.render.filepath=os.path.join(repo,"tools",name)
            bpy.ops.render.render(write_still=True)
            bpy.data.objects.remove(cam,do_unlink=True)
        # 側面（profile：+Yが右＝進行方向）でうつ伏せ水平姿勢を確認、frame1とframe24
        shot("hero_player_swim_side1.png",1,(6.5,0.4,1.5),(math.radians(88),0,math.radians(90)))
        shot("hero_player_swim_side24.png",24,(6.5,0.4,1.5),(math.radians(88),0,math.radians(90)))
        # 3/4 俯瞰
        shot("hero_player_swim_3q.png",24,(4.6,3.2,3.4),(math.radians(58),0,math.radians(126)))
        print("[voxel] swim preview rendered: tools/hero_player_swim_side1/side24/3q.png")
except Exception as e:
    print("[voxel] swim preview skipped:", e)
