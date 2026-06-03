# -*- coding: utf-8 -*-
# VOXEL WORLD - ボス出現演出パーツ（fx_*.glb）
# Blender 5.1 / headless: blender --background --python tools/build_fx_boss.py [-- --render]
#   出力: models/fx_magic_circle.glb / fx_miasma.glb / fx_collapse.glb
#   規約: Y-up / 正面 Blender+Y(=glTF -Z) / 1ブロック≒1m。発光=Emission。軽量(subsurf+decimate)。
#   各パーツは自己完結のループアニメ「loop」を内包（全オブジェクトのNLAトラック名を "loop" に統一
#   ＝glTFで単一アニメ "loop" にマージ）。1号機は bossSpawn 時に生成し animation "loop" を再生。
#   地面置き想定で原点=footprint中心・接地(z=0)。回転演出は中心Z軸まわり。

import bpy, os, math, mathutils
V=mathutils.Vector
scene=bpy.context.scene; scene.render.fps=24
scene.frame_start=1; scene.frame_end=96

def wipe():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for blk in (bpy.data.meshes,bpy.data.materials,bpy.data.objects,bpy.data.actions):
        for it in list(blk):
            try: blk.remove(it)
            except Exception: pass

def mat(n,rgb,r=0.8,me=0.0,emis=None,es=3.0,alpha=1.0):
    m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*rgb,alpha);b.inputs["Roughness"].default_value=r;b.inputs["Metallic"].default_value=me
    if emis is not None:
        b.inputs["Emission Color"].default_value=(*emis,1.0); b.inputs["Emission Strength"].default_value=es
    return m

G=[]   # 現在のグループの部品
def cube(loc,s,m,rot=(0,0,0),n="c"):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.rotation_euler=rot;o.data.materials.append(m);G.append(o);return o
def cyl(loc,r,d,m,verts=20,rot=(0,0,0),n="cy"):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d,location=loc)
    o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);G.append(o);return o
def cone(loc,r,d,m,verts=8,rot=(0,0,0),r2=0.0,n="co"):
    bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r,radius2=r2,depth=d,location=loc)
    o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);G.append(o);return o
def sphere(loc,s,m,segs=16,rings=10,n="sp"):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs,ring_count=rings,location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.data.materials.append(m);G.append(o);return o
def torus(loc,maj,minr,m,rot=(0,0,0),mv=40,minv=10,n="to"):
    bpy.ops.mesh.primitive_torus_add(location=loc,major_radius=maj,minor_radius=minr,
        major_segments=mv,minor_segments=minv,rotation=rot)
    o=bpy.context.active_object;o.name=n;o.data.materials.append(m);G.append(o);return o

def join_group(name, origin=(0,0,0), subsurf=0, ratio=0.6, bevel=0.0, flat=True):
    """G の部品を1メッシュに結合し origin を設定。G はクリア。返り値=オブジェクト"""
    bpy.ops.object.select_all(action='DESELECT')
    for o in G: o.select_set(True)
    bpy.context.view_layer.objects.active=G[0]; bpy.ops.object.join()
    o=bpy.context.active_object; o.name=name
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    if bevel>0:
        bv=o.modifiers.new("B",'BEVEL'); bv.width=bevel; bv.segments=1; bpy.ops.object.modifier_apply(modifier=bv.name)
    if subsurf:
        s=o.modifiers.new("S",'SUBSURF');s.levels=subsurf;s.render_levels=subsurf
        bpy.ops.object.shade_smooth();bpy.ops.object.modifier_apply(modifier=s.name)
    if ratio<1.0:
        d=o.modifiers.new("D",'DECIMATE');d.decimate_type='COLLAPSE';d.ratio=ratio;bpy.ops.object.modifier_apply(modifier=d.name)
    bpy.ops.object.shade_flat() if flat else bpy.ops.object.shade_smooth()
    scene.cursor.location=origin
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    G.clear(); return o

# --- アニメ（全トラック名 "loop"・frame1=最終で継ぎ目なし） ---
def act(o,n):
    if o.animation_data is None: o.animation_data_create()
    a=bpy.data.actions.new(n);a.use_fake_user=True;o.animation_data.action=a;return a
def push(o):
    ad=o.animation_data; a=ad.action; tr=ad.nla_tracks.new(); tr.name="loop"
    tr.strips.new(a.name,int(a.frame_range[0]),a); ad.action=None
