# -*- coding: utf-8 -*-
# item装備を一列に並べて1枚プレビュー（原点=握り/中心。z=0を跨ぐので各々を持ち上げて表示）
import bpy, os, mathutils
V=mathutils.Vector
repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
NAMES=os.environ.get("EQUIP","item_sword,item_pickaxe,item_axe,item_bow,item_shield,item_armor").split(",")
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
x=0.0; gap=1.1
for n in NAMES:
    glb=os.path.join(repo,"models",n+".glb")
    if not os.path.exists(glb): continue
    before=set(bpy.context.scene.objects); bpy.ops.import_scene.gltf(filepath=glb)
    new=[o for o in bpy.context.scene.objects if o not in before]
    for o in new:
        if o.animation_data: o.animation_data_clear()
    zs=[(o.matrix_world@V(c)).z for o in new if o.type=='MESH' for c in o.bound_box]
    print("[voxel] %-14s origin->Z: %.3f .. %.3f"%(n, min(zs) if zs else 0, max(zs) if zs else 0))
    roots=[o for o in new if o.parent is None]
    minz=min(zs) if zs else 0
    for r in roots: r.location.x+=x; r.location.z-=minz   # 表示用に足元を0へ
    x+=gap
bpy.ops.object.light_add(type='SUN',location=(4,-6,10)); bpy.context.active_object.data.energy=4.0
bpy.ops.object.light_add(type='SUN',location=(-4,6,5)); bpy.context.active_object.data.energy=2.0
scene=bpy.context.scene
try: scene.render.engine='BLENDER_EEVEE_NEXT'
except Exception: scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=1280; scene.render.resolution_y=560
scene.world=scene.world or bpy.data.worlds.new("W"); scene.world.use_nodes=True
scene.world.node_tree.nodes["Background"].inputs[0].default_value=(0.55,0.72,0.95,1)
cx=(x-gap)/2.0
bpy.ops.object.camera_add(location=(cx,9.5,1.3)); cam=bpy.context.active_object
d=bpy.data.objects.new("E",None); scene.collection.objects.link(d); d.location=(cx,0,0.55)
c=cam.constraints.new('TRACK_TO'); c.target=d
scene.camera=cam; scene.render.filepath=os.path.join(repo,"tools","preview_equip_row.png")
bpy.ops.render.render(write_still=True); print("[voxel] preview ->", scene.render.filepath)
