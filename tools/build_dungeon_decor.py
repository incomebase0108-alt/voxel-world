# -*- coding: utf-8 -*-
# VOXEL WORLD - ダンジョン装飾・罠・タイル・看板・宝物（dgn_*・第2弾）
# blender --background --python tools/build_dungeon_decor.py
#   出力(12):
#     ①ボス部屋: dgn_altar_boss / dgn_throne / dgn_magic_floor
#     ②罠      : dgn_spike_trap / dgn_trapdoor
#     ③床壁    : dgn_floor_stone / dgn_wall_mossy / dgn_wall_cracked
#     ④看板    : dgn_sign_wood（板面は+Y正面・平ら＝1号機がテキストを乗せる）
#     ⑤宝物    : dgn_treasure_gold / dgn_gems / dgn_crown（宝箱の報酬の見た目）
#   規約: Y-up / 足元中心z=0 / 正面 +Y(→ゲーム-Z) / 1ブロック≒1m / 2MB以下・アニメ無し（静物）。
#     魔法陣/祭壇の紋様/宝物=Emission発光。タイルは1m角でグリッド敷設前提。壁は背面=-Y。

import bpy, os, math, mathutils, random
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
def ico(n,loc,s,m,subd=1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subd,location=loc)
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
    scene.cursor.location=((min(xs)+max(xs))/2,(min(ys)+max(ys))/2,min(zs))
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR'); o.location=(0,0,0)
    out=os.path.join(models,name+".glb")
    bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_animations=False)
    print("[voxel] %-18s -> %.3f MB  %.2fx%.2fx%.2f (W×D×H)"%(name,os.path.getsize(out)/1048576,max(xs)-min(xs),max(ys)-min(ys),max(zs)-min(zs)))

def STONE(): return mat("Stone",(0.47,0.46,0.49),0.9)
def STONE2():return mat("Stone2",(0.37,0.36,0.40),0.92)
def STONE3():return mat("Stone3",(0.28,0.27,0.31),0.93)
def IRON():  return mat("Iron",(0.24,0.24,0.27),0.45,me=0.75)
def IRONK(): return mat("IronDark",(0.14,0.14,0.16),0.5,me=0.7)
def GOLD():  return mat("Gold",(0.86,0.67,0.22),0.32,me=0.9)
def GOLD2(): return mat("Gold2",(0.70,0.50,0.16),0.4,me=0.85)
def WOOD():  return mat("Wood",(0.50,0.34,0.18),0.72)
def WOOD2(): return mat("Wood2",(0.37,0.25,0.13),0.72)
def WOOD3(): return mat("Wood3",(0.27,0.18,0.10),0.75)

# ============================================================
# ① ボス部屋の装飾
# ============================================================
# --- dgn_altar_boss（荘厳な祭壇・段重ね＋発光クリスタル＋ルーン）---
reset()
ST=STONE(); ST2=STONE2(); ST3=STONE3(); GD=GOLD()
RUNE=mat("Rune",(0.45,0.18,0.62),0.5,emis=(0.78,0.34,0.98),es=4.0)        # 紫のルーン発光
CRY =mat("AltarCry",(0.55,0.30,0.85),0.25,emis=(0.70,0.38,1.0),es=5.0)    # 中央クリスタル
# 段重ねの基壇（八角風＝45度回した2枚重ね）
cyl("Tier0",(0,0,0.10),0.85,0.20,ST2,verts=8)
cyl("Tier1",(0,0,0.28),0.70,0.18,ST,verts=8)
cyl("Tier2",(0,0,0.46),0.55,0.18,ST2,verts=8)
# 天板＋金縁
cyl("Top",(0,0,0.60),0.50,0.10,ST,verts=8)
cyl("GoldRim",(0,0,0.66),0.50,0.03,GD,verts=8)
# 側面のルーン（発光する刻み）
for i in range(8):
    a=math.radians(i*45); cube("Rune%d"%i,(math.cos(a)*0.55,math.sin(a)*0.55,0.40),(0.05,0.05,0.10),RUNE,rot=(0,0,a))
# 四隅の小柱＋火皿
for i in range(4):
    a=math.radians(45+i*90); x=math.cos(a)*0.62; y=math.sin(a)*0.62
    cyl("Pil%d"%i,(x,y,0.42),0.06,0.84,ST3,verts=6)
    cyl("Bowl%d"%i,(x,y,0.86),0.09,0.08,IRONK(),verts=8)
    cone("Fl%d"%i,(x,y,0.98),0.06,0.16,mat("AltFl",(0.6,0.4,1.0),0.3,emis=(0.62,0.40,1.0),es=4.5),verts=8)
