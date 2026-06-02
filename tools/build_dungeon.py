# -*- coding: utf-8 -*-
# VOXEL WORLD - 構造物用モデル群②：ダンジョン要素
# Blender 5.1 / headless: blender --background --python tools/build_dungeon.py
#   出力: models/struct_chest.glb / struct_spawner.glb / struct_torch.glb / struct_altar.glb
#   規約: Y-up / 足元中心が原点(z=0) / 正面 Blender+Y(=glTF -Z) / 1ブロック≒1m。
#   アニメ（NLAクリップ内包・golem方式踏襲）:
#     chest   : idle(閉) / open(蓋が後方へ開く)  ← 1号機は open を順再生で開、逆再生で閉
#     spawner : idle(中の小型像が回転＋上下)
#     torch   : idle(炎の揺らぎ＝scale脈動)
#     altar   : idle(浮遊する魔石が上下＋ゆっくり回転)
#   1号機②の構造物自動生成(ダンジョン)に直結。

import bpy, os, math, mathutils
V=mathutils.Vector
scene=bpy.context.scene; scene.render.fps=24

def reset_all():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for blk in (bpy.data.meshes,bpy.data.materials,bpy.data.objects,bpy.data.actions):
        for it in list(blk):
            try: blk.remove(it)
            except Exception: pass

def mat(n,rgb,r=0.7,me=0.0,alpha=1.0,emis=None):
    m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*rgb,alpha);b.inputs["Roughness"].default_value=r;b.inputs["Metallic"].default_value=me
    if alpha<1.0:
        b.inputs["Alpha"].default_value=alpha
        try: m.blend_method='BLEND'
        except Exception: pass
    if emis is not None:
        b.inputs["Emission Color"].default_value=(*emis,1.0); b.inputs["Emission Strength"].default_value=4.0
    return m

def cube(g,n,loc,s,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.rotation_euler=rot;o.data.materials.append(m);g.append(o);return o
def cyl(g,n,loc,r,d,m,verts=16,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d,location=loc)
    o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);g.append(o);return o
def sphere(g,n,loc,s,m,segs=14,rings=8):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs,ring_count=rings,location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.data.materials.append(m);g.append(o);return o
def cone(g,n,loc,r,d,m,verts=14,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r,radius2=0.0,depth=d,location=loc)
    o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);g.append(o);return o

def join(group,name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in group:o.select_set(True)
    bpy.context.view_layer.objects.active=group[0];bpy.ops.object.join()
    o=bpy.context.active_object;o.name=name;return o
def set_origin(o,p):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    scene.cursor.location=p;bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
def apply_scale(o):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
def parent(c,p):
    bpy.ops.object.select_all(action='DESELECT');c.select_set(True);p.select_set(True)
    bpy.context.view_layer.objects.active=p;bpy.ops.object.parent_set(type='OBJECT',keep_transform=True)
def ground_snap(objs,root):
    bpy.context.view_layer.update()
    minz=min((o.matrix_world@V(c)).z for o in objs for c in o.bound_box)
    root.location.z-=minz
def new_action(o,n):
    if o.animation_data is None:o.animation_data_create()
    a=bpy.data.actions.new(n);a.use_fake_user=True;o.animation_data.action=a;return a
def push(o,t):
    ad=o.animation_data;act=ad.action;tr=ad.nla_tracks.new();tr.name=t
    tr.strips.new(act.name,int(act.frame_range[0]),act);ad.action=None
def krx(o,f,d):o.rotation_euler[0]=math.radians(d);o.keyframe_insert('rotation_euler',index=0,frame=f)
def krz(o,f,d):o.rotation_euler[2]=math.radians(d);o.keyframe_insert('rotation_euler',index=2,frame=f)
def kz(o,f,z):o.location.z=z;o.keyframe_insert('location',index=2,frame=f)
def ks(o,f,s):o.scale=(s,s,s);o.keyframe_insert('scale',frame=f)

repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."));models=os.path.join(repo,"models");os.makedirs(models,exist_ok=True)
def export_glb(name):
    bpy.ops.object.select_all(action='SELECT')
    out=os.path.join(models,name+".glb")
    bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_yup=True,
        export_apply=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_optimize_animation_size=True)
    zs=[]
    for o in bpy.context.scene.objects:
        if o.type=='MESH':
            for v in o.bound_box: zs.append((o.matrix_world@V(v)).z)
    sz=os.path.getsize(out)
    print("[voxel] %-16s -> %.3f MB  height=%.2fm feet=%.3f"%(name, sz/1048576, max(zs), min(zs)))