def krz(o,f,d): o.rotation_euler[2]=math.radians(d); o.keyframe_insert('rotation_euler',index=2,frame=f)
def kz(o,f,z): o.location.z=z; o.keyframe_insert('location',index=2,frame=f)
def ksc(o,f,s):
    o.scale=(s,s,s); o.keyframe_insert('scale',frame=f)

repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
models=os.path.join(repo,"models"); os.makedirs(models,exist_ok=True)

def export(name, objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active=objs[0]
    scene.frame_set(1)
    out=os.path.join(models,name+".glb")
    bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_yup=True,
        export_apply=False,export_animations=True,export_animation_mode='NLA_TRACKS',
        export_optimize_animation_size=True)
    zs=[(o.matrix_world@V(c)).z for o in objs for c in o.bound_box]
    sz=os.path.getsize(out)
    print("[voxel] %-18s -> %.3f MB  H%.2fm  anim:loop"%(name, sz/1048576, max(zs)-min(zs)))

# ============================================================
# ① fx_magic_circle（召喚魔法陣・地面接地・発光）
#    外輪(深紅)＝右回り / 内星(紫)＝左回り(逆) / 中央グロウ＝拍動。直径≒3.6m。
# ============================================================
wipe()
CRIM=mat("FxCrimson",(0.50,0.04,0.08),0.6,emis=(0.95,0.10,0.16),es=5.0)
VIOL=mat("FxViolet",(0.28,0.06,0.45),0.6,emis=(0.62,0.22,0.98),es=4.5)
GLOW=mat("FxGlow",(0.85,0.55,1.0),0.5,emis=(0.85,0.60,1.0),es=6.0)
RUNE=mat("FxRune",(0.40,0.10,0.55),0.6,emis=(0.80,0.30,0.95),es=4.0)
Zc=0.03   # 接地からの僅かな浮き
# --- 外輪グループ（深紅）---
torus((0,0,Zc),1.78,0.045,CRIM,mv=48,minv=8,n="RingOut")
torus((0,0,Zc),1.55,0.028,CRIM,mv=48,minv=8,n="RingOut2")
NR=24
for i in range(NR):                       # 外周のルーン刻み
    a=2*math.pi*i/NR
    cube((1.66*math.cos(a),1.66*math.sin(a),Zc),(0.05,0.10 if i%2==0 else 0.05,0.012),RUNE,rot=(0,0,a),n="Rune")
ring_out=join_group("fx_mc_ring", origin=(0,0,0), ratio=0.85, bevel=0.004)
# --- 内星グループ（紫・六芒星＝三角形2枚）---
def star_tri(flip):
    # 三角形の頂点（六芒星＝三角2枚）→ 各辺を細長cubeで
    R=1.30; verts=[(R*math.cos(math.radians(90+120*k+(180 if flip else 0))),
                    R*math.sin(math.radians(90+120*k+(180 if flip else 0))),Zc) for k in range(3)]
    for k in range(3):
        x0,y0,_=verts[k]; x1,y1,_=verts[(k+1)%3]
        mx,my=(x0+x1)/2,(y0+y1)/2; ang=math.atan2(y1-y0,x1-x0); ln=math.hypot(x1-x0,y1-y0)
        cube((mx,my,Zc),(ln/2,0.035,0.012),VIOL,rot=(0,0,ang),n="StarEdge")
star_tri(False); star_tri(True)
torus((0,0,Zc),1.18,0.024,VIOL,mv=40,minv=8,n="RingMid")
ring_in=join_group("fx_mc_star", origin=(0,0,0), ratio=0.9, bevel=0.003)
# --- 中央グロウ ---
cyl((0,0,Zc),0.42,0.018,GLOW,verts=28,n="CoreDisk")
sphere((0,0,Zc+0.05),(0.22,0.22,0.10),GLOW,segs=18,rings=10,n="CoreOrb")
core=join_group("fx_mc_core", origin=(0,0,Zc), ratio=0.7)
# --- アニメ ---
act(ring_out,"mc_out");  [krz(ring_out,f,d) for f,d in [(1,0),(96,360)]]; push(ring_out)   # 右回り1周/4s
act(ring_in,"mc_in");    [krz(ring_in,f,d) for f,d in [(1,0),(96,-360)]]; push(ring_in)    # 逆回り
act(core,"mc_core")
for f,s in [(1,1.0),(24,1.18),(48,0.92),(72,1.18),(96,1.0)]: ksc(core,f,s)                 # 拍動
push(core)
export("fx_magic_circle",[ring_out,ring_in,core])

