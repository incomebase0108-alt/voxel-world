# -*- coding: utf-8 -*-
# VOXEL WORLD - 洞窟バリエーション（世界拡張④・発光プロップ）
# Blender 5.1 / headless: blender --background --python tools/build_cave_var.py [-- --render]
#   規約: Y-up / 足元最下点z=0 / 正面 -Z / 1ブロック≒1m / 軽量(flat+bevel+decimate)・アニメ無し。
#   方針: 既存 cave_stalactite/stalagmite/pillar・ore_* に対し「洞窟を彩るバリエ」を追加。
#     発光クリスタル(青/紫)・光るキノコ・苔むした巨岩・晶洞(ジオード)。発光部はEmissionで暗所に映える。
#   既存規約: cave_ プレフィックス＝ASSETS索引「洞窟・鉱石」カテゴリに自動分類。
#   出力: models/cave_*.glb。

import bpy, os, math, mathutils, sys
V=mathutils.Vector
scene=bpy.context.scene

parts=[]
def reset():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for blk in (bpy.data.meshes,bpy.data.materials,bpy.data.objects,bpy.data.actions):
        for it in list(blk):
            try: blk.remove(it)
            except Exception: pass
    parts.clear()
def mat(n,rgb,r=0.9,me=0.0,emis=None,es=2.0):
    m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*rgb,1.0);b.inputs["Roughness"].default_value=r;b.inputs["Metallic"].default_value=me
    if emis is not None:
        b.inputs["Emission Color"].default_value=(*emis,1.0); b.inputs["Emission Strength"].default_value=es
    return m
def cube(n,loc,s,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.rotation_euler=rot;o.data.materials.append(m);parts.append(o);return o
def cyl(n,loc,r,d,m,verts=12,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d,location=loc)
    o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);parts.append(o);return o
def cone(n,loc,r,d,m,verts=6,rot=(0,0,0),r2=0.0):
    bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r,radius2=r2,depth=d,location=loc)
    o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);parts.append(o);return o
def sphere(n,loc,s,m,segs=16,rings=10):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs,ring_count=rings,location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.data.materials.append(m);parts.append(o);return o

repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))

def finish(name, ratio=0.6, bevel=0.01, flat=True):
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts: o.select_set(True)
    bpy.context.view_layer.objects.active=parts[0]; bpy.ops.object.join()
    o=bpy.context.active_object; o.name=name
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
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
    scene.cursor.location=((min(xs)+max(xs))/2,(min(ys)+max(ys))/2,min(zs))
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR'); o.location=(0,0,0)
    out=os.path.join(repo,"models",name+".glb")
    bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_animations=False)
    print("[voxel] %-20s -> %.3f MB  dims=%.2fx%.2fx%.2f"%(name, os.path.getsize(out)/1048576, max(xs)-min(xs),max(ys)-min(ys),max(zs)-min(zs)))
    return o

ROCK=lambda:mat("Rock",(0.30,0.30,0.34),0.95)
ROCK2=lambda:mat("Rock2",(0.22,0.22,0.26),0.95)
MOSS=lambda:mat("Moss",(0.26,0.40,0.18),0.9)

def crystal_cluster(name, ccol, glow):
    """発光クリスタルの群生（岩座＋数本の結晶）"""
    reset()
    RK=ROCK2(); CR=mat("Cry",ccol,0.25,me=0.1,emis=glow,es=3.2); CR2=mat("Cry2",[c*0.8 for c in ccol],0.3,emis=glow,es=2.2)
    # 岩座
    sphere("Base",(0,0,0.10),(0.34,0.34,0.16),RK)
    cube("Base2",(0.12,-0.10,0.10),(0.16,0.14,0.12),RK)
    # 結晶（六角錐＝先細りcone・角度と長さを散らす）
    spec=[(0,0,0.0,0.55,0.07),(0.12,0.06,8,0.40,0.05),(-0.10,0.08,-10,0.46,0.055),
          (0.06,-0.12,14,0.32,0.045),(-0.14,-0.06,-16,0.30,0.04),(0.16,0.0,20,0.24,0.04)]
    for i,(x,y,tilt,h,r) in enumerate(spec):
        m=CR if i%2==0 else CR2
        cone("Cry%d"%i,(x,y,0.16+h*0.5),r,h,m,verts=6,rot=(math.radians(tilt),0,math.radians(i*40)))
    # 発光は結晶自体(Emission)で。オーラ球は結晶を覆い隠すため不使用。
    return finish(name, ratio=0.7, bevel=0.006)

