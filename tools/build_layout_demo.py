# -*- coding: utf-8 -*-
# VOXEL WORLD - 構造物の配置見本シーンを実パーツから組んでレンダ（1号機②自動生成の見本）
# Blender 5.1 / headless: blender --background --python tools/build_layout_demo.py
#   models/struct_*.glb を実際にグリッド配置して「5×5コテージ＋井戸＋柵」と
#   「7×7ダンジョン部屋」を組み立て、俯瞰レンダを tools/ に出力。
#   ここで使う PLACE 配列の座標は models/LAYOUT.md の表と一致させること（仕様の実体）。
#   グリッド規約: 1セル=1m。配置座標=セル中心の床(地面 y=0)。front(装飾面)はモデルの -Z(glTF)。
#   yaw(度,Z回り,CCW): 0=front北(+Y) / 90=front西(-X) / 180=front南(-Y) / 270=front東(+X)。

import bpy, os, math, mathutils
V=mathutils.Vector
repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
MODELS=os.path.join(repo,"models")

bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)

def place(model, gx, gy, level, yaw=0.0, scale=(1,1,1)):
    """struct_*.glb を1個 import し (gx,gy,level) に yaw 回転・scale で配置。"""
    glb=os.path.join(MODELS,model+".glb")
    before=set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=glb)
    new=[o for o in bpy.context.scene.objects if o not in before]
    for o in new:
        if o.animation_data: o.animation_data_clear()   # 静止配置（NLA解除で回転自由）
    roots=[o for o in new if o.parent is None]
    for r in roots:
        r.rotation_mode='XYZ'
        r.location=(gx, gy, level)
        r.rotation_euler[2]=math.radians(yaw)
        r.scale=scale
    return roots

# ===== 5×5 コテージ（X,Y ∈ 0..4、壁2段=level0/1、屋根 level2）=====
HOUSE=[]
# 南壁(Y=0, front南=yaw180)：X=2はドア、X=1/3の上段(level1)は窓
for x in (0,1,3,4):
    HOUSE.append(("struct_wall",x,0,0,180))
for x in (0,4):
    HOUSE.append(("struct_wall",x,0,1,180))
HOUSE.append(("struct_window",1,0,1,180)); HOUSE.append(("struct_wall",1,0,0,180))
HOUSE.append(("struct_window",3,0,1,180)); HOUSE.append(("struct_wall",3,0,0,180))
HOUSE.append(("struct_door",2,0,0,180))     # 2m・level0基準で上に伸びる
# 北壁(Y=4, front北=yaw0)：X=2上段に窓
for x in (0,1,2,3,4):
    HOUSE.append(("struct_wall",x,4,0,0))
for x in (0,1,3,4):
    HOUSE.append(("struct_wall",x,4,1,0))
HOUSE.append(("struct_window",2,4,1,0))
# 西壁(X=0, front西=yaw90) / 東壁(X=4, front東=yaw270) ：Y=1..3、2段
for y in (1,2,3):
    HOUSE.append(("struct_wall",0,y,0,90)); HOUSE.append(("struct_wall",0,y,1,90))
    HOUSE.append(("struct_wall",4,y,0,270)); HOUSE.append(("struct_wall",4,y,1,270))
for m,gx,gy,lv,yaw in HOUSE: place(m,gx,gy,lv,yaw)

# 切妻屋根(level2)：ridgeはX方向(東西)。各面は roof piece を Y方向2倍にして1枚で葺く。
#   南面=Y=1中心(Y0-2を覆う,yaw180,棟側が高い) / 北面=Y=3中心(Y2-4,yaw0)。棟 Y=2 で交わる。
for x in range(5):
    place("struct_roof", x, 1.0, 2.0, 180, scale=(1,2,1))
    place("struct_roof", x, 3.0, 2.0, 0,   scale=(1,2,1))

