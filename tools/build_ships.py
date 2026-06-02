# -*- coding: utf-8 -*-
# VOXEL WORLD - 船モデル（水上探索・将来の乗船用）
# Blender 5.1 / headless: blender --background --python tools/build_ships.py
#   出力: models/ship_rowboat.glb / ship_sailboat.glb / ship_wreck.glb
#   規約: Y-up / 1ブロック≒1m / 軽量・アニメ無し。前面(船首)= +Y(Blender)=glTF -Z。
#   原点: キール最下点 z=0（他モデルと統一）。喫水線z・甲板(乗船)z は計測して SHIPS.md に明記
#         （馬の鞍と同要領＝1号機はプレイヤーを甲板zに乗せ、喫水線zが水面に来るよう沈める）。

import bpy, os, math, mathutils
V=mathutils.Vector

def reset():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for blk in (bpy.data.meshes,bpy.data.materials,bpy.data.objects,bpy.data.actions):
        for it in list(blk):
            try: blk.remove(it)
            except Exception: pass
    parts.clear()

def mat(n,rgb,r=0.7,me=0.0):
    m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*rgb,1.0);b.inputs["Roughness"].default_value=r;b.inputs["Metallic"].default_value=me;return m

parts=[]
def cube(n,loc,s,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.rotation_euler=rot;o.data.materials.append(m);parts.append(o);return o
def cyl(n,loc,r,d,m,verts=12,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d,location=loc)
    o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);parts.append(o);return o

def hull(name, length, width, height, m, bow_taper=0.22, stern_taper=0.5, rocker=0.55, subsurf=1):
    """細分キューブをテーパー＋ロッカーで船体に。+Y=船首側を尖らせる。"""
    bpy.ops.mesh.primitive_cube_add(location=(0,0,0))
    o=bpy.context.active_object; o.name=name
    o.scale=(width/2, length/2, height/2); bpy.ops.object.transform_apply(scale=True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.subdivide(number_cuts=6); bpy.ops.object.mode_set(mode='OBJECT')
    me=o.data; half=length/2; hh=height/2
    for v in me.vertices:
        ny=max(-1,min(1, v.co.y/half))           # -1(船尾)..1(船首)
        t = bow_taper if ny>0 else stern_taper    # 船首は鋭く・船尾はやや広い
        v.co.x *= (1 - (1-t)*abs(ny)**1.6)        # 端へ向け幅を絞る
        if v.co.z < 0:                            # 底をロッカー（端で持ち上げ）
            v.co.z += rocker*hh*abs(ny)**2.0
    o.data.materials.append(m)
    if subsurf:
        s=o.modifiers.new("S",'SUBSURF'); s.levels=subsurf; s.render_levels=subsurf
        bpy.ops.object.shade_smooth(); bpy.ops.object.modifier_apply(modifier=s.name)
    parts.append(o); return o

repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."));models=os.path.join(repo,"models");os.makedirs(models,exist_ok=True)
scene=bpy.context.scene

def finish(name, ratio=0.55, bevel=0.0):
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts: o.select_set(True)
    bpy.context.view_layer.objects.active=parts[0]; bpy.ops.object.join()
    o=bpy.context.active_object; o.name=name
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel>0:
        bv=o.modifiers.new("B",'BEVEL'); bv.width=bevel; bv.segments=1; bpy.ops.object.modifier_apply(modifier=bv.name)
    if ratio<1.0:
        d=o.modifiers.new("D",'DECIMATE');d.decimate_type='COLLAPSE';d.ratio=ratio; bpy.ops.object.modifier_apply(modifier=d.name)
    bpy.ops.object.shade_smooth()
    bpy.context.view_layer.update()
    xs=[(o.matrix_world@V(c)).x for c in o.bound_box]; ys=[(o.matrix_world@V(c)).y for c in o.bound_box]; zs=[(o.matrix_world@V(c)).z for c in o.bound_box]
    scene.cursor.location=((min(xs)+max(xs))/2,(min(ys)+max(ys))/2,min(zs))
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR'); o.location=(0,0,0)
    out=os.path.join(models,name+".glb")
    bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_animations=False)
    sz=os.path.getsize(out)
    print("[voxel] %-16s -> %.3f MB  L%.2f W%.2f H%.2f"%(name, sz/1048576, max(ys)-min(ys),max(xs)-min(xs),max(zs)-min(zs)))

def WOOD(): return mat("Wood",(0.50,0.34,0.18),0.7)
def WOOD2(): return mat("Wood2",(0.40,0.26,0.13),0.7)
def DECK(): return mat("Deck",(0.62,0.45,0.26),0.7)
def SAIL(): return mat("Sail",(0.90,0.88,0.80),0.8)
def ROPE(): return mat("Rope",(0.62,0.52,0.34),0.8)
def IRON(): return mat("Iron",(0.28,0.28,0.30),0.45,me=0.6)

