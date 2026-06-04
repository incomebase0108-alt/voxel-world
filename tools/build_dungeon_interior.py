# -*- coding: utf-8 -*-
# VOXEL WORLD - 「建物に入るとダンジョン」室内パーツ一式（dgn_*）
# blender --background --python tools/build_dungeon_interior.py
#   出力(17): dgn_door_wood/dgn_door_iron / dgn_torch_wall/dgn_candelabra /
#             dgn_chest_closed/dgn_chest_open / dgn_table/dgn_chair/dgn_bookshelf/dgn_barrel /
#             dgn_stairs/dgn_stairs_spiral / dgn_banner/dgn_pillar/dgn_bars /
#             dgn_anvil/dgn_forge
#   規約: Y-up / 足元中心z=0 / 正面 +Y(→ゲーム-Z) / 1ブロック≒1m / 2MB以下・アニメ無し（静物）。
#     松明/燭台/炉/開いた宝箱の中身=Emission発光。角張った石/木/鉄（bevel+flat中心）で軽量。
#   用途: 王国城・砦・村の建物内部を 1号機 が組み合わせ配置（扉=入口の目印 / 階段=フロア移動 /
#         鍛冶道具=鍛冶屋NPCのそば＝鉱石で装備強化の舞台）。壁掛け物は背面=-Y側、正面+Yへ張り出す。

import bpy, os, math, mathutils
V=mathutils.Vector
scene=bpy.context.scene

def reset():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for blk in (bpy.data.meshes,bpy.data.materials,bpy.data.objects,bpy.data.actions):
        for it in list(blk):
            try: blk.remove(it)
            except Exception: pass
    parts.clear()

def mat(n,rgb,r=0.7,me=0.0,emis=None,es=2.5):
    m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*rgb,1.0);b.inputs["Roughness"].default_value=r;b.inputs["Metallic"].default_value=me
    if emis is not None:
        b.inputs["Emission Color"].default_value=(*emis,1.0); b.inputs["Emission Strength"].default_value=es
    return m

parts=[]
def cube(n,loc,s,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.rotation_euler=rot;o.data.materials.append(m);parts.append(o);return o
def cyl(n,loc,r,d,m,verts=14,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d,location=loc)
    o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);parts.append(o);return o
def cone(n,loc,r,d,m,verts=12,rot=(0,0,0),r2=0.0):
    bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r,radius2=r2,depth=d,location=loc)
    o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);parts.append(o);return o
def sphere(n,loc,s,m,segs=10,rings=7):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs,ring_count=rings,location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.data.materials.append(m);parts.append(o);return o

repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."));models=os.path.join(repo,"models");os.makedirs(models,exist_ok=True)

def finish(name, ratio=0.7, bevel=0.008, flat=True):
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts: o.select_set(True)
    bpy.context.view_layer.objects.active=parts[0]; bpy.ops.object.join()
    o=bpy.context.active_object; o.name=name
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel>0:
        bv=o.modifiers.new("B",'BEVEL'); bv.width=bevel; bv.segments=1; bpy.ops.object.modifier_apply(modifier=bv.name)
    if ratio<1.0:
        d=o.modifiers.new("D",'DECIMATE');d.decimate_type='COLLAPSE';d.ratio=ratio; bpy.ops.object.modifier_apply(modifier=d.name)
    bpy.ops.object.shade_flat() if flat else bpy.ops.object.shade_smooth()
    bpy.context.view_layer.update()
    xs=[(o.matrix_world@V(c)).x for c in o.bound_box]; ys=[(o.matrix_world@V(c)).y for c in o.bound_box]; zs=[(o.matrix_world@V(c)).z for c in o.bound_box]
    scene.cursor.location=((min(xs)+max(xs))/2,(min(ys)+max(ys))/2,min(zs))   # footprint中心・接地
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR'); o.location=(0,0,0)
    out=os.path.join(models,name+".glb")
    bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_animations=False)
    print("[voxel] %-18s -> %.3f MB  %.2fx%.2fx%.2f (W×D×H)"%(name,os.path.getsize(out)/1048576,max(xs)-min(xs),max(ys)-min(ys),max(zs)-min(zs)))