# 中央の供物クリスタル
cone("Crystal",(0,0,0.92),0.16,0.52,CRY,verts=6)
cone("CrystalB",(0,0,0.74),0.12,-0.22,CRY,verts=6)        # 下向きの尖り
ico("Glow",(0,0,0.84),(0.10,0.10,0.10),CRY,subd=1)
finish("dgn_altar_boss", ratio=0.7)

# --- dgn_throne（玉座・高背＋金縁＋赤クッション＋角の意匠）---
reset()
ST=STONE(); ST2=STONE2(); ST3=STONE3(); GD=GOLD(); GD2=GOLD2()
CUSH=mat("Cushion",(0.55,0.10,0.12),0.8); HORN=mat("ThroneHorn",(0.86,0.80,0.66),0.6)
# 台座と座面
cube("Plinth",(0,0,0.12),(0.62,0.58,0.12),ST2)
cube("Seat",(0,0,0.55),(0.50,0.46,0.10),ST)
cube("Cushion",(0,0.02,0.63),(0.42,0.38,0.05),CUSH)
# 高い背もたれ（上に向け広がる）＋頂部の尖り
cube("Back",(0,-0.40,1.35),(0.50,0.10,0.80),ST)
cube("BackTrim",(0,-0.33,1.35),(0.40,0.04,0.72),GD2)
cube("BackInlay",(0,-0.30,1.30),(0.30,0.02,0.55),CUSH)
for i,x in enumerate((-0.46,0.0,0.46)):
    cone("Spire%d"%i,(x,-0.40,2.18+(-0.18 if x else 0.12)),0.10,0.40 if x==0 else 0.30,ST2,verts=6)
# 王の角の意匠（背の上部左右）
for sgn in (1,-1):
    cone("Horn%d"%sgn,(0.40*sgn,-0.36,2.05),0.07,0.46,HORN,verts=6,rot=(math.radians(20),0,math.radians(26*sgn)))
# 肘掛け＋金の親柱（竜頭の簡略）
for sgn in (1,-1):
    cube("Arm%d"%sgn,(0.46*sgn,0.0,0.78),(0.06,0.40,0.06),ST2)
    cube("ArmPost%d"%sgn,(0.46*sgn,0.34,0.70),(0.07,0.07,0.22),ST3)
    sphere("Knob%d"%sgn,(0.46*sgn,0.34,0.86),(0.08,0.08,0.08),GD,segs=10,rings=7)
# 脚
for (x,y) in [(0.44,0.40),(0.44,-0.40),(-0.44,0.40),(-0.44,-0.40)]:
    cube("Leg",(x,y,0.22),(0.06,0.06,0.22),ST3)
finish("dgn_throne", ratio=0.72)

# --- dgn_magic_floor（魔法陣の床模様・fx_magic_circle静物版・床に薄く発光）---
reset()
Z=0.025
CRIM=mat("McCrim",(0.50,0.05,0.09),0.6,emis=(0.98,0.13,0.20),es=4.6)
VIOL=mat("McViol",(0.30,0.07,0.46),0.6,emis=(0.66,0.26,1.0),es=5.2)
GLOW=mat("McGlow",(0.85,0.55,1.0),0.5,emis=(0.88,0.62,1.0),es=6.0)
RUNE=mat("McRune",(0.42,0.12,0.55),0.6,emis=(0.82,0.32,0.98),es=4.4)
# 外輪（深紅・薄いトーラス×2）。リング間の地は仄暗い紫（黒潰れ回避）
cyl("RingO",(0,0,Z),1.20,0.04,CRIM,verts=48); cyl("RingOi",(0,0,Z+0.001),1.10,0.05,mat("Hole",(0.10,0.04,0.15),0.9),verts=48)
cyl("RingM",(0,0,Z),0.86,0.035,CRIM,verts=44); cyl("RingMi",(0,0,Z+0.001),0.80,0.05,mat("Hole2",(0.08,0.03,0.13),0.9),verts=44)
# 外周ルーン刻み
for i in range(24):
    a=2*math.pi*i/24; cube("Rn%d"%i,(1.14*math.cos(a),1.14*math.sin(a),Z),(0.05,0.10 if i%2==0 else 0.05,0.012),RUNE,rot=(0,0,a))
