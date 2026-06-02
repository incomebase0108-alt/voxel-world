# -*- coding: utf-8 -*-
# VOXEL WORLD - 洞窟/採掘アセット：鉱石ブロック4種＋洞窟装飾3種
# Blender 5.1 / headless: blender --background --python tools/build_cave.py
#   出力: models/ore_coal/ore_iron/ore_gold/ore_gem.glb（石ブロック＋鉱石ナゲット埋込・1x1x1）
#         models/cave_stalactite/cave_stalagmite/cave_pillar.glb（洞窟装飾）
#   規約: Y-up / 1ブロック≒1m / 軽量・アニメ無し。
#   原点: 鉱石ブロック=足元中心z=0（terrainブロック相当）。
#         stalagmite/pillar=床中心z=0。stalactite=【例外】天井付着点を原点(z=0)・先端は下(-Z)へ。
#   1号機の洞窟生成(鉱石ブロック・深さランク)に直結。深さ/ドロップ仕様は ORES.md/json 参照。

import bpy, os, math, mathutils, random
V=mathutils.Vector
random.seed(42)   # 再現性

def reset():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for blk in (bpy.data.meshes,bpy.data.materials,bpy.data.objects,bpy.data.actions):
        for it in list(blk):
            try: blk.remove(it)
            except Exception: pass
    parts.clear()

def mat(n,rgb,r=0.8,me=0.0,emis=None):
    m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*rgb,1.0);b.inputs["Roughness"].default_value=r;b.inputs["Metallic"].default_value=me
    if emis is not None:
        b.inputs["Emission Color"].default_value=(*emis,1.0); b.inputs["Emission Strength"].default_value=1.5
    return m

parts=[]
def cube(n,loc,s,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.rotation_euler=rot;o.data.materials.append(m);parts.append(o);return o
def ico(n,loc,s,m,subd=1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subd,location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.data.materials.append(m);parts.append(o);return o
def cone(n,loc,r,d,m,verts=10,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r,radius2=0.0,depth=d,location=loc)
    o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);parts.append(o);return o
def cyl(n,loc,r,d,m,verts=10,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d,location=loc)
    o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);parts.append(o);return o

repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."));models=os.path.join(repo,"models");os.makedirs(models,exist_ok=True)
scene=bpy.context.scene

def finish(name, origin_mode="floor", ratio=0.7, bevel=0.01, flat=True):
    """parts結合→decimate→原点設定→GLB。origin_mode: floor(足元中心z=0)/ceiling(天井付着=最上点中心)。"""
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts: o.select_set(True)
    bpy.context.view_layer.objects.active=parts[0]; bpy.ops.object.join()
    o=bpy.context.active_object; o.name=name
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel>0:
        bv=o.modifiers.new("B",'BEVEL'); bv.width=bevel; bv.segments=1
        bpy.ops.object.modifier_apply(modifier=bv.name)
    if ratio<1.0:
        d=o.modifiers.new("D",'DECIMATE');d.decimate_type='COLLAPSE';d.ratio=ratio
        bpy.ops.object.modifier_apply(modifier=d.name)
    if flat: bpy.ops.object.shade_flat()
    else: bpy.ops.object.shade_smooth()
    bpy.context.view_layer.update()
    xs=[(o.matrix_world@V(c)).x for c in o.bound_box]; ys=[(o.matrix_world@V(c)).y for c in o.bound_box]; zs=[(o.matrix_world@V(c)).z for c in o.bound_box]
    cx=(min(xs)+max(xs))/2; cy=(min(ys)+max(ys))/2
    pz = max(zs) if origin_mode=="ceiling" else min(zs)   # 天井付着は最上点を原点に
    scene.cursor.location=(cx,cy,pz)
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR'); o.location=(0,0,0)
    out=os.path.join(models,name+".glb")
    bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_animations=False)
    sz=os.path.getsize(out)
    print("[voxel] %-18s -> %.3f MB  dims=%.2fx%.2fx%.2f"%(name, sz/1048576, max(xs)-min(xs),max(ys)-min(ys),max(zs)-min(zs)))