# ---- 共通マテリアル生成 ----
def WOOD():  return mat("Wood",(0.50,0.34,0.18),0.72)
def WOOD2(): return mat("Wood2",(0.37,0.25,0.13),0.72)
def WOOD3(): return mat("Wood3",(0.27,0.18,0.10),0.75)        # 暗い古材
def IRON():  return mat("Iron",(0.24,0.24,0.27),0.45,me=0.75)
def IRONK(): return mat("IronDark",(0.14,0.14,0.16),0.5,me=0.7)
def STONE(): return mat("Stone",(0.47,0.46,0.49),0.9)
def STONE2():return mat("Stone2",(0.37,0.36,0.40),0.92)
def GOLD():  return mat("Gold",(0.85,0.66,0.22),0.35,me=0.85)
def FLAME(): return mat("Flame",(1.0,0.5,0.12),0.3,emis=(1.0,0.46,0.10),es=5.5)
def FLAME2():return mat("Flame2",(1.0,0.82,0.34),0.3,emis=(1.0,0.80,0.32),es=4.0)

# ============================================================
# ① 扉
# ============================================================
# --- dgn_door_wood（石枠＋木板＋鉄帯＝ダンジョン入口の目印）---
reset()
W=WOOD(); W2=WOOD2(); IR=IRON(); ST=STONE2()
# 石のアーチ枠（左右柱＋まぐさ）
cube("FrameL",(-0.62,0,1.05),(0.12,0.16,1.05),ST); cube("FrameR",(0.62,0,1.05),(0.12,0.16,1.05),ST)
cube("Lintel",(0,0,2.05),(0.74,0.16,0.16),ST)
for i,x in enumerate((-0.4,-0.13,0.13,0.4)):                      # まぐさ上のアーチ石
    cube("Arch%d"%i,(x,0,2.22),(0.16,0.16,0.10),ST,rot=(0,math.radians(8*(i-1.5)),0))
# 木の扉板（縦板5枚・わずかに前へ）
for i,x in enumerate((-0.40,-0.20,0.0,0.20,0.40)):
    cube("Plank%d"%i,(x,0.05,1.0),(0.10,0.05,0.95),W if i%2==0 else W2)
# 鉄の帯＋鋲
for z in (0.45,1.55):
    cube("Band%.0f"%(z*10),(0,0.11,z),(0.52,0.03,0.07),IR)
    for x in (-0.4,0.0,0.4): sphere("Stud",(x,0.16,z),(0.04,0.03,0.04),IR,segs=8,rings=6)
# 取手（鉄の輪）
cyl("Ring",(0.22,0.13,1.0),0.08,0.025,IR,verts=14,rot=(math.radians(90),0,0))
finish("dgn_door_wood", ratio=0.7)

# --- dgn_door_iron（重厚な鉄扉・リベット・覗き格子）---
reset()
IR=IRON(); IK=IRONK(); ST=STONE2()
cube("FrameL",(-0.60,0,1.05),(0.12,0.18,1.05),ST); cube("FrameR",(0.60,0,1.05),(0.12,0.18,1.05),ST)
cube("Lintel",(0,0,2.05),(0.72,0.18,0.16),ST)
cube("Plate",(0,0.06,1.0),(0.50,0.06,0.95),IK)                   # 鉄板本体
cube("PlateTrim",(0,0.10,1.0),(0.44,0.03,0.88),IR)
# リベット格子
for z in (0.30,0.70,1.10,1.50,1.80):
    for x in (-0.42,-0.21,0.0,0.21,0.42): sphere("Riv",(x,0.14,z),(0.03,0.025,0.03),IR,segs=7,rings=5)
# 覗き格子（上部）＋取手
for x in (-0.10,0.02,0.14): cube("Bar",(x,0.14,1.62),(0.018,0.03,0.10),IR)
cube("Slot",(0,0.12,1.62),(0.18,0.02,0.12),IK)
cyl("Ring",(0.20,0.15,0.95),0.075,0.022,IR,verts=14,rot=(math.radians(90),0,0))
finish("dgn_door_iron", ratio=0.7)

