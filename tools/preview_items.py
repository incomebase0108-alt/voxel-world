# -*- coding: utf-8 -*-
# item_*.glb を一列に並べて1枚にレンダ（確認用）
import bpy, os
repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
items=["item_meat","item_egg","item_coin","item_apple"]
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
x=-0.45
for it in items:
    before=set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(repo,"models",it+".glb"))
    for o in set(bpy.context.scene.objects)-before:
        o.location.x += x
    x += 0.30
bpy.ops.object.light_add(type='SUN',location=(2,-4,6)); bpy.context.active_object.data.energy=4.0
bpy.ops.object.light_add(type='SUN',location=(-3,3,3)); bpy.context.active_object.data.energy=1.6
scene=bpy.context.scene
try: scene.render.engine='BLENDER_EEVEE_NEXT'
except Exception: scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=900; scene.render.resolution_y=300
scene.world=scene.world or bpy.data.worlds.new("W"); scene.world.use_nodes=True
scene.world.node_tree.nodes["Background"].inputs[0].default_value=(0.55,0.72,0.95,1)
bpy.ops.object.camera_add(location=(0.0,-1.3,0.5))
cam=bpy.context.active_object
d=bpy.data.objects.new("E",None); scene.collection.objects.link(d); d.location=(0,0,0.05)
cam.constraints.new('TRACK_TO').target=d
scene.camera=cam
scene.render.filepath=os.path.join(repo,"tools","preview_items.png")
bpy.ops.render.render(write_still=True)
print("[voxel] -> tools/preview_items.png")
