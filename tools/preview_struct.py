# -*- coding: utf-8 -*-
# struct_*.glb を一列に並べて1枚にプレビュー＋各Zレンジ（足元z=0確認用）
import bpy, os, mathutils
repo = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
NAMES = os.environ.get("STRUCTS","struct_wall,struct_roof,struct_door,struct_window,struct_fence,struct_well").split(",")

bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
x=0.0; gap=1.6; placed=[]
for n in NAMES:
    glb=os.path.join(repo,"models",n+".glb")
    if not os.path.exists(glb): continue
    before=set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=glb)
    new=[o for o in bpy.context.scene.objects if o not in before]
    for o in new:
        if o.animation_data: o.animation_data_clear()
    # Zレンジ
    zs=[];
    for o in new:
        if o.type=='MESH':
            for v in o.bound_box: zs.append((o.matrix_world@mathutils.Vector(v)).z)
    print("[voxel] %-16s Z: %.3f .. %.3f"%(n, min(zs) if zs else 0, max(zs) if zs else 0))
    # 並べる：ルート空ノード or 最上位を移動
    roots=[o for o in new if o.parent is None]
    for r in roots: r.location.x += x
    placed+= new; x+=gap

bpy.ops.object.light_add(type='SUN', location=(4,-6,10)); bpy.context.active_object.data.energy=4.0
bpy.ops.object.light_add(type='SUN', location=(-4,6,5)); bpy.context.active_object.data.energy=1.8
scene=bpy.context.scene
try: scene.render.engine='BLENDER_EEVEE_NEXT'
except Exception: scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=1280; scene.render.resolution_y=540
scene.world=scene.world or bpy.data.worlds.new("W"); scene.world.use_nodes=True
scene.world.node_tree.nodes["Background"].inputs[0].default_value=(0.55,0.72,0.95,1)
cx=(x-gap)/2.0
bpy.ops.object.camera_add(location=(cx, 14.0, 4.0)); cam=bpy.context.active_object
d=bpy.data.objects.new("E",None); scene.collection.objects.link(d); d.location=(cx,0,1.0)
c=cam.constraints.new('TRACK_TO'); c.target=d
scene.camera=cam; scene.render.filepath=os.path.join(repo,"tools","preview_struct_row.png")
bpy.ops.render.render(write_still=True)
print("[voxel] preview ->", scene.render.filepath)
