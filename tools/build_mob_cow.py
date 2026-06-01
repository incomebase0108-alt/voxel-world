# -*- coding: utf-8 -*-
# VOXEL WORLD - モブ第一弾：牛（中立・四足動物） 生成スクリプト
# Blender 5.1 / headless 実行用
#   実行: blender --background --python tools/build_mob_cow.py
#   出力: models/mob_cow.glb  (glTF Binary, Y-up, 足元原点, 正面=glTF -Z)
#         アニメ2クリップ内包: idle / walk
#
# 設計方針（司令塔指示）:
#   - 基準は player と同じ: Y-up / 足元中心が原点 / 正面 -Z / 1ブロック≒1m
#   - 四足らしく 高さ1m前後・横長
#   - 軽量パイプライン（subsurf1 + decimate）で 1MB以下
#   - リグ＋アニメを最初から同梱（idle=待機, walk=歩行）。クリップ名は idle / walk
#   - armature を使わず「部品を body 配下に階層化し、脚は股関節を原点に回す」方式。
#     各オブジェクトに idle/walk のアクションを作り、同名 NLA トラックへ。
#     export_animation_mode='NLA_TRACKS' で同名トラックが1クリップに統合される。
#
# Blender軸→glTF(Y-up)変換: Blender +Y → glTF -Z。よって正面(顔)は Blender +Y に作る。

import bpy, os, math

# ----------------------------------------------------------------------
# 0. 初期化
# ----------------------------------------------------------------------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for blk in (bpy.data.meshes, bpy.data.materials, bpy.data.objects, bpy.data.actions):
    for item in list(blk):
        try: blk.remove(item)
        except Exception: pass

scene = bpy.context.scene
scene.render.fps = 24

# ----------------------------------------------------------------------
# マテリアル
# ----------------------------------------------------------------------
def mat(name, rgb, rough=0.7, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m

M_BODY  = mat("CowBody",  (0.93, 0.92, 0.90))   # 白
M_SPOT  = mat("CowSpot",  (0.18, 0.13, 0.10))   # こげ茶の斑
M_SNOUT = mat("Snout",    (0.94, 0.74, 0.74))   # 鼻面ピンク
M_NOSE  = mat("Nose",     (0.10, 0.08, 0.08))   # 鼻黒
M_HORN  = mat("Horn",     (0.90, 0.86, 0.72))   # 角クリーム
M_HOOF  = mat("Hoof",     (0.12, 0.10, 0.09))   # 蹄黒
M_EYE   = mat("Eye",      (0.05, 0.05, 0.06))   # 目
M_TUFT  = mat("Tuft",     (0.20, 0.15, 0.11))   # 尾の房

# ----------------------------------------------------------------------
# プリミティブ
# ----------------------------------------------------------------------
def sphere(name, loc, scale, m, segs=16, rings=10):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=rings, location=loc)
    o = bpy.context.active_object; o.name = name; o.scale = scale
    o.data.materials.append(m)
    return o

def cyl(name, loc, r, depth, m, verts=14, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc)
    o = bpy.context.active_object; o.name = name; o.rotation_euler = rot
    o.data.materials.append(m)
    return o

def set_origin(obj, point):
    """obj の原点を world 座標 point に移す（脚の股関節ピボット用）。"""
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True); bpy.context.view_layer.objects.active = obj
    scene.cursor.location = point
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

# ----------------------------------------------------------------------
# 1. 胴体（横長の楕円体）。中心 z=0.62、長手は Y（前後）。
# ----------------------------------------------------------------------
body = sphere("CowBody", (0, 0, 0.62), (0.24, 0.42, 0.27), M_BODY, segs=20, rings=14)

# 斑（body に従属）
spots = []
for i,(x,y,z,s) in enumerate([(0.12,0.12,0.74,0.10),(-0.14,-0.05,0.70,0.12),
                              (0.10,-0.22,0.60,0.09),(-0.08,0.24,0.66,0.08),
                              (0.16,-0.10,0.55,0.07)]):
    sp = sphere("Spot%d"%i, (x, y, z), (s, s*1.1, s), M_SPOT, segs=12, rings=8)
    spots.append(sp)

