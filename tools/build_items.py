# -*- coding: utf-8 -*-
# VOXEL WORLD - アイテム/ドロップ小物（item_*.glb）
# Blender 5.1 / headless: blender --background --python tools/build_items.py
#   出力: models/item_meat.glb / item_egg.glb / item_coin.glb / item_apple.glb
#   アニメ無し・ごく軽量。Y-up、原点=中心（ドロップ回転表示しやすいよう）。サイズ目安 約0.3m。
#   1号機のインベントリ/ドロップに使用。

import bpy, os, math, mathutils

def reset():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for blk in (bpy.data.meshes,bpy.data.materials,bpy.data.objects,bpy.data.actions):
        for it in list(blk):
            try: blk.remove(it)
            except Exception: pass
    parts.clear()   # 前アイテムの（削除済み）参照を捨てる

def mat(n,rgb,r=0.5,me=0.0):
    m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*rgb,1.0);b.inputs["Roughness"].default_value=r;b.inputs["Metallic"].default_value=me;return m

parts=[]
def sphere(n,loc,s,m,segs=16,rings=10):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs,ring_count=rings,location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.data.materials.append(m);parts.append(o);return o
def cyl(n,loc,r,d,m,verts=20,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d,location=loc)
    o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);parts.append(o);return o
def cube(n,loc,s,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.rotation_euler=rot;o.data.materials.append(m);parts.append(o);return o

repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."));models=os.path.join(repo,"models");os.makedirs(models,exist_ok=True)

def finish(name, subsurf=1, ratio=0.6, center=True):
    """parts を結合→subsurf/decimate→原点中心→GLB書き出し"""
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts: o.select_set(True)
    bpy.context.view_layer.objects.active=parts[0]; bpy.ops.object.join()
    o=bpy.context.active_object; o.name=name
    if subsurf:
        s=o.modifiers.new("S",'SUBSURF');s.levels=subsurf;s.render_levels=subsurf
        bpy.ops.object.shade_smooth();bpy.ops.object.modifier_apply(modifier=s.name)
    d=o.modifiers.new("D",'DECIMATE');d.decimate_type='COLLAPSE';d.ratio=ratio
    bpy.ops.object.modifier_apply(modifier=d.name);bpy.ops.object.shade_smooth()
    # 原点を形状中心に
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    o.location=(0,0,0)
    out=os.path.join(models,name+".glb")
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
    bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_animations=False)
    sz=os.path.getsize(out)
    print("[voxel] %s -> %.3f MB (%d B)"%(name, sz/1048576, sz))

# ---- 肉（ドラムスティック：茶の肉＋白い骨）----
reset()
M_MEAT=mat("Meat",(0.62,0.30,0.18),0.55); M_BONE=mat("Bone",(0.93,0.90,0.82),0.4)
sphere("Flesh",(0,0.04,0),(0.11,0.13,0.11),M_MEAT)
cyl("BoneShaft",(0,-0.13,0),0.025,0.14,M_BONE,rot=(math.radians(90),0,0))
sphere("Knob1",(0.025,-0.20,0.02),(0.035,0.035,0.035),M_BONE,segs=10,rings=8)
sphere("Knob2",(-0.025,-0.20,-0.02),(0.035,0.035,0.035),M_BONE,segs=10,rings=8)
finish("item_meat")

# ---- 卵 ----
reset()
M_EGG=mat("Egg",(0.96,0.93,0.86),0.35)
sphere("Egg",(0,0,0),(0.08,0.08,0.11),M_EGG,segs=18,rings=12)  # 縦長
finish("item_egg", ratio=0.7)

# ---- コイン（金の円盤・面に窪み）----
reset()
M_GOLD=mat("Gold",(0.95,0.78,0.20),0.25,0.9); M_GOLD2=mat("Gold2",(0.80,0.62,0.12),0.3,0.9)
cyl("Coin",(0,0,0),0.11,0.03,M_GOLD,verts=28)
cyl("Face",(0,0,0.016),0.075,0.012,M_GOLD2,verts=24)  # 浮き彫り風
finish("item_coin", subsurf=0, ratio=0.8)

# ---- りんご（赤い実＋茶の軸＋緑の葉）----
reset()
M_APPLE=mat("Apple",(0.82,0.13,0.12),0.35); M_STEM=mat("Stem",(0.36,0.24,0.12),0.7); M_LEAF=mat("Leaf",(0.30,0.62,0.22),0.6)
sphere("Apple",(0,0,0),(0.10,0.10,0.095),M_APPLE,segs=18,rings=12)
cyl("Stem",(0,0,0.10),0.012,0.06,M_STEM,verts=8)
sphere("Leaf",(0.05,0.02,0.11),(0.04,0.02,0.012),M_LEAF,segs=8,rings=6)
finish("item_apple")

print("[voxel] all items done")