# 六芒星（紫・三角2枚を細長cubeの辺で）
def star_tri(flip,R=0.78):
    vs=[(R*math.cos(math.radians(90+120*k+(180 if flip else 0))),R*math.sin(math.radians(90+120*k+(180 if flip else 0)))) for k in range(3)]
    for k in range(3):
        x0,y0=vs[k]; x1,y1=vs[(k+1)%3]; mx,my=(x0+x1)/2,(y0+y1)/2
        ang=math.atan2(y1-y0,x1-x0); ln=math.hypot(x1-x0,y1-y0)
        cube("St",(mx,my,Z),(ln/2,0.028,0.012),VIOL,rot=(0,0,ang))
star_tri(False); star_tri(True)
cyl("RingIn",(0,0,Z),0.70,0.026,VIOL,verts=40)
# 中央グロウ
cyl("Core",(0,0,Z),0.26,0.018,GLOW,verts=28)
finish("dgn_magic_floor", ratio=0.85, bevel=0.0)

# ============================================================
# ② 罠
# ============================================================
# --- dgn_spike_trap（床から突き出る鉄棘・1m角の踏板＋棘群）---
reset()
ST2=STONE2(); ST3=STONE3(); IR=IRON(); IK=IRONK()
cube("Plate",(0,0,0.05),(0.48,0.48,0.05),ST3)               # 床に沈む踏板
cube("Rim",(0,0,0.02),(0.50,0.50,0.02),ST2)                 # 枠
random.seed(5)
for gx in (-0.30,-0.10,0.10,0.30):
    for gy in (-0.30,-0.10,0.10,0.30):
        h=random.uniform(0.34,0.56); jx=random.uniform(-0.03,0.03); jy=random.uniform(-0.03,0.03)
        cone("Spike",(gx+jx,gy+jy,0.10+h/2),0.06,h,IR if (round(gx*10)+round(gy*10))%2 else IK,verts=6)
# 少数の血錆（暗赤）で凄み
for (x,y) in [(0.1,0.0),(-0.2,0.15)]:
    cube("Rust",(x,y,0.11),(0.06,0.06,0.005),mat("Rust",(0.30,0.07,0.05),0.9))
finish("dgn_spike_trap", ratio=0.72, bevel=0.004)

# --- dgn_trapdoor（落とし穴の蓋・ひび割れた板＋暗い穴の縁＋蝶番）---
reset()
WD=WOOD2(); WD3=WOOD3(); IR=IRON(); VOID=mat("Void",(0.02,0.02,0.03),1.0)
cube("Frame",(0,0,0.06),(0.52,0.52,0.06),STONE2())          # 石枠
cube("Hole",(0,0,0.05),(0.44,0.44,0.05),VOID)               # 奥の闇（穴）
# 蓋（少しずれて開きかけ・板4枚）
for i,x in enumerate((-0.30,-0.10,0.10,0.30)):
    sag=0.0 if i in (0,3) else -0.02
    cube("Plank%d"%i,(x*0.9,0.02,0.11+sag),(0.095,0.42,0.03),WD if i%2 else WD3,rot=(math.radians(2*(i-1.5)),0,0))
cube("BandA",(0,0.0,0.12),(0.40,0.05,0.025),IR,rot=(0,0,0))
cube("BandB",(0,0.0,0.12),(0.05,0.40,0.025),IR)
# 蝶番（後縁）＋取手
for x in (-0.28,0.28): cube("Hinge",(x,-0.42,0.12),(0.05,0.08,0.02),IR)
cyl("Ring",(0,0.30,0.13),0.06,0.02,IR,verts=12,rot=(math.radians(90),0,0))
# ひび割れ（板上の暗い筋）
for (x,y,a) in [(-0.05,0.1,20),(0.12,-0.08,-35)]:
    cube("Crack",(x,y,0.135),(0.18,0.008,0.004),mat("Crk",(0.06,0.05,0.04),0.9),rot=(0,0,math.radians(a)))
finish("dgn_trapdoor", ratio=0.75, bevel=0.004)

# ============================================================
# ③ 床/壁タイル（1m角・グリッド敷設）
# ============================================================
# --- dgn_floor_stone（石畳の床・1m角・凹凸の敷石）---
reset()
ST=STONE(); ST2=STONE2(); ST3=STONE3()
cube("Slab",(0,0,0.05),(0.50,0.50,0.05),ST3)                # 下地
random.seed(3)
mats=[ST,ST2,ST3]
# 敷石（4x4・目地で隙間・高さ微差）
for ix in range(4):
    for iy in range(4):
        x=-0.375+ix*0.25; y=-0.375+iy*0.25
        s=0.108+random.uniform(-0.008,0.008); h=0.06+random.uniform(0.0,0.02)
        cube("Cobble",(x,y,0.05+h/2),(s,s,h/2),mats[(ix+iy)%3],rot=(0,0,math.radians(random.uniform(-3,3))))
