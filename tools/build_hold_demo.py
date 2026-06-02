# -*- coding: utf-8 -*-
# VOXEL WORLD - 装備の手持ち表示 見本レンダ＋グリップ仕様（1号機の将来の装備システム向け）
# Blender 5.1 / headless: blender --background --python tools/build_hold_demo.py
#   player.glb の手に武器glbを持たせてレンダ。tools/hold_*.png 出力。
#   手先実測（player.glb・Blenderワールド m, 正面+Y）:
#     右手 HAND_R=(-0.39,-0.02,0.70) / 左手 HAND_L=(0.39,-0.02,0.70)
#   武器origin（=握り）を手先に置き、GRIP回転を与える。値は EQUIP_HOLD.md と一致。

import bpy, os, math, mathutils
V=mathutils.Vector
repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
MODELS=os.path.join(repo,"models")
HAND_R=V((-0.37,0.0,0.73)); HAND_L=V((0.37,0.0,0.73))   # ヒーロー版player再計測

# 武器ごとの手持ち仕様：(手, 位置=手先からの微調整, 回転euler度)
# 回転は Blender(Z-up,正面+Y)。剣/ピッケル/斧=握り基部が手・刃/頭が上前方、弓/盾=握り中央/中心。
HOLD={
 "item_sword":   ("R", V((0,0,0)),        (-18, 0, 0)),   # 刃を上前方へ少し倒す
 "item_pickaxe": ("R", V((0,0,0)),        (-12, 0, 0)),
 "item_axe":     ("R", V((0,0,0)),        (-12, 0, 0)),
 "item_bow":     ("L", V((0,0.04,0.05)),  (8,  0, 0)),    # 弓は握り中央を左手・やや前
 "item_shield":  ("L", V((0.02,0.16,0.32)),(0, 0, 0)),   # 盾は左前腕・正面+Y外向き
}

def clear():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for blk in (bpy.data.meshes,bpy.data.objects,bpy.data.actions):
        for it in list(blk):
            try: blk.remove(it)
            except Exception: pass

def load(name):
    before=set(bpy.context.scene.objects); bpy.ops.import_scene.gltf(filepath=os.path.join(MODELS,name+".glb"))
    new=[o for o in bpy.context.scene.objects if o not in before]
    for o in new:
        if o.animation_data: o.animation_data_clear()
    return [o for o in new if o.parent is None]

def attach(weapon):
    hand_s, off, rot = HOLD[weapon]
    hand = HAND_R if hand_s=="R" else HAND_L
    roots=load(weapon)
    for r in roots:
        r.rotation_mode='XYZ'
        r.location = hand+off
        r.rotation_euler = [math.radians(d) for d in rot]
    return roots

scene=bpy.context.scene
try: scene.render.engine='BLENDER_EEVEE_NEXT'
except Exception: scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=560; scene.render.resolution_y=780
scene.world=scene.world or bpy.data.worlds.new("W"); scene.world.use_nodes=True
scene.world.node_tree.nodes["Background"].inputs[0].default_value=(0.55,0.72,0.95,1)

def setup_lights():
    bpy.ops.object.light_add(type='SUN', location=(4,-6,8)); bpy.context.active_object.data.energy=4.2
    bpy.ops.object.light_add(type='SUN', location=(-5,5,4)); bpy.context.active_object.data.energy=1.8

def shot(name, loc, look=(0,0.1,1.0)):
    bpy.ops.object.camera_add(location=loc); cam=bpy.context.active_object
    d=bpy.data.objects.new("E",None); scene.collection.objects.link(d); d.location=look
    c=cam.constraints.new('TRACK_TO'); c.target=d
    scene.camera=cam; scene.render.filepath=os.path.join(repo,"tools",name)
    bpy.ops.render.render(write_still=True); print("[voxel] ->", name)

def scene_with(weapons, tag):
    clear(); setup_lights(); load("player")
    for w in weapons: attach(w)
    shot("hold_%s_front.png"%tag, (0.0, 4.2, 1.3))
    shot("hold_%s_3q.png"%tag,   (-3.0, 3.0, 1.6))   # 右手側(-X)から見る前斜め

scene_with(["item_sword"], "sword")
scene_with(["item_pickaxe"], "pickaxe")
scene_with(["item_axe"], "axe")
scene_with(["item_bow"], "bow")
scene_with(["item_sword","item_shield"], "hero")   # 剣＋盾のヒーロー立ち
print("[voxel] hold demo done")
