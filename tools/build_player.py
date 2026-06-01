# -*- coding: utf-8 -*-
# VOXEL WORLD - プレイヤーキャラ（人型ヒーロー）生成スクリプト【リグ＋アニメ版】
# Blender 5.1 / headless 実行用
#   実行: blender --background --python tools/build_player.py
#   出力: models/player.glb  (glTF Binary, Y-up, 足元原点, 正面=glTF -Z)
#         アニメ2クリップ内包: idle / walk
#
# 設計方針（司令塔指示・牛 mob_cow と骨格/クリップ名を統一）:
#   - 基準: Y-up / 足元中心が原点 / 正面 -Z / 身長 約1.9m / 1ブロック≒1m
#   - 顔/髪/筋肉まで作り込む（subsurf1+decimate で滑らか・ブロック調回避）
#   - リグ＋アニメを同梱（idle=待機, walk=歩行）。クリップ名は idle / walk
#   - armature不使用。胴(body)を root に、腕(肩ピボット)・脚(股関節ピボット)を
#     可動部品として分け、各部品の idle/walk アクションを同名NLAトラックに積んで
#     export_animation_mode='NLA_TRACKS' で2クリップ統合。
#   - Blender +Y → glTF -Z。正面(顔)は Blender +Y に作る。

import bpy, os, math, mathutils

# ----------------------------------------------------------------------
# 0. 初期化
# ----------------------------------------------------------------------
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for blk in (bpy.data.meshes, bpy.data.materials, bpy.data.objects, bpy.data.actions):
    for item in list(blk):
        try: blk.remove(item)
        except Exception: pass
scene = bpy.context.scene; scene.render.fps = 24

# ----------------------------------------------------------------------
# マテリアル
# ----------------------------------------------------------------------
def mat(name, rgb, rough=0.55, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    return m
# 見た目バリアント（PVARIANT 環境変数）。未指定=既定の青ヒーロー、出力は player.glb。
#   例: PVARIANT=crimson → player_crimson.glb（赤黒コスチューム）
VARIANT = os.environ.get("PVARIANT", "")
PALETTE = {
    "":        dict(suit=(0.12,0.22,0.55), acc=(0.85,0.16,0.16), boot=(0.30,0.06,0.06), hair=(0.10,0.08,0.07)),
    "crimson": dict(suit=(0.55,0.10,0.12), acc=(0.10,0.10,0.12), boot=(0.08,0.08,0.10), hair=(0.10,0.08,0.07)),
}
P = PALETTE.get(VARIANT, PALETTE[""])
MAT_SKIN = mat("Skin",(0.86,0.66,0.52),0.5);  MAT_SUIT = mat("Suit",P["suit"],0.45)
MAT_ACC  = mat("Accent",P["acc"],0.4);         MAT_HAIR = mat("Hair",P["hair"],0.6)
MAT_EYE  = mat("Eye",(0.05,0.05,0.08),0.2);    MAT_BELT = mat("Belt",(0.90,0.74,0.20),0.35,0.6)
MAT_BOOT = mat("Boot",P["boot"],0.45)

# ----------------------------------------------------------------------
# プリミティブ（グループ list に集約）
# ----------------------------------------------------------------------
def sphere(g, name, loc, scale, m, segs=20, rings=14):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=rings, location=loc)
    o = bpy.context.active_object; o.name=name; o.scale=scale; o.data.materials.append(m); g.append(o); return o
def cyl(g, name, loc, r, depth, m, verts=16, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc)
    o = bpy.context.active_object; o.name=name; o.rotation_euler=rot; o.data.materials.append(m); g.append(o); return o
