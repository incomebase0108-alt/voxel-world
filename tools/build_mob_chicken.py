# -*- coding: utf-8 -*-
# VOXEL WORLD - 中立モブ：鶏（小型・二足）
# Blender 5.1 / headless: blender --background --python tools/build_mob_chicken.py
#   出力: models/mob_chicken.glb （Y-up / 足元原点 / 正面 -Z / 高さ約0.4m / 1ブロック≒1m）
#   アニメ: idle / walk（中立・クリップ名統一）。食料ドロップ源。
# 方針: 白い体＋赤いとさか/肉垂・橙の嘴と脚・小さな翼と尾。subsurf1+decimateで軽量(<0.5MB)。
#   二足リグ: body配下に脚(股関節)・頭・翼・尾を階層化、NLAトラックで idle/walk。前=+Y。

import bpy, os, math, mathutils

bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for blk in (bpy.data.meshes,bpy.data.materials,bpy.data.objects,bpy.data.actions):
    for it in list(blk):
        try: blk.remove(it)
        except Exception: pass
scene=bpy.context.scene; scene.render.fps=24

def mat(n,rgb,r=0.6,me=0.0):
    m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*rgb,1.0);b.inputs["Roughness"].default_value=r;b.inputs["Metallic"].default_value=me;return m
M_BODY=mat("CkBody",(0.95,0.95,0.93)); M_RED=mat("CkRed",(0.85,0.16,0.14)); M_BEAK=mat("CkBeak",(0.95,0.66,0.18))
M_LEG=mat("CkLeg",(0.92,0.60,0.16)); M_EYE=mat("CkEye",(0.05,0.05,0.06))

def sphere(g,n,loc,s,m,segs=14,rings=10):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs,ring_count=rings,location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.data.materials.append(m);g.append(o);return o
def cyl(g,n,loc,r,d,m,verts=10,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d,location=loc)
    o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);g.append(o);return o
