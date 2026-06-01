# -*- coding: utf-8 -*-
# mob_cow.glb を読み込んで アニメ一覧確認 ＋ 前/横プレビュー
import bpy, os, mathutils
repo = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
glb = os.path.join(repo, "models", "mob_cow.glb")

bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
bpy.ops.import_scene.gltf(filepath=glb)

# アニメ一覧
acts = [a.name for a in bpy.data.actions]
print("[voxel] animations in GLB:", acts)
zs=[]
for o in bpy.context.scene.objects:
    if o.type=='MESH':
        for v in o.bound_box: zs.append((o.matrix_world@mathutils.Vector(v)).z)
print("[voxel] Z range (Blender m): %.3f .. %.3f" % (min(zs), max(zs)))

bpy.ops.object.light_add(type='SUN', location=(4,-6,8)); bpy.context.active_object.data.energy=4.0
bpy.ops.object.light_add(type='SUN', location=(-4,6,4)); bpy.context.active_object.data.energy=1.8
scene = bpy.context.scene
try: scene.render.engine='BLENDER_EEVEE_NEXT'
except Exception: scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=720; scene.render.resolution_y=560
scene.world = scene.world or bpy.data.worlds.new("W")
scene.world.use_nodes=True
scene.world.node_tree.nodes["Background"].inputs[0].default_value=(0.55,0.72,0.95,1)

def shot(name, loc, look=(0,0.1,0.55)):
    bpy.ops.object.camera_add(location=loc)
    cam=bpy.context.active_object
    d=bpy.data.objects.new("E",None); scene.collection.objects.link(d); d.location=look
    c=cam.constraints.new('TRACK_TO'); c.target=d
    scene.camera=cam; scene.render.filepath=os.path.join(repo,"tools",name)
    bpy.ops.render.render(write_still=True)
    print("[voxel] preview ->", scene.render.filepath)

# 正面=+Y(顔側) / 斜め前
shot("preview_mob_front.png", (0.0, 3.4, 0.9))
shot("preview_mob_3q.png",   (2.6, 2.0, 1.1))