# ============ 鉱石ブロック（石1x1x1＋鉱石ナゲットを各面に散らす）============
def ore_block(name, ore_rgb, ore_r=0.5, ore_me=0.0, emis=None, n_nug=8):
    reset()
    STONE=mat("Stone_"+name,(0.50,0.50,0.53),0.92)
    ORE=mat("Ore_"+name,ore_rgb,ore_r,ore_me,emis)
    cube("Block",(0,0,0.5),(0.5,0.5,0.5),STONE)   # 1x1x1 石ブロック（z 0..1）
    # 4側面＋上面に鉱石ナゲット。面に沿って平たく埋め込み（法線方向は薄く＝突出~0.04）。
    #   axis: 面の法線軸。0=X,1=Y,2=Z。sign: ±。面中心に置き面内2軸にランダムオフセット。
    faces=[(0, 0.5),(0,-0.5),(1, 0.5),(1,-0.5),(2, 1.0)]  # X+,X-,Y+,Y-,Z+(上面のみ)
    for i in range(n_nug):
        axis,sgn=random.choice(faces)
        s=random.uniform(0.09,0.16); thin=0.05    # 面内サイズ／法線方向の薄さ(突出~0.04)
        sc=[s,s,s]; sc[axis]=thin
        loc=[0.0,0.0,0.0]; loc[axis]=sgn
        for a in (0,1,2):
            if a==axis: continue
            loc[a]= random.uniform(0.20,0.80) if a==2 else random.uniform(-0.32,0.32)  # Zは塊内
        ico("Nug%d"%i,tuple(loc),tuple(sc),ORE,subd=1)
    finish(name, origin_mode="floor", ratio=0.6, bevel=0.008, flat=True)

ore_block("ore_coal", (0.10,0.10,0.12), ore_r=0.6)                         # 石炭（黒）浅層
ore_block("ore_iron", (0.74,0.56,0.42), ore_r=0.7)                         # 鉄（赤茶/buff）中層
ore_block("ore_gold", (0.92,0.75,0.26), ore_r=0.35, ore_me=0.6)            # 金（金属）深層
ore_block("ore_gem",  (0.35,0.85,0.95), ore_r=0.15, emis=(0.2,0.6,0.7), n_nug=6)  # 宝石（水晶）最深層・淡発光

# ============ 洞窟装飾 ============
ROCK=lambda: mat("Rock",(0.46,0.45,0.47),0.9); ROCK2=lambda: mat("Rock2",(0.38,0.37,0.40),0.9)

# 鍾乳石（天井から下へ・原点=天井付着点）
reset()
R=ROCK(); R2=ROCK2()
cyl("Base",(0,0,-0.06),0.16,0.12,R,verts=10)          # 天井付け根
cone("Spike",(0,0,-0.5),0.15,0.8,R2,verts=10,rot=(math.radians(180),0,0))  # 下向きの尖り
finish("cave_stalactite", origin_mode="ceiling", ratio=0.7, bevel=0.01, flat=True)

# 石筍（床から上へ・原点=床中心）
reset()
R=ROCK(); R2=ROCK2()
cyl("Base",(0,0,0.06),0.18,0.12,R,verts=10)
cone("Spike",(0,0,0.5),0.17,0.85,R2,verts=10)
finish("cave_stalagmite", origin_mode="floor", ratio=0.7, bevel=0.01, flat=True)

# 岩柱（床から立つ太い石柱・約2.2m・原点=床中心）
reset()
R=ROCK(); R2=ROCK2()
cyl("Lower",(0,0,0.55),0.26,1.1,R,verts=12)
cyl("Upper",(0,0,1.6),0.22,1.1,R2,verts=12)
ico("Bulge",(0.12,0.05,1.0),(0.18,0.16,0.22),R,subd=1)   # 不整な岩肌
ico("Bulge2",(-0.10,-0.08,1.7),(0.16,0.15,0.20),R2,subd=1)
finish("cave_pillar", origin_mode="floor", ratio=0.6, bevel=0.012, flat=True)

print("[voxel] cave/ore assets done")
