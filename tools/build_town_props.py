# -*- coding: utf-8 -*-
# VOXEL WORLD - 町の生活小物（村/町を「生きている」感じに）
# blender --background --python tools/build_town_props.py
#   出力: prop_stall/bench/sign/lamp/brazier/cart/barrel/crate/laundry .glb
#   規約: Y-up / 足元中心z=0 / 正面 -Z / 1ブロック≒1m / グリッド準拠・軽量・アニメ無し。
#   ※街灯/篝火は発光(Emission)。1号機が村/町に装飾配置。
#   prop_brazier/lamp の炎は微発光。井戸は既存 struct_well を流用、ここは洗い場(washtub)等。

import bpy, os, math, mathutils
V=mathutils.Vector

def reset():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for blk in (bpy.data.meshes,bpy.data.materials,bpy.data.objects,bpy.data.actions):
        for it in list(blk):
            try: blk.remove(it)
            except Exception: pass
    parts.clear()

def mat(n,rgb,r=0.7,me=0.0,emis=None):
    m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*rgb,1.0);b.inputs["Roughness"].default_value=r;b.inputs["Metallic"].default_value=me
    if emis is not None:
        b.inputs["Emission Color"].default_value=(*emis,1.0); b.inputs["Emission Strength"].default_value=2.5
    return m

parts=[]
def cube(n,loc,s,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.rotation_euler=rot;o.data.materials.append(m);parts.append(o);return o
def cyl(n,loc,r,d,m,verts=14,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d,location=loc)
    o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);parts.append(o);return o
def cone(n,loc,r,d,m,verts=12,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r,radius2=0.0,depth=d,location=loc)
    o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);parts.append(o);return o

repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."));models=os.path.join(repo,"models");os.makedirs(models,exist_ok=True)
scene=bpy.context.scene

def finish(name, subsurf=0, ratio=0.7, bevel=0.008, flat=False):
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
    bpy.context.view_layer.update()
    xs=[(o.matrix_world@V(c)).x for c in o.bound_box]; ys=[(o.matrix_world@V(c)).y for c in o.bound_box]; zs=[(o.matrix_world@V(c)).z for c in o.bound_box]
    scene.cursor.location=((min(xs)+max(xs))/2,(min(ys)+max(ys))/2,min(zs))
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR'); o.location=(0,0,0)
    out=os.path.join(models,name+".glb")
    bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_animations=False)
    sz=os.path.getsize(out)
    print("[voxel] %-14s -> %.3f MB  dims=%.2fx%.2fx%.2f"%(name, sz/1048576, max(xs)-min(xs),max(ys)-min(ys),max(zs)-min(zs)))

def WOOD(): return mat("Wood",(0.52,0.36,0.19),0.7)
def WOOD2(): return mat("Wood2",(0.40,0.27,0.14),0.7)
def IRON(): return mat("Iron",(0.26,0.26,0.28),0.45,me=0.7)
def ROPE(): return mat("Rope",(0.66,0.56,0.36),0.85)
def CLOTH(rgb): return mat("Cloth",rgb,0.8)

# ============ prop_stall（屋台・カウンター＋柱＋縞の天幕）============
reset()
W=WOOD(); W2=WOOD2(); RED=CLOTH((0.72,0.24,0.20)); WH=CLOTH((0.90,0.88,0.82))
cube("Counter",(0,-0.1,0.78),(0.85,0.40,0.06),W)           # 天板
cube("Front",(0,-0.48,0.40),(0.85,0.05,0.40),W2)           # 前板
for x in (-0.8,0.8):
    cube("Post",(x,0.35,1.1),(0.05,0.05,1.1),W2)            # 後柱
    cube("PostF",(x,-0.45,0.4),(0.05,0.05,0.4),W2)          # 前脚
# 天幕（前下がり・赤白縞）
for i,x in enumerate([-0.6,-0.2,0.2,0.6]):
    c = RED if i%2==0 else WH
    cube("Awn",(x,-0.05,1.65),(0.21,0.6,0.03),c,rot=(math.radians(-18),0,0))
cube("Ridge",(0,0.36,1.95),(0.9,0.04,0.04),W2)
# 商品（箱と果物）
cube("Box",(-0.4,-0.1,0.86),(0.12,0.12,0.06),W2)
cyl("Fruit",(0.3,-0.1,0.85),0.06,0.05,mat("Fruit",(0.80,0.30,0.20)),verts=10)
finish("prop_stall", ratio=0.7)

# ============ prop_bench（ベンチ）============
reset()
W=WOOD(); W2=WOOD2()
cube("Seat",(0,0,0.45),(0.7,0.20,0.04),W)
cube("Back",(0,-0.16,0.62),(0.7,0.04,0.16),W)
for x in (-0.6,0.6):
    cube("Leg",(x,0,0.22),(0.05,0.18,0.22),W2)
finish("prop_bench", ratio=0.8, bevel=0.01)

# ============ prop_sign（立て看板）============
reset()
W=WOOD(); W2=WOOD2()
cube("Post",(0,0,0.7),(0.06,0.06,0.7),W2)
cube("Board",(0,-0.04,1.15),(0.36,0.04,0.24),W)
cube("FrameT",(0,-0.06,1.40),(0.40,0.03,0.03),W2)
cube("FrameB",(0,-0.06,0.90),(0.40,0.03,0.03),W2)
finish("prop_sign", ratio=0.8, bevel=0.008)

