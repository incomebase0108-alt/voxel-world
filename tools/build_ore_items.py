# -*- coding: utf-8 -*-
# VOXEL WORLD - 鉱石ドロップ用アイテム（item_*.glb）
# blender --background --python tools/build_ore_items.py
#   出力: models/item_coal.glb / item_iron.glb / item_gold.glb / item_gem.glb
#   ore_*.glb(ブロック)を採掘したときに落ちるドロップ形態。1号機が item_<x>.glb で読む。
#   規約: 既存 item_*（meat/coin等）に合わせ 原点=形状中心 / アニメ無し / 約0.25〜0.3m / 軽量。

import bpy, os, math, mathutils
V=mathutils.Vector

def reset():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for blk in (bpy.data.meshes,bpy.data.materials,bpy.data.objects,bpy.data.actions):
        for it in list(blk):
            try: blk.remove(it)
            except Exception: pass
    parts.clear()

def mat(n,rgb,r=0.5,me=0.0,emis=None):
    m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*rgb,1.0);b.inputs["Roughness"].default_value=r;b.inputs["Metallic"].default_value=me
    if emis is not None:
        b.inputs["Emission Color"].default_value=(*emis,1.0); b.inputs["Emission Strength"].default_value=1.2
    return m

parts=[]
def cube(n,loc,s,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.rotation_euler=rot;o.data.materials.append(m);parts.append(o);return o
def ico(n,loc,s,m,subd=1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subd,location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.data.materials.append(m);parts.append(o);return o
def cone(n,loc,r,d,m,verts=6,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r,radius2=0.0,depth=d,location=loc)
    o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);parts.append(o);return o

repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."));models=os.path.join(repo,"models");os.makedirs(models,exist_ok=True)

def finish(name, subsurf=0, ratio=0.7, bevel=0.0, flat=True):
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts: o.select_set(True)
    bpy.context.view_layer.objects.active=parts[0]; bpy.ops.object.join()
    o=bpy.context.active_object; o.name=name
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel>0:
        bv=o.modifiers.new("B",'BEVEL'); bv.width=bevel; bv.segments=1; bpy.ops.object.modifier_apply(modifier=bv.name)
    if subsurf:
        sm=o.modifiers.new("S",'SUBSURF');sm.levels=subsurf;sm.render_levels=subsurf
        bpy.ops.object.shade_smooth(); bpy.ops.object.modifier_apply(modifier=sm.name)
    if ratio<1.0:
        d=o.modifiers.new("D",'DECIMATE');d.decimate_type='COLLAPSE';d.ratio=ratio; bpy.ops.object.modifier_apply(modifier=d.name)
    if flat: bpy.ops.object.shade_flat()
    else: bpy.ops.object.shade_smooth()
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS'); o.location=(0,0,0)
    bpy.context.view_layer.update()
    zs=[(o.matrix_world@V(c)) for c in o.bound_box]
    dim=max((max(p[i] for p in zs)-min(p[i] for p in zs)) for i in range(3))
    out=os.path.join(models,name+".glb")
    bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_animations=False)
    sz=os.path.getsize(out)
    print("[voxel] %-12s -> %.3f MB  maxdim=%.2fm"%(name, sz/1048576, dim))

# ---- 石炭（黒い塊・角張った岩） ----
reset()
COAL=mat("Coal",(0.09,0.09,0.11),0.55); COAL2=mat("Coal2",(0.14,0.14,0.16),0.5)
ico("Lump",(0,0,0),(0.12,0.10,0.11),COAL,subd=1)
ico("Lump2",(0.06,0.03,0.04),(0.06,0.06,0.05),COAL2,subd=1)
ico("Lump3",(-0.05,-0.04,0.02),(0.05,0.05,0.05),COAL2,subd=1)
finish("item_coal", ratio=0.8, bevel=0.004, flat=True)

# ---- 鉄インゴット（台形の延べ棒・金属） ----
reset()
IRON=mat("Iron",(0.70,0.69,0.66),0.4,me=0.85); IRON2=mat("Iron2",(0.58,0.57,0.55),0.45,me=0.85)
ing=cube("Ingot",(0,0,0),(0.15,0.085,0.055),IRON)
# 上面を内側に絞って台形に
bpy.ops.object.select_all(action='DESELECT'); ing.select_set(True); bpy.context.view_layer.objects.active=ing
me=ing.data
for v in me.vertices:
    if v.co.z>0: v.co.x*=0.7; v.co.y*=0.7
cube("Ridge",(0,0,0.056),(0.10,0.05,0.006),IRON2)
finish("item_iron", ratio=0.9, bevel=0.006, flat=True)

# ---- 金インゴット（同形・金色金属） ----
reset()
GOLD=mat("Gold",(0.93,0.76,0.26),0.3,me=0.95); GOLD2=mat("Gold2",(0.82,0.64,0.16),0.35,me=0.95)
ing=cube("Ingot",(0,0,0),(0.15,0.085,0.055),GOLD)
bpy.ops.object.select_all(action='DESELECT'); ing.select_set(True); bpy.context.view_layer.objects.active=ing
me=ing.data
for v in me.vertices:
    if v.co.z>0: v.co.x*=0.7; v.co.y*=0.7
cube("Ridge",(0,0,0.056),(0.10,0.05,0.006),GOLD2)
finish("item_gold", ratio=0.9, bevel=0.006, flat=True)

# ---- 宝石（カット水晶・八面体＋淡発光） ----
reset()
GEM=mat("Gem",(0.38,0.85,0.95),0.12,emis=(0.18,0.5,0.6)); GEM2=mat("Gem2",(0.28,0.72,0.88),0.12)
cone("Top",(0,0,0.05),0.10,0.13,GEM,verts=6)                       # 上の尖り
cone("Bot",(0,0,-0.04),0.10,0.10,GEM2,verts=6,rot=(math.radians(180),0,0))  # 下の尖り（八面体）
finish("item_gem", ratio=0.95, bevel=0.0, flat=True)

print("[voxel] all ore-drop items done")