def cube(g, name, loc, scale, m, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object; o.name=name; o.scale=scale; o.rotation_euler=rot; o.data.materials.append(m); g.append(o); return o

BODY=[]; ARML=[]; ARMR=[]; LEGL=[]; LEGR=[]

# ---- 胴体・胸・腹・肩・ベルト ----
cube(BODY,"Torso",(0,0,1.18),(0.30,0.18,0.30),MAT_SUIT)
sphere(BODY,"PecL",(0.13,-0.16,1.34),(0.13,0.10,0.11),MAT_SUIT)
sphere(BODY,"PecR",(-0.13,-0.16,1.34),(0.13,0.10,0.11),MAT_SUIT)
sphere(BODY,"Abs",(0,-0.15,1.02),(0.16,0.07,0.16),MAT_SUIT)
sphere(BODY,"ShoulderL",(0.29,0,1.45),(0.105,0.115,0.11),MAT_SUIT)
sphere(BODY,"ShoulderR",(-0.29,0,1.45),(0.105,0.115,0.11),MAT_SUIT)
cube(BODY,"Belt",(0,0,0.92),(0.31,0.195,0.07),MAT_BELT)
cube(BODY,"Buckle",(0,0.20,0.92),(0.06,0.03,0.05),MAT_ACC)
# ---- 首・頭・顔・髪 ----
cyl(BODY,"Neck",(0,0,1.58),0.085,0.12,MAT_SKIN)
sphere(BODY,"Head",(0,0,1.74),(0.135,0.15,0.165),MAT_SKIN,segs=28,rings=20)
sphere(BODY,"Jaw",(0,-0.02,1.66),(0.11,0.12,0.10),MAT_SKIN)
FY=0.13
sphere(BODY,"EyeL",(0.055,FY,1.76),(0.028,0.020,0.030),MAT_EYE,segs=14,rings=10)
sphere(BODY,"EyeR",(-0.055,FY,1.76),(0.028,0.020,0.030),MAT_EYE,segs=14,rings=10)
cube(BODY,"BrowL",(0.058,FY-0.005,1.795),(0.035,0.018,0.008),MAT_HAIR)
cube(BODY,"BrowR",(-0.058,FY-0.005,1.795),(0.035,0.018,0.008),MAT_HAIR)
sphere(BODY,"Nose",(0,FY+0.015,1.72),(0.025,0.035,0.030),MAT_SKIN,segs=14,rings=10)
cube(BODY,"Mouth",(0,FY,1.665),(0.045,0.012,0.010),MAT_ACC)
sphere(BODY,"Hair",(0,-0.01,1.80),(0.155,0.16,0.15),MAT_HAIR,segs=28,rings=20)
for i,x in enumerate((-0.08,-0.03,0.03,0.08)):
    cube(BODY,"Bang%d"%i,(x,FY-0.02,1.84),(0.022,0.03,0.05),MAT_HAIR,rot=(math.radians(20),0,0))
# ---- マント（背面 -Y）----
cube(BODY,"Cape",(0,-0.26,1.12),(0.33,0.015,0.50),MAT_ACC,rot=(math.radians(7),0,0))
sphere(BODY,"CapeClasp",(0,-0.16,1.50),(0.05,0.05,0.05),MAT_BELT)

# ---- 腕（肩ピボット z=1.46）----
def arm(g, s):
    x=0.34*s
    cyl(g,"UpperArm",(x,0,1.30),0.085,0.34,MAT_SKIN,rot=(0,math.radians(8*s),0))
    sphere(g,"Bicep",(x+0.01*s,-0.02,1.34),(0.09,0.10,0.10),MAT_SKIN)
    sphere(g,"Elbow",(x+0.04*s,0,1.12),(0.07,0.07,0.07),MAT_SKIN)
    cyl(g,"Forearm",(x+0.06*s,0,0.96),0.072,0.32,MAT_SKIN,rot=(0,math.radians(10*s),0))
    sphere(g,"Hand",(x+0.09*s,0,0.78),(0.075,0.06,0.09),MAT_SKIN)
    cyl(g,"Cuff",(x+0.07*s,0,0.86),0.078,0.06,MAT_ACC,rot=(0,math.radians(10*s),0))
arm(ARML,1); arm(ARMR,-1)

# ---- 脚（股関節ピボット z=0.84）----
def leg(g, s):
    x=0.12*s
    cyl(g,"Thigh",(x,0,0.62),0.105,0.42,MAT_SUIT)
    sphere(g,"ThighMass",(x,-0.02,0.66),(0.115,0.12,0.16),MAT_SUIT)
    sphere(g,"Knee",(x,0.01,0.40),(0.085,0.085,0.085),MAT_SUIT)
    cyl(g,"Shin",(x,0,0.22),0.085,0.36,MAT_SUIT)
    sphere(g,"Calf",(x,-0.04,0.26),(0.09,0.10,0.13),MAT_SUIT)
    cube(g,"Boot",(x,0.04,0.05),(0.10,0.17,0.06),MAT_BOOT)
    sphere(g,"Toe",(x,0.18,0.045),(0.095,0.07,0.05),MAT_BOOT)
leg(LEGL,1); leg(LEGR,-1)

# ----------------------------------------------------------------------
# グループを1オブジェクトに結合
# ----------------------------------------------------------------------
def join(group, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in group: o.select_set(True)
    bpy.context.view_layer.objects.active = group[0]
    bpy.ops.object.join()
    obj = bpy.context.active_object; obj.name = name; return obj
body = join(BODY,"Body"); armL=join(ARML,"ArmL"); armR=join(ARMR,"ArmR")
legL = join(LEGL,"LegL"); legR=join(LEGR,"LegR")

# ピボット（原点）設定
def set_origin(obj, p):
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    scene.cursor.location = p; bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
set_origin(body,(0,0,0))               # 足元中心が原点
set_origin(armL,(0.30,0,1.46));  set_origin(armR,(-0.30,0,1.46))
set_origin(legL,(0.12,0,0.84));  set_origin(legR,(-0.12,0,0.84))

# ----------------------------------------------------------------------
# ジオメトリ確定：subsurf1 + decimate + smooth（部品ごと）
# ----------------------------------------------------------------------
for o in (body,armL,armR,legL,legR):
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
    bpy.context.view_layer.objects.active = o
    s=o.modifiers.new("Sub",'SUBSURF'); s.levels=1; s.render_levels=1
    bpy.ops.object.shade_smooth(); bpy.ops.object.modifier_apply(modifier=s.name)
    d=o.modifiers.new("Dec",'DECIMATE'); d.decimate_type='COLLAPSE'; d.ratio=0.45
    bpy.ops.object.modifier_apply(modifier=d.name); bpy.ops.object.shade_smooth()

# ----------------------------------------------------------------------
# 親子付け（腕・脚 → body）
# ----------------------------------------------------------------------
def parent(child, par):
    bpy.ops.object.select_all(action='DESELECT')
    child.select_set(True); par.select_set(True); bpy.context.view_layer.objects.active=par
    bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
for limb in (armL,armR,legL,legR): parent(limb, body)

# ----------------------------------------------------------------------
# アニメーション（idle / walk）を NLA トラックで内包
# ----------------------------------------------------------------------
def new_action(obj,name):
    if obj.animation_data is None: obj.animation_data_create()
    a=bpy.data.actions.new(name); a.use_fake_user=True; obj.animation_data.action=a; return a
def push(obj,track):
    ad=obj.animation_data; act=ad.action
    t=ad.nla_tracks.new(); t.name=track; t.strips.new(act.name,int(act.frame_range[0]),act); ad.action=None
def key_z(obj,f,z): obj.location.z=z; obj.keyframe_insert('location',index=2,frame=f)
def key_rx(obj,f,d): obj.rotation_euler[0]=math.radians(d); obj.keyframe_insert('rotation_euler',index=0,frame=f)

BZ = body.location.z  # 0

# --- idle（48f≒2s）: 胴のゆるい上下＋腕の微揺れ ---
new_action(body,"body_idle")
for f,z in [(1,BZ),(24,BZ+0.015),(48,BZ)]: key_z(body,f,z)
push(body,"idle")
for a,sgn in [(armL,1),(armR,-1)]:
    new_action(a,a.name+"_idle")
    for f,d in [(1,0),(24,4*sgn),(48,0)]: key_rx(a,f,d)
    push(a,"idle")

# --- walk（20f≒0.83s）: 脚を逆位相、腕は脚と逆相 ---
LEG_AMP=16.0; ARM_AMP=14.0   # 足が地面下に潜りすぎない控えめ振幅
def swing(obj,amp,sign):
    new_action(obj,obj.name+"_walk")
    for f,p in [(1,1),(11,-1),(21,1)]: key_rx(obj,f,sign*p*amp)
    push(obj,"walk")
swing(legL,LEG_AMP,1); swing(legR,LEG_AMP,-1)     # 脚: L前→R後 で逆相
swing(armL,ARM_AMP,-1); swing(armR,ARM_AMP,1)     # 腕: 脚と逆相（自然な歩行）
new_action(body,"body_walk")                       # 胴の上下（2回/サイクル）
for f,z in [(1,BZ),(6,BZ+0.02),(11,BZ),(16,BZ+0.02),(21,BZ)]: key_z(body,f,z)
push(body,"walk")

# --- attack（16f≒0.67s）: 右腕の突き（前方=-Z）＋わずかな前傾。idle/walk と統一名 ---
new_action(armR,"armR_attack")
for f,d in [(1,0),(4,32),(9,-85),(13,-18),(16,0)]: key_rx(armR,f,d)  # 溜め→突き→戻り
push(armR,"attack")
new_action(armL,"armL_attack")
for f,d in [(1,0),(9,20),(16,0)]: key_rx(armL,f,d)                   # 反対腕で反動
push(armL,"attack")
new_action(body,"body_attack")
for f,d in [(1,0),(9,-7),(16,0)]: key_rx(body,f,d)                   # 軽い前傾（足元ピボット）
push(body,"attack")

# ----------------------------------------------------------------------
# 書き出し（GLB / Y-up / アニメ NLA トラック）
# ----------------------------------------------------------------------
repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
models=os.path.join(repo,"models"); os.makedirs(models,exist_ok=True)
out=os.path.join(models, "player.glb" if not VARIANT else ("player_%s.glb"%VARIANT))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=True,
    export_yup=True, export_apply=True, export_animations=True,
    export_animation_mode='NLA_TRACKS', export_optimize_animation_size=True)

zs=[]
for o in (body,armL,armR,legL,legR):
    for v in o.bound_box: zs.append((o.matrix_world@mathutils.Vector(v)).z)
print("[voxel] export OK ->", out)
print("[voxel] height(Z) ~= %.2f m (feet %.3f)" % (max(zs), min(zs)))
print("[voxel] clips: idle / walk / attack")