# ============================================================
# ② 室内パーツ
# ============================================================
# --- dgn_torch_wall（壁掛け松明・背面-Yに台座・発光）---
reset()
IR=IRON(); WD=mat("TStick",(0.30,0.20,0.11),0.8); FL=FLAME(); FL2=FLAME2()
cube("Plate",(0,-0.10,1.0),(0.10,0.04,0.18),IR)                  # 壁付け台座(背面)
cube("Arm",(0,0.04,0.96),(0.03,0.14,0.03),IR,rot=(math.radians(-26),0,0))  # 前上へ伸びる腕
cyl("Cup",(0,0.18,1.06),0.07,0.10,IR,verts=12)                   # 受け皿
cyl("Stick",(0,0.16,0.96),0.025,0.34,WD,verts=8,rot=(math.radians(18),0,0))
cone("Flame",(0,0.19,1.22),0.09,0.30,FL,verts=12)               # 炎
cone("Flame2",(0,0.19,1.27),0.05,0.18,FL2,verts=10)
finish("dgn_torch_wall", ratio=0.7)

# --- dgn_candelabra（床置き燭台・3灯・発光）---
reset()
IR=IRON(); WX=mat("Wax",(0.92,0.88,0.74),0.6); FL=FLAME(); FL2=FLAME2()
cyl("Base",(0,0,0.05),0.20,0.10,IR,verts=16)
cyl("Pole",(0,0,0.78),0.04,1.5,IR,verts=10)
cyl("Knob",(0,0,0.55),0.07,0.08,IR,verts=12)
cube("ArmBar",(0,0,1.40),(0.42,0.03,0.03),IR)                    # 横木（左右灯）
for x in (-0.40,0.0,0.40):
    z=1.46 if x!=0 else 1.66
    cyl("Hold%.0f"%(x*10),(x,0,z-0.06),0.05,0.06,IR,verts=10)
    cyl("Candle%.0f"%(x*10),(x,0,z+0.06),0.035,0.16,WX,verts=8)
    cone("Fl%.0f"%(x*10),(x,0,z+0.22),0.04,0.12,FL,verts=8)
    cone("Fl2%.0f"%(x*10),(x,0,z+0.25),0.022,0.07,FL2,verts=8)
for x in (-0.40,0.40): cyl("ArmUp%.0f"%(x*10),(x,0,1.43),0.025,0.10,IR,verts=8)
finish("dgn_candelabra", ratio=0.72)

# --- dgn_chest_closed（宝箱・閉）---
def chest(open_lid):
    W=WOOD2(); W3=WOOD3(); IR=IRON(); GD=GOLD()
    cube("Box",(0,0,0.22),(0.36,0.26,0.22),W)                    # 本体
    for x in (-0.30,0.0,0.30): cube("BandV",(x,0,0.22),(0.03,0.27,0.22),IR)
    cube("BandH",(0,0,0.10),(0.37,0.27,0.03),IR)
    # 蓋（かまぼこ：3枚の傾き板）。open時は後方ヒンジで開く
    lid=[]
    def lidpart(n,loc,s,rot):
        o=cube(n,loc,s,W3,rot=rot); lid.append(o); return o
    base_z=0.46
    segs=[(-0.0,0.10),(0.0,0.0),(0.0,-0.10)]
    lidpart("LidTop",(0,0.0,base_z+0.06),(0.37,0.10,0.05),(0,0,0))
    lidpart("LidF",(0,0.18,base_z),(0.37,0.06,0.07),(math.radians(38),0,0))
    lidpart("LidB",(0,-0.18,base_z),(0.37,0.06,0.07),(math.radians(-38),0,0))
    cube("LidBandV",(0,0.0,base_z+0.04),(0.03,0.20,0.10),IR)
    lid.append(parts[-1])
    cube("Lock",(0,0.27,0.34),(0.06,0.03,0.06),GD); lid_lock=parts[-1]
    if open_lid:
        # 蓋＆錠を後方ヒンジ(y=-0.26,z=0.44)まわりに開く
        import mathutils as _mu
        piv=_mu.Vector((0,-0.26,0.44)); ang=math.radians(-105)
        rotm=_mu.Matrix.Rotation(ang,4,'X')
        for o in lid+[parts[-1]]:
            rel=o.location-piv; o.location=piv+rotm@rel
            o.rotation_euler[0]+=ang
        # 中身：金貨の山（発光）
        GLOW=mat("GoldGlow",(1.0,0.82,0.30),0.35,me=0.7,emis=(1.0,0.78,0.28),es=2.6)
        for i,(x,y) in enumerate([(0,0),(0.14,0.05),(-0.14,0.04),(0.07,-0.08),(-0.08,-0.07)]):
            cyl("Coin%d"%i,(x,y,0.30+0.02*(i%2)),0.07,0.03,GLOW,verts=10)
        sphere("Treasure",(0,0,0.34),(0.10,0.10,0.07),GLOW,segs=10,rings=7)

