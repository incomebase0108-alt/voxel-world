# -*- coding: utf-8 -*-
# player.glb を読み込んで前/横からプレビューPNGを書き出す（目視確認用）
# 注意: glTF(Y-up)をimportするとBlenderはZ-upへ戻す。
#       正面(glTF -Z)はBlenderでは +Y を向く。高さは Z 0..~1.95。
import bpy, os

repo = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
glb = os.path.join(repo, "models", "player.glb")

bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
bpy.ops.import_scene.gltf(filepath=glb)

# import後のZ範囲を確認（足元0か）
zs = []
for o in bpy.context.scene.objects:
    if o.type == 'MESH':
        for v in o.bound_box:
            zs.append((o.matrix_world @ __import__('mathutils').Vector(v)).z)
print("[voxel] Z range (Blender, m): %.3f .. %.3f" % (min(zs), max(zs)))

bpy.ops.object.light_add(type='SUN', location=(4,-6,8))
bpy.context.active_object.data.energy = 4.0
bpy.ops.object.light_add(type='SUN', location=(-4,6,4))
bpy.context.active_object.data.energy = 1.8

scene = bpy.context.scene
try:
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
except Exception:
    scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 600
scene.render.resolution_y = 820
scene.world = bpy.data.worlds.new("W") if not scene.world else scene.world
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.55,0.72,0.95,1)

def shot(name, loc, look_at=(0,0,0.95)):
    bpy.ops.object.camera_add(location=loc)
    cam = bpy.context.active_object
    d = bpy.data.objects.new("Empty", None); scene.collection.objects.link(d)
    d.location = look_at
    c = cam.constraints.new('TRACK_TO'); c.target = d
    scene.camera = cam
    scene.render.filepath = os.path.join(repo, "tools", name)
    bpy.ops.render.render(write_still=True)
    print("[voxel] preview ->", scene.render.filepath)

# 正面=+Y を向くので、前から見る=+Y側にカメラ。横=+X側。
shot("preview_front.png", (0.0, 4.2, 1.05))
shot("preview_side.png",  (4.2, 0.6, 1.05))
