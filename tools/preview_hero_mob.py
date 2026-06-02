# -*- coding: utf-8 -*-
# 敵モブの迫力プレビュー（近接・暗めの背景で発光部を映える描画）。MOB環境変数で指定。
import bpy, os, mathutils
V=mathutils.Vector
repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
MOB=os.environ.get("MOB","mob_golem")
glb=os.path.join(repo,"models",MOB+".glb")
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
bpy.ops.import_scene.gltf(filepath=glb)
for o in list(bpy.context.scene.objects):
    if o.animation_data:
        o.animation_data.action=None
        for t in o.animation_data.nla_tracks: t.mute=True   # rest立ち姿
zs=[(o.matrix_world@V(v)).z for o in bpy.context.scene.objects if o.type=='MESH' for v in o.bound_box]
zmax=max(zs)
scene=bpy.context.scene
try:
    scene.render.engine='BLENDER_EEVEE_NEXT'
except Exception:
    scene.render.engine='BLENDER_EEVEE'
try: scene.eevee.use_bloom=True; scene.eevee.bloom_intensity=0.06
except Exception: pass
scene.render.resolution_x=640; scene.render.resolution_y=860
scene.world=scene.world or bpy.data.worlds.new("W"); scene.world.use_nodes=True
scene.world.node_tree.nodes["Background"].inputs[0].default_value=(0.10,0.11,0.14,1)  # 暗い背景
bpy.ops.object.light_add(type='SUN',location=(5,-6,9)); bpy.context.active_object.data.energy=2.6
bpy.ops.object.light_add(type='SUN',location=(-5,5,4)); bpy.context.active_object.data.energy=1.0
look=(0,0.05,zmax*0.52)
def shot(name,loc):
    bpy.ops.object.camera_add(location=loc); cam=bpy.context.active_object
    d=bpy.data.objects.new("E",None); scene.collection.objects.link(d); d.location=look
    c=cam.constraints.new('TRACK_TO'); c.target=d
    scene.camera=cam; scene.render.filepath=os.path.join(repo,"tools",name)
    bpy.ops.render.render(write_still=True); print("[voxel] ->",name)
shot("hero_%s_front.png"%MOB,(0.0, zmax*1.7, zmax*0.55))
shot("hero_%s_3q.png"%MOB,  (zmax*1.25, zmax*1.15, zmax*0.62))
print("[voxel] hero mob preview done")