# ----------------------------------------------------------------------
# 2. 頭（前=+Y）。鼻面・鼻・目・耳・角。
# ----------------------------------------------------------------------
head  = sphere("CowHead", (0, 0.50, 0.80), (0.16, 0.18, 0.16), M_BODY, segs=18, rings=12)
snout = sphere("Snout", (0, 0.66, 0.74), (0.11, 0.09, 0.09), M_SNOUT)
noseL = sphere("NoseL", (0.04, 0.73, 0.74), (0.02,0.015,0.02), M_NOSE, segs=10, rings=8)
noseR = sphere("NoseR", (-0.04, 0.73, 0.74), (0.02,0.015,0.02), M_NOSE, segs=10, rings=8)
eyeL  = sphere("EyeL", (0.09, 0.60, 0.86), (0.025,0.02,0.03), M_EYE, segs=10, rings=8)
eyeR  = sphere("EyeR", (-0.09, 0.60, 0.86), (0.025,0.02,0.03), M_EYE, segs=10, rings=8)
earL  = sphere("EarL", (0.15, 0.46, 0.88), (0.06,0.03,0.04), M_BODY)
earR  = sphere("EarR", (-0.15, 0.46, 0.88), (0.06,0.03,0.04), M_BODY)
hornL = sphere("HornL", (0.07, 0.44, 0.95), (0.03,0.03,0.05), M_HORN, segs=10, rings=8)
hornR = sphere("HornR", (-0.07, 0.44, 0.95), (0.03,0.03,0.05), M_HORN, segs=10, rings=8)
head_children = [snout, noseL, noseR, eyeL, eyeR, earL, earR, hornL, hornR]

# ----------------------------------------------------------------------
# 3. 脚 ×4（股関節 z=0.50 を原点に。下端 z=0 接地）。前=+Y。
# ----------------------------------------------------------------------
HIP_Z = 0.50
LEG_LEN = 0.50
def make_leg(name, x, y):
    # 中心 z = HIP_Z - LEG_LEN/2 = 0.25、下端 0、上端 0.5
    leg = cyl(name, (x, y, HIP_Z - LEG_LEN/2), 0.065, LEG_LEN, M_BODY)
    hoof = cyl(name+"_hoof", (x, y, 0.03), 0.07, 0.06, M_HOOF)
    set_origin(leg, (x, y, HIP_Z))     # 股関節を原点に
    return leg, hoof

legFL, hoofFL = make_leg("LegFL", 0.15, 0.28)
legFR, hoofFR = make_leg("LegFR", -0.15, 0.28)
legBL, hoofBL = make_leg("LegBL", 0.15, -0.28)
legBR, hoofBR = make_leg("LegBR", -0.15, -0.28)
legs = [legFL, legFR, legBL, legBR]
hooves = {legFL:hoofFL, legFR:hoofFR, legBL:hoofBL, legBR:hoofBR}

# ----------------------------------------------------------------------
# 4. 尾（背面 -Y）。tuft（房）は尾に従属。
# ----------------------------------------------------------------------
tail = cyl("Tail", (0, -0.44, 0.66), 0.022, 0.34, M_BODY, rot=(math.radians(28),0,0))
set_origin(tail, (0, -0.42, 0.82))    # 付け根を原点に（揺れ用）
tuft = sphere("Tuft", (0, -0.52, 0.50), (0.04,0.04,0.06), M_TUFT)

# ----------------------------------------------------------------------
# 5. ジオメトリ確定：subsurf1 + decimate + smooth（部品ごと）
# ----------------------------------------------------------------------
all_parts = [body]+spots+[head]+head_children+legs+list(hooves.values())+[tail, tuft]
for o in all_parts:
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True); bpy.context.view_layer.objects.active = o
    s = o.modifiers.new("Sub", 'SUBSURF'); s.levels = 1; s.render_levels = 1
    bpy.ops.object.shade_smooth()
    bpy.ops.object.modifier_apply(modifier=s.name)
    d = o.modifiers.new("Dec", 'DECIMATE'); d.decimate_type='COLLAPSE'; d.ratio=0.5
    bpy.ops.object.modifier_apply(modifier=d.name)
    bpy.ops.object.shade_smooth()

# ----------------------------------------------------------------------
# 6. 親子付け（keep transform）
# ----------------------------------------------------------------------
def parent(child, par):
    bpy.ops.object.select_all(action='DESELECT')
    child.select_set(True); par.select_set(True)
    bpy.context.view_layer.objects.active = par
    bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)