# =================================================================== 宝箱 chest
reset_all()
WOOD=mat("ChestWood",(0.55,0.36,0.18),0.6); DW=mat("ChestDark",(0.36,0.22,0.10),0.6)
IRON=mat("ChestIron",(0.22,0.20,0.18),0.4,me=0.85); GOLD=mat("Lock",(0.85,0.68,0.22),0.3,me=0.8)
BASE=[]; LID=[]
# 箱本体（front=+Y）
cube(BASE,"Box",(0,0,0.21),(0.40,0.30,0.21),WOOD)
for x in (-0.40,0.40):
    cube(BASE,"BandV",(x,0,0.21),(0.025,0.31,0.21),IRON)     # 縦の鉄帯
cube(BASE,"BandFront",(0,0.30,0.21),(0.40,0.02,0.21),DW)
# 蓋（後方ヒンジ=-Y側、上面）
cube(LID,"Lid",(0,0,0.49),(0.40,0.30,0.10),WOOD)
for x in (-0.40,0.40):
    cube(LID,"LidBandV",(x,0,0.49),(0.025,0.31,0.10),IRON)
cube(LID,"LidFront",(0,0.30,0.49),(0.40,0.02,0.10),DW)
cube(LID,"LockPlate",(0,0.31,0.40),(0.07,0.02,0.06),GOLD)    # 前面の錠前
base=join(BASE,"ChestBase"); lid=join(LID,"ChestLid")
set_origin(base,(0,0,0))
set_origin(lid,(0,-0.30,0.42))   # ヒンジ＝後方(-Y)・蓋下端
for o in (base,lid): apply_scale(o)
parent(lid,base)
ground_snap((base,lid),base)
# idle（閉じたまま）/ open（後方へ開く＝+X回転で前縁が持ち上がる）
new_action(lid,"lid_idle");
for f in (1,40): krx(lid,f,0)
push(lid,"idle")
new_action(lid,"lid_open")
for f,d in [(1,0),(16,105),(40,105)]: krx(lid,f,d)
push(lid,"open")
export_glb("struct_chest")

# =================================================================== スポナー spawner
reset_all()
BAR=mat("Bars",(0.18,0.18,0.20),0.45,me=0.7); CORE=mat("SpawnCore",(0.45,0.85,0.55),0.2,emis=(0.3,1.0,0.4))
DARK=mat("Mini",(0.10,0.12,0.14),0.6)
CAGE=[]; MINI=[]
# 鉄格子の立方体フレーム。1辺≒0.9、z 0..0.9
s=0.45; r=0.035
# 四隅の縦柱
for (x,y) in [(-s,-s),(s,-s),(-s,s),(s,s)]:
    cube(CAGE,"Pillar",(x,y,0.45),(r,r,s),BAR)
# 上下＋中段の横桟（X方向2本・Y方向2本 × 3段）
for zc in (0.06,0.45,0.84):
    for y in (-s,s): cube(CAGE,"RX",(0,y,zc),(s,r,r),BAR)
    for x in (-s,s): cube(CAGE,"RY",(x,0,zc),(r,s,r),BAR)
# 中の小型像（回転＋上下するモブ影）
cube(MINI,"MiniBody",(0,0,0.40),(0.12,0.10,0.14),DARK)
cube(MINI,"MiniHead",(0,0.02,0.58),(0.09,0.09,0.09),DARK)
sphere(MINI,"MiniEyeL",(0.04,0.10,0.59),(0.018,0.012,0.018),CORE,segs=8,rings=6)
sphere(MINI,"MiniEyeR",(-0.04,0.10,0.59),(0.018,0.012,0.018),CORE,segs=8,rings=6)
cage=join(CAGE,"SpawnerCage"); mini=join(MINI,"SpawnerMini")
set_origin(cage,(0,0,0)); set_origin(mini,(0,0,0.45))
for o in (cage,mini): apply_scale(o)
parent(mini,cage)
ground_snap((cage,mini),cage)
MZ=mini.location.z
new_action(mini,"mini_idle")
for f,d in [(1,0),(120,355)]: krz(mini,f,d)             # ゆっくり一回転
for f,z in [(1,MZ),(30,MZ+0.06),(60,MZ),(90,MZ+0.06),(120,MZ)]: kz(mini,f,z)  # 上下
push(mini,"idle")
export_glb("struct_spawner")

