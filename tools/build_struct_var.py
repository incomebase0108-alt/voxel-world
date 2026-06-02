# -*- coding: utf-8 -*-
# VOXEL WORLD - 建物バリエ（大きい建物用・既存パーツの別サイズ/様式を少し）
# Blender 5.1 / headless: blender --background --python tools/build_struct_var.py
#   出力: struct_wall_tall / struct_wall_stone / struct_door_double /
#         struct_window_arch / struct_roof_hip .glb
#   規約: Y-up / 足元中心z=0 / 正面-Z / 1ブロック≒1m / グリッド整合・軽量・アニメ無し。
#   ④軽め：新規量産は最小限。既存 struct_* と混在して大型建築に使う。

import bpy, os, math, mathutils
V=mathutils.Vector

def reset():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for blk in (bpy.data.meshes,bpy.data.materials,bpy.data.objects,bpy.data.actions):
        for it in list(blk):
            try: blk.remove(it)
            except Exception: pass
    parts.clear()

def mat(n,rgb,r=0.7,me=0.0,alpha=1.0):
    m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*rgb,alpha);b.inputs["Roughness"].default_value=r;b.inputs["Metallic"].default_value=me
    if alpha<1.0:
        b.inputs["Alpha"].default_value=alpha
        try: m.blend_method='BLEND'
        except Exception: pass
    return m

parts=[]
def cube(n,loc,s,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.rotation_euler=rot;o.data.materials.append(m);parts.append(o);return o
def cyl(n,loc,r,d,m,verts=16,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d,location=loc)
    o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);parts.append(o);return o

repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."));models=os.path.join(repo,"models");os.makedirs(models,exist_ok=True)
scene=bpy.context.scene

def finish(name, subsurf=0, ratio=0.7, bevel=0.0, flat=False):
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts: o.select_set(True)
    bpy.context.view_layer.objects.active=parts[0]; bpy.ops.object.join()
    o=bpy.context.active_object; o.name=name
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel>0:
        bv=o.modifiers.new("B",'BEVEL'); bv.width=bevel; bv.segments=1; bpy.ops.object.modifier_apply(modifier=bv.name)
    if subsurf:
        s=o.modifiers.new("S",'SUBSURF');s.levels=subsurf;s.render_levels=subsurf
        bpy.ops.object.shade_smooth(); bpy.ops.object.modifier_apply(modifier=s.name)
    if ratio<1.0:
        d=o.modifiers.new("D",'DECIMATE');d.decimate_type='COLLAPSE';d.ratio=ratio; bpy.ops.object.modifier_apply(modifier=d.name)
    if flat: bpy.ops.object.shade_flat()
    else: bpy.ops.object.shade_smooth()
    bpy.context.view_layer.update()
    xs=[(o.matrix_world@V(c)).x for c in o.bound_box]; ys=[(o.matrix_world@V(c)).y for c in o.bound_box]; zs=[(o.matrix_world@V(c)).z for c in o.bound_box]
    scene.cursor.location=((min(xs)+max(xs))/2,(min(ys)+max(ys))/2,min(zs))
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR'); o.location=(0,0,0)
    out=os.path.join(models,name+".glb")
    bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_animations=False)
    sz=os.path.getsize(out)
    print("[voxel] %-18s -> %.3f MB  dims=%.2fx%.2fx%.2f"%(name, sz/1048576, max(xs)-min(xs),max(ys)-min(ys),max(zs)-min(zs)))

def PL(): return mat("Planks",(0.66,0.45,0.26),0.65)
def DW(): return mat("DarkWood",(0.40,0.26,0.14),0.6)
def ST(): return mat("Stone",(0.55,0.55,0.57),0.85)
def ST2(): return mat("Stone2",(0.44,0.44,0.47),0.85)

# ============ struct_wall_tall（1x1x2 板壁・大型建物の1階分を1枚で）============
reset()
p=PL(); d=DW()
cube("Panel",(0,0,1.0),(0.5,0.45,1.0),p)
for x in (-0.5,-0.17,0.17,0.5):
    cube("BeamV",(x,-0.46,1.0),(0.03,0.02,1.0),d)
