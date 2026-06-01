# -*- coding: utf-8 -*-
# 指定モデルの指定クリップを指定フレームでポーズして描画（attack等の検証用）
#   例: MODEL=player CLIP=attack FRAME=9 blender -b --python tools/preview_anim.py
import bpy, os, mathutils
repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
MODEL=os.environ.get("MODEL","player"); CLIP=os.environ.get("CLIP","attack"); FRAME=int(os.environ.get("FRAME","9"))
glb=os.path.join(repo,"models",MODEL+".glb")

bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
bpy.ops.import_scene.gltf(filepath=glb)

# 指定クリップのNLAトラックだけ有効化
for o in bpy.context.scene.objects:
    if o.animation_data:
        for trk in o.animation_data.nla_tracks:
            trk.mute = (trk.name != CLIP)
bpy.context.scene.frame_set(FRAME)
bpy.context.view_layer.update()

bpy.ops.object.light_add(type='SUN',location=(4,-6,8)); bpy.context.active_object.data.energy=4.0
bpy.ops.object.light_add(type='SUN',location=(-4,6,4)); bpy.context.active_object.data.energy=1.8
scene=bpy.context.scene
try: scene.render.engine='BLENDER_EEVEE_NEXT'
except Exception: scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=640; scene.render.resolution_y=760
scene.world=scene.world or bpy.data.worlds.new("W"); scene.world.use_nodes=True
scene.world.node_tree.nodes["Background"].inputs[0].default_value=(0.55,0.72,0.95,1)

# 高さ把握
zs=[]
for o in scene.objects:
    if o.type=='MESH':
        for v in o.bound_box: zs.append((o.matrix_world@mathutils.Vector(v)).z)
zmax=max(zs)
def shot(name,loc,look):
    bpy.ops.object.camera_add(location=loc); cam=bpy.context.active_object
    d=bpy.data.objects.new("E",None); scene.collection.objects.link(d); d.location=look
    c=cam.constraints.new('TRACK_TO'); c.target=d
    scene.camera=cam; scene.render.filepath=os.path.join(repo,"tools",name)
    bpy.ops.render.render(write_still=True); print("[voxel] ->",scene.render.filepath)
look=(0,0,zmax*0.55)
shot("anim_%s_%s_side.png"%(MODEL,CLIP), (zmax*2.4, zmax*0.9, zmax*0.6), look)  # 横（突きの前後が分かる）
shot("anim_%s_%s_3q.png"%(MODEL,CLIP),   (zmax*1.8, zmax*1.6, zmax*0.7), look)
print("[voxel] posed", MODEL, CLIP, "frame", FRAME)