finish("dgn_floor_stone", ratio=0.8, bevel=0.006)

# --- dgn_wall_mossy（苔むした石壁・1m角・背面-Y）---
reset()
ST=STONE(); ST2=STONE2(); ST3=STONE3(); MOSS=mat("Moss",(0.22,0.36,0.13),0.95); MOSS2=mat("Moss2",(0.16,0.28,0.10),0.95)
cube("Back",(0,-0.06,0.5),(0.50,0.06,0.50),ST3)             # 壁下地
random.seed(8); mats=[ST,ST2,ST3]
# 石積み（段違いレンガ）
for iy in range(4):
    off=0.0 if iy%2==0 else 0.12
    x=-0.5+off
    while x<0.5:
        w=random.uniform(0.10,0.16)
        cube("Brick",(min(x+w,0.46),0.02,0.13+iy*0.245),(min(w,0.46-x) if x+w>0.46 else w,0.05,0.115),mats[random.randrange(3)])
        x+=w*2+0.02
# 苔（下側・隙間に多め）
for (mx,mz,s) in [(-0.3,0.12,0.16),(0.1,0.18,0.20),(0.34,0.30,0.14),(-0.12,0.40,0.12),(0.22,0.62,0.10),(-0.36,0.7,0.1)]:
    ico("Moss",(mx,0.06,mz),(s,0.04,s*0.7),MOSS if (mx>0) else MOSS2,subd=1)
finish("dgn_wall_mossy", ratio=0.72, bevel=0.005)

# --- dgn_wall_cracked（ひび割れた石壁・1m角・崩れ欠け＋亀裂）---
reset()
ST=STONE(); ST2=STONE2(); ST3=STONE3(); CRK=mat("Crack",(0.06,0.06,0.07),0.95)
cube("Back",(0,-0.06,0.5),(0.50,0.06,0.50),ST3)
random.seed(12); mats=[ST,ST2,ST3]
for iy in range(4):
    off=0.0 if iy%2==0 else 0.12
    x=-0.5+off
    while x<0.5:
        w=random.uniform(0.10,0.16)
        # 一部の石を欠けさせる（小さく沈める＝崩れ）
        broken=random.random()<0.22
        h=0.115*(0.5 if broken else 1.0); zz=0.13+iy*0.245-(0.05 if broken else 0)
        cube("Brick",(min(x+w,0.46),0.02,zz),(min(w,0.46-x) if x+w>0.46 else w,0.05,h),mats[random.randrange(3)])
        x+=w*2+0.02
# 走る亀裂（枝分かれ）
def crackline(x0,z0,seg,ang):
    x,z=x0,z0
    for i in range(seg):
        ln=random.uniform(0.10,0.18); a=math.radians(ang+random.uniform(-25,25))
        nx=x+math.cos(a)*ln; nz=z+math.sin(a)*ln
        cube("Crk",( (x+nx)/2,0.055,(z+nz)/2),(ln/2,0.012,0.012),CRK,rot=(math.atan2(nz-z,1)*0,0,a))
        x,z=nx,nz
crackline(-0.1,0.95,5,-78); crackline(0.18,0.55,3,-110)
# 大きな欠落穴（暗い）
cube("Hole",(0.22,0.0,0.36),(0.14,0.05,0.12),CRK)
finish("dgn_wall_cracked", ratio=0.72, bevel=0.005)

# ============================================================
# ④ 看板・標識（板面=+Y正面・平ら／1号機がテキストを乗せる）
# ============================================================
reset()
W=WOOD(); W2=WOOD2(); W3=WOOD3(); IR=IRON()
# 2本柱の立て看板
for x in (-0.42,0.42): cube("Post",(x,0,0.62),(0.06,0.06,0.62),W3)
cube("Board",(0,0.02,1.05),(0.50,0.04,0.30),W)             # 板（前面+Y＝テキスト面）
cube("FrameT",(0,0.0,1.37),(0.54,0.05,0.04),W2); cube("FrameB",(0,0.0,0.73),(0.54,0.05,0.04),W2)
cube("FrameL",(-0.50,0.0,1.05),(0.04,0.05,0.34),W2); cube("FrameR",(0.50,0.0,1.05),(0.04,0.05,0.34),W2)
# 鉄の鋲（四隅）
for (x,z) in [(-0.46,1.30),(0.46,1.30),(-0.46,0.80),(0.46,0.80)]:
    sphere("Stud",(x,0.05,z),(0.03,0.025,0.03),IR,segs=7,rings=5)
