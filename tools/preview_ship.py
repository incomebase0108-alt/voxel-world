# -*- coding: utf-8 -*-
# 船を3/4側面から一列プレビュー（長辺Yを見せる）。各船のZレンジも表示。
import bpy, os, mathutils
V=mathutils.Vector
repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
NAMES=os.environ.get("SHIPS","ship_rowboat,ship_sailboat,ship_wreck").split(",")
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
x=0.0; gap=7.0
for n in NAMES:
    glb=os.path.join(repo,"models",n+".glb")
    if not os.path.exists(glb): continue
    before=set(bpy.context.scene.objects); bpy.ops.import_scene.gltf(filepath=glb)
    new=[o for o in bpy.context.scene.objects if o not in before]
    for o in new:
        if o.animation_data: o.animation_data_clear()
    zs=[(o.matrix_world@V(c)).z for o in new if o.type=='MESH' for c in o.bound_box]
    print("[voxel] %-16s Z: %.3f .. %.3f"%(n, min(zs) if zs else 0, max(zs) if zs else 0))
    for r in [o for o in new if o.parent is None]: r.location.x+=x
    x+=gap
bpy.ops.object.light_add(type='SUN',location=(6,-6,10)); bpy.context.active_object.data.energy=4.0
bpy.ops.object.light_add(type='SUN',location=(-5,6,5)); bpy.context.active_object.data.energy=1.8
scene=bpy.context.scene
try: scene.render.engine='BLENDER_EEVEE_NEXT'
except Exception: scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=1300; scene.render.resolution_y=520
scene.world=scene.world or bpy.data.worlds.new("W"); scene.world.use_nodes=True
scene.world.node_tree.nodes["Background"].inputs[0].default_value=(0.45,0.62,0.85,1)
cx=(x-gap)/2.0
bpy.ops.object.camera_add(location=(cx+7.0, -20.0, 9.0)); cam=bpy.context.active_object   # 3/4側面・引き
d=bpy.data.objects.new("E",None); scene.collection.objects.link(d); d.location=(cx,0,1.0)
c=cam.constraints.new('TRACK_TO'); c.target=d
scene.camera=cam; scene.render.filepath=os.path.join(repo,"tools","preview_ship_row.png")
bpy.ops.render.render(write_still=True); print("[voxel] preview ->", scene.render.filepath)