reset(); chest(False); finish("dgn_chest_closed", ratio=0.7)
reset(); chest(True);  finish("dgn_chest_open",   ratio=0.7)

# --- dgn_table（木テーブル）---
reset()
W=WOOD(); W2=WOOD2()
cube("Top",(0,0,0.74),(0.62,0.40,0.05),W)
cube("Apron",(0,0,0.66),(0.56,0.34,0.04),W2)
for (x,y) in [(0.54,0.32),(0.54,-0.32),(-0.54,0.32),(-0.54,-0.32)]:
    cube("Leg",(x,y,0.36),(0.05,0.05,0.36),W2)
finish("dgn_table", ratio=0.8, bevel=0.01)

# --- dgn_chair（椅子）---
reset()
W=WOOD(); W2=WOOD2()
cube("Seat",(0,0,0.45),(0.22,0.22,0.04),W)
cube("Back",(0,-0.18,0.66),(0.22,0.04,0.20),W)
for i,z in enumerate((0.74,0.62)): cube("Slat%d"%i,(0,-0.18,z),(0.18,0.03,0.025),W2)
for (x,y) in [(0.18,0.18),(0.18,-0.18),(-0.18,0.18),(-0.18,-0.18)]:
    cube("Leg",(x,y,0.22),(0.035,0.035,0.22),W2)
finish("dgn_chair", ratio=0.8, bevel=0.008)

# --- dgn_bookshelf（本棚・本入り）---
reset()
W=WOOD2(); W3=WOOD3()
cube("SideL",(0.42,0,1.0),(0.04,0.22,1.0),W3); cube("SideR",(-0.42,0,1.0),(0.04,0.22,1.0),W3)
cube("TopP",(0,0,1.98),(0.46,0.22,0.04),W3); cube("BotP",(0,0,0.04),(0.46,0.22,0.04),W3)
cube("Back",(0,-0.20,1.0),(0.42,0.02,1.0),W3)
shelf_z=(0.45,0.95,1.45)
for z in shelf_z: cube("Shelf%.0f"%(z*10),(0,0,z),(0.42,0.21,0.03),W)
# 本（各段に並ぶ・色とりどり・高さばらつき）
bookcols=[(0.55,0.16,0.14),(0.18,0.32,0.50),(0.20,0.42,0.22),(0.55,0.45,0.16),(0.36,0.20,0.45),(0.40,0.30,0.18)]
import random as _r; _r.seed(11)
for zi,z in enumerate((0.48,0.98,1.48,1.86)):
    x=-0.36
    while x<0.36:
        w=_r.uniform(0.035,0.07); h=_r.uniform(0.22,0.34)
        c=bookcols[_r.randrange(len(bookcols))]
        cube("Bk",(x+w,0.0,z+h/2),(w,0.16,h/2),mat("Book",c,0.8),rot=(0,math.radians(_r.uniform(-3,5)),0))
        x+=w*2+0.012
finish("dgn_bookshelf", ratio=0.75, bevel=0.005)

# --- dgn_barrel（ダンジョン樽・暗め）---
reset()
W=WOOD3(); IR=IRONK()
cyl("Body",(0,0,0.42),0.28,0.80,W,verts=16)
cyl("BodyMid",(0,0,0.42),0.31,0.28,W,verts=16)
for z in (0.12,0.42,0.72): cyl("Hoop",(0,0,z),0.315,0.05,IR,verts=16)
finish("dgn_barrel", ratio=0.72, bevel=0.01)