# 庭：井戸(2x2なので中心を X=7.5,Y=2.5 付近) と 柵(南の生垣)
place("struct_well", 7.5, 2.0, 0, 0)
for x in (6,7,8,9):
    place("struct_fence", x, -1.0, 0, 0)
for y in (0,1,2):
    place("struct_fence", 5.5, y, 0, 90)

# ===== ダンジョン部屋（X∈12..18, Y∈0..6 の7×7。中央スポナー・隅宝箱・壁松明・奥祭壇）=====
DX=15  # 部屋中心X
place("struct_spawner", DX, 3, 0, 0)            # 中央スポナー
place("struct_chest", DX-2.5, 0.6, 0, 0)        # 入口寄りの宝箱
place("struct_chest", DX+2.5, 5.4, 0, 200)      # 奥の宝箱（少し振る）
place("struct_altar", DX, 5.6, 0, 0)            # 奥の祭壇
for (tx,ty,tyaw) in [(DX-3,1,90),(DX-3,5,90),(DX+3,1,270),(DX+3,5,270)]:
    place("struct_torch", tx, ty, 0, tyaw)      # 四隅付近の壁松明

# ===== 砦（角に塔・辺に城壁2段＋狭間・南に門・塔に旗）X∈22..28 付近 =====
FX=25  # 砦中心X
# 4隅の塔（2x2）
for (tx,ty) in [(FX-3,0),(FX+3,0),(FX-3,6),(FX+3,6)]:
    place("fort_tower", tx, ty, 0, 0)
    place("fort_flag", tx, ty, 3.64, 0)               # 塔頂に旗
# 城壁（辺・各2段＋天端に狭間）。yaw=外向き
def wall_run(cells, yaw):
    for (x,y) in cells:
        place("fort_wall", x, y, 0, yaw); place("fort_wall", x, y, 1, yaw)
        place("fort_battlement", x, y, 2, yaw)
wall_run([(FX-1,0),(FX+1,0)], 180)                    # 南辺（中央 FX,0 は門）
wall_run([(FX-2,6),(FX,6),(FX+2,6)], 0)               # 北辺
wall_run([(FX-3,2),(FX-3,4)], 90)                     # 西辺
wall_run([(FX+3,2),(FX+3,4)], 270)                    # 東辺
place("fort_gate", FX, 0, 0, 180)                     # 南の門

# ===== ライティング/カメラ/レンダ =====
bpy.ops.object.light_add(type='SUN', location=(6,-10,16)); bpy.context.active_object.data.energy=4.2
bpy.ops.object.light_add(type='SUN', location=(-6,8,8)); bpy.context.active_object.data.energy=1.6
scene=bpy.context.scene
try: scene.render.engine='BLENDER_EEVEE_NEXT'
except Exception: scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=1400; scene.render.resolution_y=720
scene.world=scene.world or bpy.data.worlds.new("W"); scene.world.use_nodes=True
scene.world.node_tree.nodes["Background"].inputs[0].default_value=(0.56,0.73,0.95,1)

def shot(name, loc, look):
    bpy.ops.object.camera_add(location=loc); cam=bpy.context.active_object
    d=bpy.data.objects.new("E",None); scene.collection.objects.link(d); d.location=look
    c=cam.constraints.new('TRACK_TO'); c.target=d
    scene.camera=cam; scene.render.filepath=os.path.join(repo,"tools",name)
    bpy.ops.render.render(write_still=True); print("[voxel] ->", scene.render.filepath)

# コテージ俯瞰
shot("layout_cottage.png", (3.5, -11.0, 8.5), (2.0, 2.0, 1.3))
# ダンジョン部屋俯瞰
shot("layout_dungeon.png", (DX, -7.0, 7.5), (DX, 3.0, 0.6))
# 砦俯瞰
shot("layout_fort.png", (FX, -11.0, 8.0), (FX, 3.0, 1.4))
# 全景
shot("layout_overview.png", (8.0, -16.0, 13.0), (8.0, 2.0, 0.8))
print("[voxel] layout demo done")