def cube(g,n,loc,s,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.active_object;o.name=n;o.scale=s;o.rotation_euler=rot;o.data.materials.append(m);g.append(o);return o
def set_origin(o,p):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    scene.cursor.location=p;bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

# 体（ぷっくり卵形）。中心 z=0.20。
BODY=[]
sphere(BODY,"Body",(0,0,0.20),(0.10,0.135,0.115),M_BODY,segs=18,rings=12)
# 翼（左右・付け根上）＋風切羽の段（後方へレイヤー）
WINGL=[]; WINGR=[]
sphere(WINGL,"WingL",(0.10,-0.01,0.21),(0.03,0.09,0.07),M_BODY)
sphere(WINGR,"WingR",(-0.10,-0.01,0.21),(0.03,0.09,0.07),M_BODY)
for k,dz in enumerate((0.0,-0.03)):
    cube(WINGL,"WingLf%d"%k,(0.105,-0.07,0.20+dz),(0.022,0.05,0.014),M_BODY,rot=(math.radians(-18),0,0))
    cube(WINGR,"WingRf%d"%k,(-0.105,-0.07,0.20+dz),(0.022,0.05,0.014),M_BODY,rot=(math.radians(-18),0,0))
# 尾（背面 -Y、上向きの羽を数枚レイヤーで扇に）
TAIL=[]
for k,(dz,ang,w) in enumerate([(0.0,-30,0.07),(0.035,-46,0.06),(0.07,-60,0.05)]):
    cube(TAIL,"Tail%d"%k,(0,-0.14,0.27+dz),(w,0.06,0.016),M_BODY,rot=(math.radians(ang),0,0))

# 頭（前=+Y、上）＋ とさか(複数山)/肉垂/嘴/目
HEAD=[]
sphere(HEAD,"Head",(0,0.07,0.34),(0.07,0.07,0.07),M_BODY,segs=14,rings=10)
for k,(yy,h) in enumerate([(0.10,0.022),(0.06,0.030),(0.02,0.024)]):  # とさか3山
    cube(HEAD,"Comb%d"%k,(0,yy,0.40),(0.015,0.016,h),M_RED)
sphere(HEAD,"Wattle",(0,0.12,0.29),(0.015,0.02,0.032),M_RED)     # 肉垂
cube(HEAD,"Beak",(0,0.14,0.33),(0.018,0.04,0.018),M_BEAK)         # 嘴
sphere(HEAD,"EyeL",(0.05,0.10,0.36),(0.012,0.01,0.014),M_EYE,segs=8,rings=6)
sphere(HEAD,"EyeR",(-0.05,0.10,0.36),(0.012,0.01,0.014),M_EYE,segs=8,rings=6)

# 脚 ×2（股関節 z=0.12、下端0）。橙の細い脚＋足。
def make_leg(n,x):
    leg=cyl([],"_l",(x,0,0.06),0.018,0.12,M_LEG); leg.name=n
    foot=cube([],"_f",(x,0.02,0.01),(0.025,0.045,0.012),M_LEG); foot.name=n+"_foot"
    bpy.ops.object.select_all(action='DESELECT'); leg.select_set(True); foot.select_set(True)
    bpy.context.view_layer.objects.active=leg; bpy.ops.object.join()
    set_origin(leg,(x,0,0.12)); return leg
legL=make_leg("LegL",0.045); legR=make_leg("LegR",-0.045)

# ジオメトリ確定
def finalize(o):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    s=o.modifiers.new("S",'SUBSURF');s.levels=1;s.render_levels=1
    bpy.ops.object.shade_smooth();bpy.ops.object.modifier_apply(modifier=s.name)
    d=o.modifiers.new("D",'DECIMATE');d.decimate_type='COLLAPSE';d.ratio=0.5
    bpy.ops.object.modifier_apply(modifier=d.name);bpy.ops.object.shade_smooth()
def join(group,name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in group:o.select_set(True)
    bpy.context.view_layer.objects.active=group[0];bpy.ops.object.join()
    o=bpy.context.active_object;o.name=name;return o
body=join(BODY,"Body");head=join(HEAD,"Head");wingL=join(WINGL,"WingL");wingR=join(WINGR,"WingR");tail=join(TAIL,"Tail")
for o in (body,head,wingL,wingR,tail,legL,legR): finalize(o)
# 翼・尾の付け根を原点に（揺れ用）
set_origin(wingL,(0.10,0,0.27)); set_origin(wingR,(-0.10,0,0.27)); set_origin(tail,(0,-0.10,0.24))

def parent(c,p):
    bpy.ops.object.select_all(action='DESELECT');c.select_set(True);p.select_set(True)
    bpy.context.view_layer.objects.active=p;bpy.ops.object.parent_set(type='OBJECT',keep_transform=True)
for c in (head,wingL,wingR,tail,legL,legR): parent(c,body)

# アニメ
def new_action(o,n):
    if o.animation_data is None:o.animation_data_create()
    a=bpy.data.actions.new(n);a.use_fake_user=True;o.animation_data.action=a;return a
def push(o,t):
    ad=o.animation_data;act=ad.action;tr=ad.nla_tracks.new();tr.name=t
    tr.strips.new(act.name,int(act.frame_range[0]),act);ad.action=None
def kz(o,f,z):o.location.z=z;o.keyframe_insert('location',index=2,frame=f)
def krx(o,f,d):o.rotation_euler[0]=math.radians(d);o.keyframe_insert('rotation_euler',index=0,frame=f)
def kry(o,f,d):o.rotation_euler[1]=math.radians(d);o.keyframe_insert('rotation_euler',index=1,frame=f)
BZ=body.location.z

# idle: 頭をちょこちょこ（つつき）＋翼の微動
new_action(head,"head_idle")
for f,d in [(1,0),(12,14),(20,0),(48,0)]: krx(head,f,d)
push(head,"idle")
for w,sgn in [(wingL,1),(wingR,-1)]:
    new_action(w,w.name+"_idle")
    for f,d in [(1,0),(24,10),(48,0)]: kry(w,f,sgn*d)
    push(w,"idle")
new_action(body,"body_idle")
for f,z in [(1,BZ),(24,BZ+0.008),(48,BZ)]: kz(body,f,z)
push(body,"idle")

# walk: 二足交互＋体の上下＋頭の前後ボブ
new_action(legL,"LegL_walk")
for f,p in [(1,1),(8,-1),(16,1)]: krx(legL,f,p*22)
push(legL,"walk")
new_action(legR,"LegR_walk")
for f,p in [(1,-1),(8,1),(16,-1)]: krx(legR,f,p*22)
push(legR,"walk")
new_action(body,"body_walk")
for f,z in [(1,BZ),(4,BZ+0.012),(8,BZ),(12,BZ+0.012),(16,BZ)]: kz(body,f,z)
push(body,"walk")
new_action(head,"head_walk")
for f,d in [(1,-8),(8,8),(16,-8)]: krx(head,f,d)   # 頭の前後ボブ
push(head,"walk")

repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."));models=os.path.join(repo,"models");os.makedirs(models,exist_ok=True)
out=os.path.join(models,"mob_chicken.glb")
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_yup=True,
    export_apply=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_optimize_animation_size=True)
zs=[];ys=[];xs=[]
for o in (body,head,wingL,wingR,tail,legL,legR):
    for v in o.bound_box:
        w=o.matrix_world@mathutils.Vector(v);xs.append(w.x);ys.append(w.y);zs.append(w.z)
print("[voxel] export OK ->",out)
print("[voxel] bbox X:%.2f..%.2f Y:%.2f..%.2f Z:%.2f..%.2f"%(min(xs),max(xs),min(ys),max(ys),min(zs),max(zs)))
print("[voxel] clips: idle / walk")