# ============ prop_lamp（街灯・発光ランタン）============
reset()
IR=IRON(); GLOW=mat("Glow",(1.0,0.85,0.45),0.3,emis=(1.0,0.82,0.4)); GLS=mat("LGlass",(0.9,0.85,0.7),0.1)
cyl("Pole",(0,0,1.2),0.05,2.4,IR,verts=10)
cube("Base",(0,0,0.06),(0.14,0.14,0.06),IR)
cube("Arm",(0,0.12,2.3),(0.03,0.16,0.03),IR)
# ランタン箱
cube("LFrame",(0,0.22,2.18),(0.10,0.10,0.14),IR)
cube("LGlass",(0,0.22,2.18),(0.075,0.075,0.11),GLS)
cube("LFlame",(0,0.22,2.16),(0.04,0.04,0.06),GLOW)
cone("LTop",(0,0.22,2.32),0.10,0.08,IR,verts=8)
finish("prop_lamp", ratio=0.75, bevel=0.006)

# ============ prop_brazier（篝火・三脚の鉄鉢＋炎）============
reset()
IR=IRON(); FL=mat("Flame",(1.0,0.5,0.12),0.3,emis=(1.0,0.45,0.1)); FL2=mat("Flame2",(1.0,0.8,0.3),0.3,emis=(1.0,0.78,0.3)); WD=WOOD2()
cyl("Bowl",(0,0,0.62),0.26,0.18,IR,verts=16)
cyl("BowlIn",(0,0,0.68),0.22,0.10,mat("Char",(0.10,0.09,0.08),0.9),verts=16)
for a in range(3):
    ang=math.radians(a*120); x=math.cos(ang)*0.18; y=math.sin(ang)*0.18
    cyl("Leg",(x,y,0.30),0.025,0.62,IR,verts=6,rot=(math.radians(12),0,ang))
# 薪＋炎
for a in range(3):
    ang=math.radians(a*60); cube("Log",(math.cos(ang)*0.08,math.sin(ang)*0.08,0.70),(0.16,0.03,0.03),WD,rot=(0,0,ang))
cone("Flame",(0,0,0.92),0.16,0.34,FL,verts=12)
cone("Flame2",(0,0,0.98),0.09,0.22,FL2,verts=10)
finish("prop_brazier", ratio=0.7, bevel=0.006)

# ============ prop_cart（荷車・荷台＋2輪＋梶棒）============
reset()
W=WOOD(); W2=WOOD2(); IR=IRON()
cube("Bed",(0,0,0.50),(0.45,0.7,0.06),W)
cube("SideL",(0.45,0,0.62),(0.04,0.7,0.14),W2); cube("SideR",(-0.45,0,0.62),(0.04,0.7,0.14),W2)
cube("SideB",(0,0.7,0.62),(0.45,0.04,0.14),W2)
for sx in (-1,1):
    cyl("Wheel",(sx*0.52,-0.1,0.34),0.34,0.06,W2,verts=18,rot=(0,math.radians(90),0))
    cyl("Hub",(sx*0.52,-0.1,0.34),0.07,0.10,IR,verts=10,rot=(0,math.radians(90),0))
# 梶棒（前方-Y側）
for sx in (-1,1):
    cube("Shaft",(sx*0.30,-0.95,0.46),(0.03,0.45,0.03),W2)
# 荷（樽1）
cyl("Cargo",(0,0.2,0.74),0.18,0.34,W,verts=14)
finish("prop_cart", ratio=0.65, bevel=0.006)

# ============ prop_barrel（樽）============
reset()
W=WOOD(); IR=IRON()
cyl("Body",(0,0,0.45),0.30,0.86,W,verts=18)
cyl("BodyMid",(0,0,0.45),0.33,0.30,W,verts=18)               # 中央の膨らみ
for z in (0.12,0.45,0.78):
    cyl("Hoop",(0,0,z),0.335,0.05,IR,verts=18)
finish("prop_barrel", subsurf=0, ratio=0.7, bevel=0.01)

# ============ prop_crate（木箱）============
reset()
W=WOOD(); W2=WOOD2()
cube("Box",(0,0,0.32),(0.32,0.32,0.32),W)
# 上下の縁（各辺）
for z in (0.02,0.62):
    cube("EdgeF",(0,0.32,z),(0.34,0.03,0.03),W2); cube("EdgeB",(0,-0.32,z),(0.34,0.03,0.03),W2)
    cube("EdgeR",(0.32,0,z),(0.03,0.34,0.03),W2); cube("EdgeL",(-0.32,0,z),(0.03,0.34,0.03),W2)
# 四隅の縦柱
for (x,y) in [(0.32,0.32),(0.32,-0.32),(-0.32,0.32),(-0.32,-0.32)]:
    cube("Corner",(x,y,0.32),(0.03,0.03,0.34),W2)
# 前面の斜め筋交い
cube("XBrace",(0,-0.33,0.32),(0.30,0.01,0.03),W2,rot=(0,math.radians(45),0))
finish("prop_crate", ratio=0.8, bevel=0.006)

# ============ prop_laundry（洗濯物・2柱＋綱＋吊るし布）============
reset()
WD=WOOD2(); R=ROPE()
for x in (-0.85,0.85):
    cyl("Post",(x,0,0.7),0.04,1.4,WD,verts=8)
    cube("Cross",(x,0,1.3),(0.18,0.03,0.03),WD)
cyl("Line",(0,0,1.32),0.008,1.7,R,verts=6,rot=(0,math.radians(90),0))
for i,(x,c) in enumerate([(-0.5,(0.80,0.40,0.40)),(-0.1,(0.45,0.60,0.80)),(0.3,(0.90,0.88,0.80)),(0.65,(0.55,0.75,0.55))]):
    cube("Cloth%d"%i,(x,0.0,1.10),(0.13,0.01,0.22),CLOTH(c))
finish("prop_laundry", ratio=0.8, bevel=0.0)

print("[voxel] all town props done")