# 上の小屋根（雨除け・装飾）
for i,x in enumerate((-0.18,0.18)):
    cube("Roof%d"%i,(x,-0.02,1.46),(0.22,0.18,0.02),W2,rot=(0,math.radians(22*(1 if x>0 else -1)),0))
finish("dgn_sign_wood", ratio=0.78, bevel=0.006)

# ============================================================
# ⑤ 宝物（宝箱の報酬の見た目）
# ============================================================
# --- dgn_treasure_gold（金貨の山・発光）---
reset()
GD=GOLD(); GLOW=mat("CoinGlow",(1.0,0.82,0.32),0.32,me=0.7,emis=(1.0,0.78,0.30),es=2.4)
random.seed(7)
# 盛り上がった山（円錐状に積む）
for ring,(rad,zz,nn) in enumerate([(0.30,0.03,12),(0.22,0.09,9),(0.14,0.15,6),(0.06,0.21,3)]):
    for i in range(nn):
        a=2*math.pi*i/nn + ring*0.5; x=math.cos(a)*rad*random.uniform(0.7,1.0); y=math.sin(a)*rad*random.uniform(0.7,1.0)
        cyl("Coin",(x,y,zz),0.075,0.025,GLOW if (i+ring)%3==0 else GD,verts=10,rot=(math.radians(random.uniform(-18,18)),0,0))
cyl("Tip",(0,0,0.25),0.06,0.03,GLOW,verts=10)
# こぼれ落ちた数枚
for (x,y) in [(0.34,0.06),(-0.30,-0.12),(0.12,-0.34),(-0.18,0.30)]:
    cyl("Spill",(x,y,0.02),0.07,0.022,GD,verts=10,rot=(math.radians(82),0,math.radians(random.uniform(0,180))))
finish("dgn_treasure_gold", ratio=0.7, bevel=0.004)

# --- dgn_gems（宝石の小山・色とりどり・発光）---
reset()
GD2=GOLD2()
gemcol=[("Ruby",(0.85,0.10,0.18)),("Sapph",(0.14,0.30,0.85)),("Emer",(0.12,0.72,0.34)),
        ("Topaz",(0.95,0.74,0.18)),("Amethyst",(0.55,0.22,0.78))]
cyl("Base",(0,0,0.03),0.26,0.06,GD2,verts=14)               # 小皿
random.seed(9)
spots=[(0,0,0.14,0.13),(0.13,0.05,0.10,0.10),(-0.12,0.06,0.10,0.09),(0.05,-0.12,0.09,0.08),
       (-0.10,-0.10,0.11,0.09),(0.16,-0.04,0.08,0.07),(-0.04,0.14,0.08,0.07)]
for i,(x,y,z,s) in enumerate(spots):
    nm,c=gemcol[i%len(gemcol)]
    GM=mat("Gem_%s"%nm,c,0.18,emis=tuple(min(1,v*1.1) for v in c),es=2.2)
    ico("Gem%d"%i,(x,y,z),(s,s,s*1.25),GM,subd=1)
finish("dgn_gems", ratio=0.8, bevel=0.006)

# --- dgn_crown（王冠・金＋宝石）---
reset()
GD=GOLD(); GD2=GOLD2()
cyl("Band",(0,0,0.10),0.20,0.12,GD,verts=20)
cyl("BandIn",(0,0,0.10),0.175,0.13,mat("CrownHole",(0.10,0.08,0.05),0.6,me=0.5),verts=20)
cyl("Rim",(0,0,0.04),0.21,0.03,GD2,verts=20)
# 頂点の山（5つの尖り＋間に宝石）
gemc=[(0.85,0.10,0.18),(0.14,0.30,0.85),(0.12,0.72,0.34),(0.95,0.74,0.18),(0.55,0.22,0.78)]
for i in range(5):
    a=2*math.pi*i/5; x=math.cos(a)*0.20; y=math.sin(a)*0.20
    cone("Point%d"%i,(x,y,0.24),0.05,0.18,GD,verts=6)
    GM=mat("CGem%d"%i,gemc[i],0.18,emis=tuple(min(1,v*1.1) for v in gemc[i]),es=2.0)
    ico("CGem%d"%i,(math.cos(a)*0.205,math.sin(a)*0.205,0.14),(0.035,0.035,0.045),GM,subd=1)
# 中央前の大粒
ico("BigGem",(0,0.205,0.13),(0.05,0.04,0.06),mat("BigGem",(0.85,0.10,0.18),0.18,emis=(0.95,0.12,0.20),es=2.4),subd=1)
finish("dgn_crown", ratio=0.78, bevel=0.005)

print("[voxel] dungeon decor/trap/tile/sign/treasure set done (12 parts)")