# ============================================================
# ③ 階段
# ============================================================
# --- dgn_stairs（石の直階段・段を箱で積む・1m上る・幅1.2m）---
reset()
ST=STONE(); ST2=STONE2()
N=6; depth=1.0; rise=1.0
for i in range(N):
    h=(i+1)*(rise/N)
    cube("Step%d"%i,(0,0.5-depth/N*(i+0.5),h/2),(0.60,depth/N/2+0.005,h/2),ST if i%2==0 else ST2)
# 側壁（左右の低い欄干）
for sx in (1,-1):
    cube("Rail%d"%sx,(0.61*sx,0.0,0.55),(0.04,depth/2,0.55),ST2)
finish("dgn_stairs", ratio=0.85, bevel=0.006)

# --- dgn_stairs_spiral（螺旋階段・中心柱＋回り段）---
reset()
ST=STONE(); ST2=STONE2(); IR=IRON()
cyl("Core",(0,0,1.1),0.12,2.2,ST2,verts=12)                     # 中心柱
NS=12
for i in range(NS):
    ang=math.radians(i*30); h=(i+0.5)*(2.0/NS)
    rx=math.cos(ang)*0.42; ry=math.sin(ang)*0.42
    cube("Tread%d"%i,(rx,ry,h),(0.34,0.16,0.05),ST if i%2==0 else ST2,rot=(0,0,ang))
    # 外周の手すり支柱（数段おき）
    if i%2==0:
        ox=math.cos(ang)*0.70; oy=math.sin(ang)*0.70
        cyl("Post%d"%i,(ox,oy,h+0.22),0.02,0.44,IR,verts=6)
finish("dgn_stairs_spiral", ratio=0.8, bevel=0.005)

# ============================================================
# ④ 装飾
# ============================================================
# --- dgn_banner（壁の旗/タペストリー・紋章入り）---
reset()
IR=IRON(); CL=mat("Banner",(0.58,0.12,0.14),0.85); CL2=mat("Banner2",(0.46,0.09,0.11),0.85)
GD=GOLD()
cyl("Rod",(0,0.02,2.2),0.025,0.94,IR,verts=10,rot=(0,math.radians(90),0))
for sx in (1,-1): sphere("RodCap",(0.46*sx,0.02,2.2),(0.04,0.04,0.04),GD,segs=8,rings=6)
# 布（縦の帯・下端は三角の切れ込み）
cube("Cloth",(0,0,1.35),(0.42,0.015,0.82),CL)
cube("ClothEdgeL",(-0.30,0.005,1.35),(0.04,0.012,0.82),CL2); cube("ClothEdgeR",(0.30,0.005,1.35),(0.04,0.012,0.82),CL2)
for i,x in enumerate((-0.28,0.0,0.28)):                         # 下端の燕尾
    cone("Tail%d"%i,(x,0,0.50),0.13,0.22,CL2,verts=4,rot=(math.radians(180),0,0))
# 紋章（金の菱形＋丸）
cube("Emblem",(0,0.02,1.55),(0.14,0.012,0.14),GD,rot=(0,0,math.radians(45)))
sphere("EmblemDot",(0,0.03,1.55),(0.06,0.012,0.06),CL,segs=8,rings=6)
finish("dgn_banner", ratio=0.8, bevel=0.0)

# --- dgn_pillar（石柱・基壇＋柱身＋柱頭）---
reset()
ST=STONE(); ST2=STONE2()
cube("Base",(0,0,0.10),(0.30,0.30,0.10),ST2)
cube("Base2",(0,0,0.22),(0.25,0.25,0.05),ST)
cyl("Shaft",(0,0,1.35),0.18,2.1,ST,verts=14)
for zi,z in enumerate((0.6,1.1,1.6,2.1)): cyl("Flute%d"%zi,(0,0,z),0.185,0.02,ST2,verts=14)  # 横溝
cube("Cap",(0,0,2.46),(0.26,0.26,0.06),ST2)
cube("Cap2",(0,0,2.55),(0.30,0.30,0.05),ST)
finish("dgn_pillar", ratio=0.8, bevel=0.006)