# cave_crystal（青）/ cave_crystal_purple（紫）
crystal_cluster("cave_crystal",        (0.40,0.80,0.95),(0.40,0.85,1.0))
crystal_cluster("cave_crystal_purple", (0.66,0.42,0.92),(0.62,0.36,0.95))

# cave_mushroom（光るキノコの群生）
reset()
RK=ROCK(); MS=MOSS(); STEM=mat("Stem",(0.86,0.84,0.78),0.7)
CAP=mat("Cap",(0.30,0.66,0.74),0.4,emis=(0.30,0.85,0.9),es=2.6); SPOT=mat("Spot",(0.95,0.97,0.95),0.5,emis=(0.8,0.95,0.95),es=1.2)
GILL=mat("Gill",(0.5,0.9,0.95),0.3,emis=(0.4,0.9,0.95),es=2.0)
sphere("Mound",(0,0,0.06),(0.36,0.36,0.10),RK)
cube("MossM",(0.0,0.0,0.12),(0.30,0.26,0.012),MS)
def mushroom(x,y,h,cap):
    cyl("Stem",(x,y,h*0.5),0.045,h,STEM,verts=10)
    sphere("Cap",(x,y,h+cap*0.2),(cap,cap,cap*0.7),CAP,segs=16,rings=10)
    cyl("Gill",(x,y,h-0.01),cap*0.85,0.03,GILL,verts=12)        # 笠裏の発光ひだ
    for k in range(4):
        a=math.radians(k*90+15)
        sphere("Spot%d_%g"%(k,x),(x+cap*0.5*math.cos(a),y+cap*0.5*math.sin(a),h+cap*0.32),(0.025,0.025,0.02),SPOT,segs=8,rings=6)
mushroom(0.0,0.02,0.34,0.18)
mushroom(0.16,-0.10,0.22,0.12)
mushroom(-0.14,-0.06,0.16,0.10)
finish("cave_mushroom", ratio=0.6, bevel=0.008, flat=False)

# cave_boulder（苔むした巨岩・小結晶が顔を出す）
reset()
RK=ROCK(); RK2=ROCK2(); MS=MOSS(); CR=mat("Cry",(0.45,0.82,0.95),0.3,emis=(0.4,0.85,1.0),es=2.4)
sphere("Rock1",(0,0,0.40),(0.55,0.50,0.42),RK,segs=14,rings=10)
sphere("Rock2",(0.28,0.10,0.22),(0.30,0.28,0.24),RK2,segs=12,rings=8)
sphere("Rock3",(-0.24,-0.14,0.20),(0.26,0.24,0.20),RK2,segs=12,rings=8)
cube("Facet",(0,0.38,0.5),(0.34,0.10,0.30),RK2,rot=(math.radians(14),0,0))   # 割れ面
for (mx,my,mz,ms) in [(0.0,-0.2,0.70,0.30),(0.30,0.0,0.46,0.20),(-0.20,0.18,0.40,0.18)]:
    sphere("Moss%g"%mx,(mx,my,mz),(ms,ms,ms*0.4),MS,segs=10,rings=8)
for (cx,cy,cz,ch) in [(-0.30,0.20,0.30,0.18),(0.34,-0.18,0.28,0.14)]:
    cone("Cry%g"%cx,(cx,cy,cz),0.04,ch,CR,verts=6,rot=(math.radians(40),0,math.radians(20)))