for sp in spots: parent(sp, body)
for c in head_children: parent(c, head)
parent(head, body)
for lg in legs: parent(hooves[lg], lg); parent(lg, body)
parent(tuft, tail); parent(tail, body)

# ----------------------------------------------------------------------
# 7. アニメーション（idle / walk）を NLA トラックで内包
# ----------------------------------------------------------------------
def new_action(obj, name):
    if obj.animation_data is None: obj.animation_data_create()
    act = bpy.data.actions.new(name); act.use_fake_user = True
    obj.animation_data.action = act
    return act

def push(obj, track_name):
    ad = obj.animation_data; act = ad.action
    trk = ad.nla_tracks.new(); trk.name = track_name
    trk.strips.new(act.name, int(act.frame_range[0]), act)
    ad.action = None

def key_z(obj, frame, z):
    obj.location.z = z; obj.keyframe_insert('location', index=2, frame=frame)

def key_rx(obj, frame, deg):
    obj.rotation_euler[0] = math.radians(deg); obj.keyframe_insert('rotation_euler', index=0, frame=frame)

def key_ry(obj, frame, deg):
    obj.rotation_euler[1] = math.radians(deg); obj.keyframe_insert('rotation_euler', index=1, frame=frame)

# 静止時の基準
BODY_Z = body.location.z  # 0.62

# --- idle（48フレーム ≒ 2秒、ゆっくり呼吸＋尾揺れ）---
a = new_action(body, "body_idle")
for f,z in [(1,BODY_Z),(24,BODY_Z+0.02),(48,BODY_Z)]: key_z(body, f, z)
push(body, "idle")
a = new_action(head, "head_idle")
for f,d in [(1,0),(24,3),(48,0)]: key_rx(head, f, d)
push(head, "idle")
a = new_action(tail, "tail_idle")
for f,d in [(1,-5),(24,5),(48,-5)]: key_ry(tail, f, d)
push(tail, "idle")

# --- walk（20フレーム ≒ 0.83秒ループ、対角の脚を逆位相）---
AMP = 22.0
# A位相: FL, BR / B位相: FR, BL
phaseA = [legFL, legBR]; phaseB = [legFR, legBL]
def walk_leg(leg, sign):
    a = new_action(leg, leg.name+"_walk")
    for f,p in [(1,1),(11,-1),(21,1)]:
        key_rx(leg, f, sign*p*AMP)
    push(leg, "walk")
for lg in phaseA: walk_leg(lg, 1)
for lg in phaseB: walk_leg(lg, -1)
# 胴の上下（1サイクルに2回）
a = new_action(body, "body_walk")
for f,z in [(1,BODY_Z),(6,BODY_Z+0.02),(11,BODY_Z),(16,BODY_Z+0.02),(21,BODY_Z)]: key_z(body, f, z)
push(body, "walk")
# 尾を振る
a = new_action(tail, "tail_walk")
for f,d in [(1,-12),(11,12),(21,-12)]: key_ry(tail, f, d)
push(tail, "walk")
# 頭を軽く上下
a = new_action(head, "head_walk")
for f,d in [(1,-2),(11,4),(21,-2)]: key_rx(head, f, d)
push(head, "walk")

# 補間を線形寄りに（カクつかせず軽く）→ デフォルトBezierのままでOK

# ----------------------------------------------------------------------
# 8. 書き出し（GLB / Y-up / アニメ NLA トラック）
# ----------------------------------------------------------------------
repo = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
models = os.path.join(repo, "models"); os.makedirs(models, exist_ok=True)
out = os.path.join(models, "mob_cow.glb")

bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(
    filepath=out, export_format='GLB',
    use_selection=True, export_yup=True, export_apply=True,
    export_animations=True, export_animation_mode='NLA_TRACKS',
    export_optimize_animation_size=True,
)

# 寸法ログ（全体のバウンディング）
import mathutils
zs=[]; ys=[]; xs=[]
for o in all_parts:
    for v in o.bound_box:
        w = o.matrix_world @ mathutils.Vector(v)
        xs.append(w.x); ys.append(w.y); zs.append(w.z)
print("[voxel] export OK ->", out)
print("[voxel] bbox (Blender m)  X:%.2f..%.2f  Y(前後):%.2f..%.2f  Z(高さ):%.2f..%.2f" %
      (min(xs),max(xs),min(ys),max(ys),min(zs),max(zs)))
print("[voxel] clips: idle / walk")