# ============ ship_rowboat（小舟・手漕ぎ・約2.6m）============
reset()
W=WOOD(); W2=WOOD2(); D=DECK(); R=ROPE()
hull("Hull", length=2.6, width=1.0, height=0.55, m=W, bow_taper=0.2, stern_taper=0.55, rocker=0.5)
# 内側の床（甲板）と縁（ガンネル）— 開口の見栄え
cube("Floor",(0,0,0.30),(0.34,1.05,0.02),D)
cube("GunL",(0.40,0,0.40),(0.04,1.1,0.10),W2,rot=(0,math.radians(6),0))
cube("GunR",(-0.40,0,0.40),(0.04,1.1,0.10),W2,rot=(0,math.radians(-6),0))
# ベンチ2脚
for y in (-0.5,0.5):
    cube("Bench",(0,y,0.36),(0.34,0.06,0.05),D)
# オール2本（船縁に立てかけ）
for sx in (-1,1):
    cyl("Oar",(sx*0.45,0.1,0.5),0.02,1.1,W2,verts=8,rot=(math.radians(70),0,math.radians(sx*12)))
    cube("Blade",(sx*0.66,0.55,0.78),(0.02,0.10,0.04),W2)
finish("ship_rowboat", ratio=0.6)

# ============ ship_sailboat（帆船・約5.2m・甲板＋マスト＋帆＋船室）============
reset()
W=WOOD(); W2=WOOD2(); D=DECK(); S=SAIL(); R=ROPE(); IR=IRON()
hull("Hull", length=5.2, width=1.9, height=1.0, m=W, bow_taper=0.18, stern_taper=0.6, rocker=0.5)
# 甲板
cube("Deck",(0,-0.1,0.78),(0.72,2.2,0.04),D)
# 舷側のレール（手すり）
for sx in (-1,1):
    cube("Rail",(sx*0.74,-0.1,0.95),(0.04,2.2,0.12),W2,rot=(0,math.radians(sx*5),0))
    for yy in (-1.6,-0.6,0.6,1.4):
        cube("Stanchion",(sx*0.74,yy,0.88),(0.03,0.03,0.16),W2)
# 船尾の小船室
cube("Cabin",(0,-1.8,1.05),(0.55,0.5,0.30),W2)
cube("CabinRoof",(0,-1.8,1.38),(0.6,0.55,0.04),D)
# マスト＋帆＋ブーム
cyl("Mast",(0,0.2,1.9),0.06,2.4,W2,verts=10)
cube("Sail",(0,0.22,2.1),(0.012,0.95,0.85),S)          # 主帆（縦帆）
cube("SailFront",(0,0.95,1.7),(0.012,0.25,0.5),S)      # 前帆（ジブ）気味
cyl("Boom",(0,0.2,1.0),0.03,1.7,W2,verts=8,rot=(math.radians(90),0,0))
# 船首の bowsprit ＋ 帆綱
cyl("Bowsprit",(0,2.5,1.0),0.035,0.9,W2,verts=8,rot=(math.radians(70),0,0))
finish("ship_sailboat", ratio=0.5)

# ============ ship_wreck（難破船・壊れた帆船・約5m・探索スポット）============
reset()
W=WOOD2(); WD=mat("WreckWood",(0.33,0.25,0.16),0.85); D=mat("WreckDeck",(0.42,0.33,0.20),0.85); S=mat("TornSail",(0.70,0.66,0.56),0.85)
h=hull("Hull", length=5.0, width=1.9, height=1.0, m=WD, bow_taper=0.2, stern_taper=0.6, rocker=0.5)
# 全体を傾ける（浜に乗り上げ/難破）
h.rotation_euler=(math.radians(12),0,math.radians(-8))
# 破れた甲板（一部欠け）
cube("Deck",(0.1,-0.3,0.75),(0.6,1.6,0.04),D,rot=(math.radians(10),0,0))
# 折れたマスト（斜めに倒れる）
cyl("MastBroken",(0.2,0.3,1.2),0.06,1.6,WD,verts=10,rot=(math.radians(40),0,math.radians(20)))
cyl("MastStump",(0,0.0,1.0),0.06,0.5,WD,verts=10)
# ボロ帆（垂れ下がる）
cube("Sail",(0.45,0.5,1.3),(0.012,0.5,0.4),S,rot=(math.radians(40),0,math.radians(20)))
# 破損穴っぽい暗部＋折れた板
cube("Hole",(0.42,-0.6,0.5),(0.02,0.22,0.20),mat("Dark",(0.10,0.08,0.06),0.9),rot=(0,math.radians(80),0))
for i,(px,py,pz,rx) in enumerate([(0.3,1.6,0.6,30),(-0.3,1.2,0.7,-20),(0.1,-1.7,0.6,50)]):
    cube("Plank%d"%i,(px,py,pz),(0.03,0.22,0.03),WD,rot=(math.radians(rx),0,math.radians(15)))
finish("ship_wreck", ratio=0.55)

print("[voxel] all ships done")