finish("cave_boulder", ratio=0.55, bevel=0.01)

# cave_geode（晶洞・割れて開いた岩の間に結晶が群れる＝スプリット岩。遮蔽せず確実に映える）
reset()
RK=ROCK(); RK2=ROCK2(); MS=MOSS()
CR=mat("Cry",(0.85,0.55,0.95),0.25,emis=(0.8,0.45,0.98),es=3.0); CR2=mat("Cry2",(0.95,0.75,0.55),0.3,emis=(0.95,0.7,0.5),es=2.0)
# 土台＋割れた左右の岩塊（中央に隙間）
sphere("GBase",(0,0,0.11),(0.44,0.36,0.13),RK2)
sphere("GHalfL",(-0.34,0.0,0.26),(0.24,0.30,0.24),RK,segs=14,rings=10)
sphere("GHalfR",( 0.36,-0.02,0.24),(0.22,0.28,0.22),RK,segs=14,rings=10)
cube("GFaceL",(-0.16,0.0,0.26),(0.04,0.26,0.22),RK2,rot=(0,math.radians(14),0))   # 割れ口の岩肌
cube("GFaceR",( 0.18,0.0,0.24),(0.04,0.24,0.20),RK2,rot=(0,math.radians(-14),0))
sphere("GMoss",(-0.30,0.10,0.46),(0.16,0.14,0.06),MS,segs=10,rings=8)
# 中央の広い隙間に結晶群（岩より高く突出＝遮蔽なし）
spec=[(0.0,0.0,0,0.46,0.055),(0.07,0.05,10,0.34,0.045),(-0.07,0.05,-12,0.38,0.048),
      (0.12,-0.05,16,0.26,0.04),(-0.12,-0.04,-16,0.28,0.04),(0.0,0.10,4,0.22,0.035)]
for i,(x,y,tilt,h,r) in enumerate(spec):
    m=CR if i%2==0 else CR2
    cone("GCry%d"%i,(x,y,0.22+h*0.5),r,h,m,verts=6,rot=(math.radians(tilt),0,math.radians(i*36)))
finish("cave_geode", ratio=0.62, bevel=0.008)   # 結晶のEmissionで発光

print("[voxel] cave variations done: cave_crystal/_purple, cave_mushroom, cave_boulder, cave_geode")

# ---- プレビュー（--render 時・暗い洞窟で発光を見る。最後に残ったgeodeを描画）----
try:
    if "--render" in sys.argv:
        try: scene.render.engine='BLENDER_EEVEE_NEXT'
        except Exception: scene.render.engine='BLENDER_EEVEE'
        scene.render.resolution_x=820; scene.render.resolution_y=620
        world=bpy.data.worlds.new("W"); scene.world=world; world.use_nodes=True
        world.node_tree.nodes["Background"].inputs[0].default_value=(0.03,0.03,0.05,1)   # 暗所
        world.node_tree.nodes["Background"].inputs[1].default_value=0.4
        bpy.ops.object.light_add(type='AREA',location=(2,-3,4)); k=bpy.context.active_object
        k.data.energy=40; k.data.size=3.0
        def shot(name,loc,rot,lens=55):
            bpy.ops.object.camera_add(location=loc,rotation=rot)
            cam=bpy.context.active_object; scene.camera=cam; cam.data.lens=lens
            scene.render.filepath=os.path.join(repo,"tools",name)
            bpy.ops.render.render(write_still=True); bpy.data.objects.remove(cam,do_unlink=True)
        shot("hero_cave_geode_3q.png",(1.3,-1.3,1.0),(math.radians(64),0,math.radians(-45)))
        print("[voxel] cave preview rendered: tools/hero_cave_geode_3q.png")
except Exception as e:
    print("[voxel] cave preview skipped:", e)