# =================================================================== 松明 torch
reset_all()
STICK=mat("TorchStick",(0.40,0.27,0.14),0.8); FLAME=mat("Flame",(1.0,0.55,0.12),0.3,emis=(1.0,0.45,0.1))
FLAME2=mat("Flame2",(1.0,0.82,0.30),0.3,emis=(1.0,0.8,0.3))
STK=[]; FL=[]
cyl(STK,"Stick",(0,0,0.27),0.035,0.54,STICK,verts=10)
cube(STK,"Wrap",(0,0,0.50),(0.05,0.05,0.05),mat("Wrap",(0.30,0.30,0.32),0.7))  # 先端の布巻き
cone(FL,"FlameOuter",(0,0,0.66),0.075,0.20,FLAME,verts=12)
cone(FL,"FlameInner",(0,0,0.70),0.040,0.13,FLAME2,verts=10)
stick=join(STK,"TorchStick"); flame=join(FL,"TorchFlame")
set_origin(stick,(0,0,0)); set_origin(flame,(0,0,0.56))   # 炎の根元を支点に
for o in (stick,flame): apply_scale(o)
parent(flame,stick)
ground_snap((stick,flame),stick)
# 炎の揺らぎ：scale脈動＋わずかな傾き
new_action(flame,"flame_idle")
for f,sc in [(1,1.0),(6,1.12),(12,0.92),(18,1.08),(24,1.0)]: ks(flame,f,sc)
for f,d in [(1,-4),(12,5),(24,-4)]: krx(flame,f,d)
push(flame,"idle")
export_glb("struct_torch")

# =================================================================== 祭壇 altar
reset_all()
ST=mat("AltarStone",(0.50,0.50,0.54),0.85); ST2=mat("AltarStone2",(0.40,0.40,0.44),0.85)
GEM=mat("Gem",(0.55,0.35,0.95),0.15,emis=(0.6,0.35,1.0)); GLOW=mat("Rune",(0.65,0.45,1.0),0.2,emis=(0.6,0.4,1.0))
PED=[]; GM=[]
# 段組みの石台
cube(PED,"Step",(0,0,0.12),(0.62,0.62,0.12),ST2)          # 下段（広い）
cube(PED,"Column",(0,0,0.45),(0.40,0.40,0.24),ST)          # 中段の柱
cube(PED,"Top",(0,0,0.74),(0.55,0.55,0.06),ST2)            # 天板
for (x,y) in [(-0.45,-0.45),(0.45,-0.45),(-0.45,0.45),(0.45,0.45)]:
    cube(PED,"RuneMark",(x*0.9,y*0.9,0.805),(0.06,0.06,0.005),GLOW)  # 天板の発光紋
# 浮遊する魔石（八面体風＝sphere縦長で代用＋上下尖り）
sphere(GM,"GemBody",(0,0,1.15),(0.10,0.10,0.13),GEM,segs=12,rings=8)
cone(GM,"GemTop",(0,0,1.31),0.10,0.10,GEM,verts=8)
cone(GM,"GemBot",(0,0,0.99),0.10,0.10,GEM,verts=8,rot=(math.radians(180),0,0))
ped=join(PED,"AltarBase"); gem=join(GM,"AltarGem")
set_origin(ped,(0,0,0)); set_origin(gem,(0,0,1.15))
for o in (ped,gem): apply_scale(o)
parent(gem,ped)
ground_snap((ped,gem),ped)
GZ=gem.location.z
new_action(gem,"gem_idle")
for f,z in [(1,GZ),(45,GZ+0.07),(90,GZ)]: kz(gem,f,z)        # 浮遊
for f,d in [(1,0),(120,360)]: krz(gem,f,d)                   # ゆっくり回転
push(gem,"idle")
export_glb("struct_altar")

print("[voxel] all dungeon structures done")
