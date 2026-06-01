# -*- coding: utf-8 -*-
# VOXEL WORLD - プレイヤーキャラ（人型ヒーロー）生成スクリプト
# Blender 5.1 / headless 実行用
#   実行: blender --background --python tools/build_player.py
#   出力: models/player.glb  (glTF Binary, Y-up, 足元原点, 正面=glTF -Z)
#
# 設計方針（README/Slackブリーフ準拠）:
#   - ブロック調・カクカクは避ける → subsurf + smooth shading で滑らかに
#   - 顔パーツ(目/鼻/口)・髪・筋肉(胸/腹/腕/脚)まで作り込む
#   - 1ブロック≒1m、身長 約1.9m
#   - 足元中心が原点(Blender Z=0)、正面は Blender +Y（= glTF -Z）

import bpy
import os
import math
from mathutils import Vector

# ----------------------------------------------------------------------
# 0. シーン初期化
# ----------------------------------------------------------------------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for blk in (bpy.data.meshes, bpy.data.materials, bpy.data.objects):
    for item in list(blk):
        try:
            blk.remove(item)
        except Exception:
            pass

# ----------------------------------------------------------------------
# マテリアル
# ----------------------------------------------------------------------
def make_mat(name, rgb, rough=0.55, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    return m

MAT_SKIN  = make_mat("Skin",   (0.86, 0.66, 0.52), rough=0.5)
MAT_SUIT  = make_mat("Suit",   (0.12, 0.22, 0.55), rough=0.45)   # ヒーロースーツ(青)
MAT_ACC   = make_mat("Accent", (0.85, 0.16, 0.16), rough=0.4)    # アクセント(赤)
MAT_HAIR  = make_mat("Hair",   (0.10, 0.08, 0.07), rough=0.6)
MAT_EYE   = make_mat("Eye",    (0.05, 0.05, 0.08), rough=0.2)
MAT_BELT  = make_mat("Belt",   (0.90, 0.74, 0.20), rough=0.35, metal=0.6)  # 金ベルト
MAT_BOOT  = make_mat("Boot",   (0.30, 0.06, 0.06), rough=0.45)

# ----------------------------------------------------------------------
# プリミティブ生成ヘルパ
# ----------------------------------------------------------------------
parts = []

def add_part(obj, mat, smooth=True):
    obj.data.materials.append(mat)
    if smooth:
        for p in obj.data.polygons:
            p.use_smooth = True
    parts.append(obj)
    return obj

def sphere(name, loc, scale, mat, segs=24, rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=rings, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    return add_part(o, mat)

def cyl(name, loc, radius, depth, mat, verts=24, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.rotation_euler = rot
    return add_part(o, mat)

def cube(name, loc, scale, mat, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    o.rotation_euler = rot
    return add_part(o, mat)

# ----------------------------------------------------------------------
# 1. 体（torso）— 胸板/腹/くびれ。スーツ色。
#    身長 約1.9m。足元 Z=0。
# ----------------------------------------------------------------------
# 胴体：上が広く下がくびれた逆台形。立方体を変形 + subsurf。
torso = cube("Torso", (0, 0, 1.18), (0.30, 0.18, 0.30), MAT_SUIT)
# 上部を広げ下部を絞る → 簡易に上半身を伸ばし、後で subsurf で丸める
# 胸の盛り上がり（筋肉）
chestL = sphere("PecL", (0.13, -0.16, 1.34), (0.13, 0.10, 0.11), MAT_SUIT)
chestR = sphere("PecR", (-0.13, -0.16, 1.34), (0.13, 0.10, 0.11), MAT_SUIT)
# 腹筋ブロック（うっすら）
abs_ = sphere("Abs", (0, -0.15, 1.02), (0.16, 0.07, 0.16), MAT_SUIT)
# 肩
shL = sphere("ShoulderL", (0.29, 0, 1.45), (0.105, 0.115, 0.11), MAT_SUIT)
shR = sphere("ShoulderR", (-0.29, 0, 1.45), (0.105, 0.115, 0.11), MAT_SUIT)
# 腰ベルト（胴に沿う角ベルト。前後に飛び出さない）
belt = cube("Belt", (0, 0, 0.92), (0.31, 0.195, 0.07), MAT_BELT)
beltbuckle = cube("Buckle", (0, 0.20, 0.92), (0.06, 0.03, 0.05), MAT_ACC)

# ----------------------------------------------------------------------
# 2. 首・頭
# ----------------------------------------------------------------------
neck = cyl("Neck", (0, 0, 1.58), 0.085, 0.12, MAT_SKIN)
head = sphere("Head", (0, 0, 1.74), (0.135, 0.15, 0.165), MAT_SKIN, segs=32, rings=24)
jaw  = sphere("Jaw", (0, -0.02, 1.66), (0.11, 0.12, 0.10), MAT_SKIN)

# ----------------------------------------------------------------------
# 3. 顔パーツ（正面 = -Y 側に配置。後で全体を +Y 向きへ）
#    ※ Blender +Y を最終正面にするため、顔は +Y 側に作る
# ----------------------------------------------------------------------
FY = 0.13   # 顔面の前方(+Y)オフセット
eyeL = sphere("EyeL", (0.055, FY, 1.76), (0.028, 0.020, 0.030), MAT_EYE, segs=16, rings=12)
eyeR = sphere("EyeR", (-0.055, FY, 1.76), (0.028, 0.020, 0.030), MAT_EYE, segs=16, rings=12)
# 眉（細め・主張しすぎない）
browL = cube("BrowL", (0.058, FY-0.005, 1.795), (0.035, 0.018, 0.008), MAT_HAIR)
browR = cube("BrowR", (-0.058, FY-0.005, 1.795), (0.035, 0.018, 0.008), MAT_HAIR)
# 鼻
nose = sphere("Nose", (0, FY+0.015, 1.72), (0.025, 0.035, 0.030), MAT_SKIN, segs=16, rings=12)
# 口
mouth = cube("Mouth", (0, FY, 1.665), (0.045, 0.012, 0.010), MAT_ACC)

# ----------------------------------------------------------------------
# 4. 髪（頭頂〜後頭部を覆う。前髪あり。ブロック調回避で sphere ベース）
# ----------------------------------------------------------------------
hair = sphere("Hair", (0, -0.01, 1.80), (0.155, 0.16, 0.15), MAT_HAIR, segs=32, rings=24)
# 前髪の房（数本）
for i, x in enumerate((-0.08, -0.03, 0.03, 0.08)):
    spike = cube("Bang%d"%i, (x, FY-0.02, 1.84), (0.022, 0.03, 0.05), MAT_HAIR,
                 rot=(math.radians(20), 0, 0))

# ----------------------------------------------------------------------
# 5. 腕（上腕/前腕/手）— 筋肉感を sphere で。左右。
# ----------------------------------------------------------------------
def arm(side):
    s = 1 if side == 'L' else -1
    x = 0.34 * s
    # 上腕(力こぶ)
    cyl("UpperArm%s"%side, (x, 0, 1.30), 0.085, 0.34, MAT_SKIN, rot=(0, math.radians(8*s), 0))
    sphere("Bicep%s"%side, (x+0.01*s, -0.02, 1.34), (0.09, 0.10, 0.10), MAT_SKIN)
    # 肘
    sphere("Elbow%s"%side, (x+0.04*s, 0, 1.12), (0.07, 0.07, 0.07), MAT_SKIN)
    # 前腕
    cyl("Forearm%s"%side, (x+0.06*s, 0, 0.96), 0.072, 0.32, MAT_SKIN, rot=(0, math.radians(10*s), 0))
    # 手
    sphere("Hand%s"%side, (x+0.09*s, 0, 0.78), (0.075, 0.06, 0.09), MAT_SKIN)
    # リストバンド(アクセント)
    cyl("Cuff%s"%side, (x+0.07*s, 0, 0.86), 0.078, 0.06, MAT_ACC, rot=(0, math.radians(10*s), 0))

arm('L'); arm('R')

# ----------------------------------------------------------------------
# 6. 脚（太もも/ふくらはぎ/ブーツ）— 左右
# ----------------------------------------------------------------------
def leg(side):
    s = 1 if side == 'L' else -1
    x = 0.12 * s
    # 太もも
    cyl("Thigh%s"%side, (x, 0, 0.62), 0.105, 0.42, MAT_SUIT)
    sphere("ThighMass%s"%side, (x, -0.02, 0.66), (0.115, 0.12, 0.16), MAT_SUIT)
    # 膝
    sphere("Knee%s"%side, (x, 0.01, 0.40), (0.085, 0.085, 0.085), MAT_SUIT)
    # ふくらはぎ
    cyl("Shin%s"%side, (x, 0, 0.22), 0.085, 0.36, MAT_SUIT)
    sphere("Calf%s"%side, (x, -0.04, 0.26), (0.09, 0.10, 0.13), MAT_SUIT)
    # ブーツ（足元 Z=0 接地。つま先 +Y 方向）
    boot = cube("Boot%s"%side, (x, 0.04, 0.05), (0.10, 0.17, 0.06), MAT_BOOT)
    sphere("Toe%s"%side, (x, 0.18, 0.045), (0.095, 0.07, 0.05), MAT_BOOT)

leg('L'); leg('R')

# ----------------------------------------------------------------------
# 7. マント（ヒーローらしさ。背面 = -Y 側、肩から膝裏まで）
#    ※ 正面は +Y なので、マントは必ず -Y（背中）に置く
# ----------------------------------------------------------------------
cape = cube("Cape", (0, -0.26, 1.12), (0.33, 0.015, 0.50), MAT_ACC,
            rot=(math.radians(7), 0, 0))
capeclasp = sphere("CapeClasp", (0, -0.16, 1.50), (0.05, 0.05, 0.05), MAT_BELT)

# ----------------------------------------------------------------------
# 8. 全パーツ結合 → subsurf で滑らかに → smooth shade
# ----------------------------------------------------------------------
bpy.ops.object.select_all(action='DESELECT')
for o in parts:
    o.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
hero = bpy.context.active_object
hero.name = "Player"

# subsurf でカクつき除去（ブロック調回避）。
# 軽量化方針（司令塔承認）: subsurf を 1 に抑え、decimate で頂点を間引いて
# Web配信向けに 2MB 以下へ。顔/髪/筋肉のシルエットは保持。
sub = hero.modifiers.new("Subsurf", 'SUBSURF')
sub.levels = 1
sub.render_levels = 1
bpy.ops.object.shade_smooth()
bpy.ops.object.modifier_apply(modifier=sub.name)

# decimate（collapse）で三角形を間引く。0.45 でも丸みのシルエットは十分残る。
dec = hero.modifiers.new("Decimate", 'DECIMATE')
dec.decimate_type = 'COLLAPSE'
dec.ratio = 0.45
bpy.ops.object.modifier_apply(modifier=dec.name)
bpy.ops.object.shade_smooth()

# ----------------------------------------------------------------------
# 9. 原点を足元中心(0,0,0)へ。正面 = +Y。
# ----------------------------------------------------------------------
# いま既に足元 Z=0・中心 XY=0 で作ってあるので原点を 3Dカーソル(原点)に。
bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
hero.location = (0.0, 0.0, 0.0)
hero.rotation_euler = (0.0, 0.0, 0.0)

# ----------------------------------------------------------------------
# 10. glTF Binary 書き出し（Y-up）
# ----------------------------------------------------------------------
out_dir = os.path.join(os.path.dirname(bpy.data.filepath) if bpy.data.filepath else os.getcwd())
# スクリプトはリポジトリ直下の tools/ から動かす前提。models/ へ出力。
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
models_dir = os.path.join(repo_root, "models")
os.makedirs(models_dir, exist_ok=True)
out_path = os.path.join(models_dir, "player.glb")

bpy.ops.object.select_all(action='DESELECT')
hero.select_set(True)
bpy.context.view_layer.objects.active = hero

bpy.ops.export_scene.gltf(
    filepath=out_path,
    export_format='GLB',
    use_selection=True,
    export_yup=True,          # Y-up
    export_apply=True,        # モディファイア適用済みで書き出し
)

# 寸法ログ
dims = hero.dimensions
print("[voxel] export OK ->", out_path)
print("[voxel] dimensions (Blender XYZ, m): %.2f x %.2f x %.2f" % (dims.x, dims.y, dims.z))
print("[voxel] height(Z) ~= %.2f m" % dims.z)