for z in (0.03,1.0,1.97):
    cube("BeamH",(0,-0.46,z),(0.5,0.02,0.04),d)
finish("struct_wall_tall", bevel=0.01)

# ============ struct_wall_stone（1x1x1 石壁・石造り大型建物用）============
reset()
s=ST(); s2=ST2(); mo=mat("Mortar",(0.35,0.35,0.34),0.9)
cube("Core",(0,0,0.5),(0.5,0.45,0.5),s)
for z in (0.33,0.66):
    cube("Mort",(0,-0.45,z),(0.5,0.02,0.012),mo)
for (x,zz) in [(-0.25,0.16),(0.25,0.16),(0,0.5),(-0.25,0.83),(0.25,0.83)]:
    cube("Blk",(x,-0.46,zz),(0.20,0.01,0.13),s2)
finish("struct_wall_stone", bevel=0.01, flat=True)

# ============ struct_door_double（2幅x2高の両開き大扉・大広間/砦内）============
reset()
p=PL(); d=DW(); IRON=mat("Iron",(0.22,0.22,0.24),0.4,me=0.7)
for sx in (-1,1):
    cube("Leaf",(sx*0.47,0,1.0),(0.45,0.07,1.0),p)         # 扉2枚（各幅~0.9）
    for z in (0.4,1.0,1.6):
        cube("Band",(sx*0.47,-0.075,z),(0.45,0.012,0.05),d)
    cube("Stud",(sx*0.20,-0.10,1.0),(0.03,0.02,0.03),IRON)
cube("Frame",(0,0,2.02),(1.0,0.08,0.06),d)                 # 上枠
for sx in (-1,1):
    cube("FrameS",(sx*0.96,0,1.0),(0.05,0.08,1.0),d)        # 縦枠
cyl("RingL",(-0.12,-0.12,1.0),0.05,0.02,IRON,verts=10,rot=(math.radians(90),0,0))
cyl("RingR",( 0.12,-0.12,1.0),0.05,0.02,IRON,verts=10,rot=(math.radians(90),0,0))
finish("struct_door_double", bevel=0.006)

# ============ struct_window_arch（1x1 アーチ窓・別様式）============
reset()
d=DW(); GL=mat("Glass",(0.62,0.78,0.86),0.1,alpha=0.35)
# 下半分は方形枠、上半分はアーチ
cube("FrBot",(0,0,0.06),(0.5,0.08,0.06),d)
cube("FrL",(-0.46,0,0.45),(0.04,0.08,0.42),d)
cube("FrR",(0.46,0,0.45),(0.04,0.08,0.42),d)
# アーチ（半円）：細い円筒セグメントで縁取り
import math as _m
for i in range(7):
    a=_m.radians(180*i/6); x=_m.cos(a)*0.42; z=0.86+_m.sin(a)*0.10
    cube("ArchSeg",(x,0,z),(0.05,0.08,0.06),d,rot=(0,a,0))
cube("Pane",(0,0.0,0.46),(0.42,0.012,0.42),GL)             # ガラス
cube("MullV",(0,0,0.46),(0.022,0.05,0.42),d)               # 縦桟
finish("struct_window_arch", bevel=0.004)

# ============ struct_roof_hip（寄棟屋根キャップ・1x1四角錐・塔/大型建物の頂部）============
reset()
ROOF=mat("Roof",(0.55,0.22,0.16),0.7)
bpy.ops.mesh.primitive_cone_add(vertices=4,radius1=0.72,radius2=0.0,depth=0.7,location=(0,0,0.35),rotation=(0,0,math.radians(45)))
o=bpy.context.active_object;o.name="Hip";o.data.materials.append(ROOF);parts.append(o)
cube("Eave",(0,0,0.03),(0.52,0.52,0.03),mat("Ridge",(0.45,0.18,0.13),0.7))  # 軒
finish("struct_roof_hip", bevel=0.01, flat=True)

print("[voxel] all building variations done")