# --- dgn_bars（鉄格子・牢屋風・石枠＋縦鉄棒）---
reset()
ST=STONE2(); IR=IRON(); IK=IRONK()
cube("FrameL",(-0.62,0,1.15),(0.10,0.12,1.15),ST); cube("FrameR",(0.62,0,1.15),(0.10,0.12,1.15),ST)
cube("FrameT",(0,0,2.24),(0.72,0.12,0.10),ST); cube("FrameB",(0,0,0.06),(0.72,0.12,0.06),ST)
for x in (-0.45,-0.27,-0.09,0.09,0.27,0.45):
    cyl("Bar%.0f"%(x*100),(x,0,1.15),0.022,2.2,IR,verts=8)
for z in (0.55,1.7): cyl("Cross%.0f"%(z*10),(0,0.03,z),0.02,1.2,IK,verts=8,rot=(0,math.radians(90),0))
finish("dgn_bars", ratio=0.8, bevel=0.004)

# ============================================================
# ⑤ 鍛冶屋の道具（鉱石で装備強化の舞台）
# ============================================================
# --- dgn_anvil（金床・木の切株台）---
reset()
IR=IRON(); IK=IRONK(); WD=WOOD3()
cyl("Stump",(0,0,0.28),0.22,0.56,WD,verts=14)                   # 切株台
for z in (0.12,0.44): cyl("Ring",(0,0,z),0.225,0.03,IK,verts=14)
cube("Waist",(0,0,0.62),(0.13,0.18,0.08),IK)                    # くびれ
cube("Body",(0,0,0.74),(0.20,0.34,0.10),IR)                     # 上面の台
cone("Horn",(0,0.40,0.74),0.10,0.30,IR,verts=10,rot=(math.radians(90),0,0),r2=0.02)  # 角(前+Y)
cube("Heel",(0,-0.32,0.74),(0.16,0.10,0.10),IR)                 # 後ろのかかと
# 槌（添え物・台の上）
cube("HammerH",(0.12,-0.05,0.86),(0.06,0.10,0.05),IK)
cyl("HammerG",(0.12,-0.05,0.80),0.018,0.16,WD,verts=8)
finish("dgn_anvil", ratio=0.72, bevel=0.006)

# --- dgn_forge（炉・石炉＋燃える炭(発光)＋煙突フード＋ふいご）---
reset()
ST=STONE(); ST2=STONE2(); IR=IRON(); WD=WOOD3()
COAL=mat("Coal",(0.9,0.30,0.06),0.5,emis=(1.0,0.40,0.07),es=6.5)
COAL2=mat("Coal2",(1.0,0.70,0.25),0.4,emis=(1.0,0.66,0.22),es=4.5)
# 石の炉台（箱）
cube("Hearth",(0,0,0.45),(0.55,0.45,0.45),ST)
cube("HearthTop",(0,0,0.92),(0.57,0.47,0.04),ST2)
cube("Pit",(0,0.0,0.92),(0.30,0.26,0.05),mat("Char",(0.06,0.05,0.05),0.95))  # 炉床のくぼみ(黒)
# 燃える炭
for i,(x,y) in enumerate([(0,0),(0.14,0.06),(-0.13,0.05),(0.08,-0.09),(-0.10,-0.08),(0.0,0.10)]):
    sphere("Coal%d"%i,(x,y,0.95),(0.07,0.07,0.05),COAL if i%2 else COAL2,segs=8,rings=6)
cone("Ember",(0,0,1.06),0.12,0.20,COAL2,verts=10)               # 立ち昇る熱
# 煙突フード（上の傘）
for i,x in enumerate((-1,1)):
    cube("Hood%d"%i,(x*0.20,-0.12,1.45),(0.30,0.30,0.02),ST2,rot=(0,math.radians(28*x),0))
cube("HoodBack",(0,-0.42,1.5),(0.5,0.04,0.5),ST2)
cyl("Flue",(0,-0.30,1.95),0.14,0.5,ST2,verts=12)
# ふいご（横の革袋）
cube("Bellow",(0.66,-0.05,0.70),(0.12,0.22,0.14),WD)
cone("BNozzle",(0.52,0.10,0.78),0.05,0.18,IR,verts=8,rot=(math.radians(90),0,math.radians(20)))
for z in (0.60,0.80): cube("BSlat",(0.66,-0.05,z),(0.13,0.20,0.01),IR)
finish("dgn_forge", ratio=0.7, bevel=0.006)

print("[voxel] dungeon interior set done (17 parts)")