# ============================================================
# ② fx_miasma（瘴気・毒の霧・立ち昇る）
#    病的な緑×紫の塊雲＋触手。下層=広く濃く / 上層=細く。3層が別速で旋回＋上下うねり。高さ≒2.6m。
# ============================================================
wipe()
# 緑主体・紫は深部の陰影のみ（少数）。発光は緑を強めて毒霧らしく。
GAS1=mat("Gas1",(0.20,0.40,0.10),0.95,emis=(0.22,0.66,0.10),es=1.8)   # 病的な毒緑（主）
GAS2=mat("Gas2",(0.16,0.36,0.12),0.95,emis=(0.18,0.58,0.12),es=1.5)   # 緑の濃淡（主）
GAS3=mat("Gas3",(0.32,0.46,0.14),0.92,emis=(0.34,0.72,0.12),es=2.2)   # 明るい毒緑（上層の艶）
DEEP=mat("GasDeep",(0.20,0.10,0.26),0.95,emis=(0.30,0.10,0.42),es=0.9) # 紫＝深部の陰影（少数）
import math as _m
def blob_layer(zc, rad, n, sc, matA, matB, seed):
    for i in range(n):
        a=2*_m.pi*i/n + seed
        r=rad*(0.55+0.45*((i*7)%5)/4)                       # 半径ばらつき大
        s=sc*(0.6+0.7*((i*3)%4)/3)                          # 大小差を強く＝不揃いな霧
        zz=zc+0.18*((i*5)%3)
        # 紫は3個に1個未満＝深部のみ。大半は緑。
        mt=DEEP if (i%4==0) else (matA if i%2==0 else matB)
        sphere((r*_m.cos(a), r*_m.sin(a), zz),(s,s*1.05,s*0.72),mt,segs=11,rings=7,n="Blob")
# 下層（広く濃い）
blob_layer(0.50,1.00,8,0.55,GAS1,GAS2,0.0)
m_low=join_group("fx_mi_low", origin=(0,0,0), subsurf=1, ratio=0.30)
# 中層
blob_layer(1.30,0.66,6,0.40,GAS2,GAS1,0.5)
m_mid=join_group("fx_mi_mid", origin=(0,0,0), subsurf=1, ratio=0.30)
# 上層（細く・触手）＋立ち昇るウィスプ
blob_layer(2.00,0.42,4,0.28,GAS3,GAS1,0.9)
for i in range(4):
    a=2*_m.pi*i/4+0.3
    cone((0.5*_m.cos(a),0.5*_m.sin(a),2.30),0.09,0.7,GAS3,verts=6,r2=0.015,n="Wisp")
m_top=join_group("fx_mi_top", origin=(0,0,0), subsurf=1, ratio=0.32)
# アニメ：層ごとに別速で旋回＋上下うねり
act(m_low,"mi_low"); [krz(m_low,f,d) for f,d in [(1,0),(96,360)]];  [kz(m_low,f,z) for f,z in [(1,0),(48,0.12),(96,0)]]; push(m_low)
act(m_mid,"mi_mid"); [krz(m_mid,f,d) for f,d in [(1,0),(96,-360)]]; [kz(m_mid,f,z) for f,z in [(1,0),(48,0.20),(96,0)]]; push(m_mid)
act(m_top,"mi_top"); [krz(m_top,f,d) for f,d in [(1,0),(96,540)]];  [kz(m_top,f,z) for f,z in [(1,0),(48,0.30),(96,0)]]; push(m_top)
export("fx_miasma",[m_low,m_mid,m_top])

# ============================================================
# ③ fx_collapse（地面崩壊・瓦礫噴出＋地割れの発光）
#    中心の裂け目から、割れた岩盤(傾いた板)が円環状に隆起。瓦礫が浮揺れ・地割れが橙に脈動。直径≒3m。
# ============================================================
wipe()
ROCK=mat("Rock",(0.20,0.18,0.16),0.9)
ROCK2=mat("Rock2",(0.26,0.23,0.20),0.9)
MAGMA=mat("Magma",(0.55,0.18,0.05),0.6,emis=(1.0,0.42,0.10),es=6.0)   # 地割れの発光
# 中央の裂け目（発光・低い溝）
cyl((0,0,0.02),0.55,0.06,MAGMA,verts=10,n="Rift")
for i in range(5):
    a=2*math.pi*i/5
    cube((0.45*math.cos(a),0.45*math.sin(a),0.04),(0.30,0.05,0.02),MAGMA,rot=(0,0,a+0.3),n="Crack")
rift=join_group("fx_cl_rift", origin=(0,0,0), ratio=0.8, bevel=0.004)
# 隆起した岩盤（円環状に傾いた板）＝1グループ（ゆっくり上下に隆起）
NS=8
for i in range(NS):
    a=2*math.pi*i/NS
    R=1.15+0.12*((i*3)%3)
    tilt=math.radians(28+8*((i*2)%3))
    cube((R*math.cos(a),R*math.sin(a),0.28),(0.34,0.30,0.06),(ROCK if i%2==0 else ROCK2),
         rot=(tilt*math.sin(a),-tilt*math.cos(a),a),n="Slab")
slabs=join_group("fx_cl_slabs", origin=(0,0,0), ratio=0.7, bevel=0.006)
# 浮遊する瓦礫（小片・揺れ）
for i in range(10):
    a=2*math.pi*i/10+0.5; R=0.7+0.5*((i*7)%4)/3
    s=0.07+0.05*((i*5)%3)/2
    cube((R*math.cos(a),R*math.sin(a),0.45+0.25*((i*3)%4)/3),(s,s,s),(ROCK if i%2 else ROCK2),
         rot=(a,a*0.7,a*1.3),n="Debris")
debris=join_group("fx_cl_debris", origin=(0,0,0), ratio=0.8, bevel=0.004)
# アニメ：裂け目=脈動 / 岩盤=隆起うねり / 瓦礫=浮揺れ＋回転
act(rift,"cl_rift")
for f,s in [(1,1.0),(24,1.15),(48,0.9),(72,1.15),(96,1.0)]: ksc(rift,f,s)
push(rift)
act(slabs,"cl_slabs"); [kz(slabs,f,z) for f,z in [(1,0),(48,0.10),(96,0)]]; push(slabs)
act(debris,"cl_debris")
[krz(debris,f,d) for f,d in [(1,0),(96,180)]]; [kz(debris,f,z) for f,z in [(1,0),(24,0.12),(48,0),(72,0.12),(96,0)]]
push(debris)
export("fx_collapse",[rift,slabs,debris])

print("[voxel] fx boss-appearance set done: fx_magic_circle / fx_miasma / fx_collapse")

# ---- プレビュー（-- --render 指定時のみ）----
try:
    import sys
    if "--render" in sys.argv:
        def load(name):
            before=set(scene.objects); bpy.ops.import_scene.gltf(filepath=os.path.join(models,name+".glb"))
            return [o for o in scene.objects if o not in before]
        def setup(bg):
            try: scene.render.engine='BLENDER_EEVEE_NEXT'
            except Exception: scene.render.engine='BLENDER_EEVEE'
            scene.render.resolution_x=640; scene.render.resolution_y=640
            scene.world=bpy.data.worlds.new("W"); scene.world.use_nodes=True
            scene.world.node_tree.nodes["Background"].inputs[0].default_value=(*bg,1)
            scene.world.node_tree.nodes["Background"].inputs[1].default_value=0.4
            bpy.ops.object.light_add(type='SUN',location=(3,-4,7)); bpy.context.active_object.data.energy=2.5
        def shot(name,loc,look=(0,0,0.4)):
            bpy.ops.object.camera_add(location=loc); cam=bpy.context.active_object
            d=bpy.data.objects.new("E",None); scene.collection.objects.link(d); d.location=look
            cam.constraints.new('TRACK_TO').target=d; scene.camera=cam
            scene.render.filepath=os.path.join(repo,"tools",name); bpy.ops.render.render(write_still=True); print("[voxel] ->",name)
        for nm,bg in [("fx_magic_circle",(0.04,0.03,0.06)),("fx_miasma",(0.05,0.07,0.05)),("fx_collapse",(0.05,0.04,0.03))]:
            wipe(); setup(bg); load(nm); scene.frame_set(40)
            shot("hero_%s_3q.png"%nm,(3.0,-3.4,2.6))
        print("[voxel] fx previews rendered")
except Exception as e:
    print("[voxel] preview skipped:",e)
