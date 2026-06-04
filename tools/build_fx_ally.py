# -*- coding: utf-8 -*-
# VOXEL WORLD - 仲間マーカー（fx_ally_*.glb）【試作・3案】
# Blender 5.1 / headless: blender --background --python tools/build_fx_ally.py [-- --render]
#   出力: models/fx_ally_star.glb / fx_ally_heart.glb / fx_ally_halo.glb
#   用途: 仲間になったNPCの「頭上」に浮かべ、誰が仲間か一目で分かる小アイコン。
#   規約: Y-up / 正面 glTF -Z（Blender +Y面）/ 1ブロック≒1m。発光=Emission。軽量・Draco不使用。
#   ★地面物と違い「頭上に浮かぶ」ため 原点=アイコン中心（z=0は接地ではない）。
#     1号機が 仲間NPCの頭頂+オフセット に配置する想定。
#   各アイコンは自己完結ループアニメ「loop」を内包（NLAトラック名 "loop" に統一＝単一クリップ）。
#     共通: ゆっくり横回転（全方位から見える）＋ふわっと上下。ハートは鼓動パルスを追加。
#   サイズ ≒ 0.6m（頭上で小さく主張しすぎない）。

import bpy, os, math, mathutils, bmesh, sys
V=mathutils.Vector
scene=bpy.context.scene; scene.render.fps=24
scene.frame_start=1; scene.frame_end=96

def wipe():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for blk in (bpy.data.meshes,bpy.data.materials,bpy.data.objects,bpy.data.actions):
        for it in list(blk):
            try: blk.remove(it)
            except Exception: pass

def mat(n,rgb,r=0.6,me=0.0,emis=None,es=4.0):
    m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*rgb,1.0);b.inputs["Roughness"].default_value=r;b.inputs["Metallic"].default_value=me
    if emis is not None:
        b.inputs["Emission Color"].default_value=(*emis,1.0); b.inputs["Emission Strength"].default_value=es
    return m

# --- 平面アウトライン(X-Z平面・y=0)を1枚のnゴン面にし、Solidifyで両面厚みを付ける ---
#     回転しても裏が消えない（両面）＝頭上で全方位から視認できる。
def flat_shape(rim, m, name, thick=0.05, bevel=0.012):
    me=bpy.data.meshes.new(name); bm=bmesh.new()
    vs=[bm.verts.new((x,0.0,z)) for (x,z) in rim]
    bm.faces.new(vs)
    bm.normal_update(); bm.to_mesh(me); bm.free()
    o=bpy.data.objects.new(name,me); scene.collection.objects.link(o); o.data.materials.append(m)
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
    sol=o.modifiers.new("SOL",'SOLIDIFY'); sol.thickness=thick; sol.offset=0.0
    bpy.ops.object.modifier_apply(modifier=sol.name)
    if bevel>0:
        bv=o.modifiers.new("B",'BEVEL'); bv.width=bevel; bv.segments=1; bpy.ops.object.modifier_apply(modifier=bv.name)
    bpy.ops.object.shade_flat()
    o.location=(0,0,0)
    return o

def star_rim(outer,inner,points=5,phase=math.pi/2):
    rim=[]
    for i in range(points*2):
        r=outer if i%2==0 else inner
        a=phase+math.pi*i/points
        rim.append((r*math.cos(a), r*math.sin(a)))
    return rim

def heart_rim(scale=0.020, n=44):
    pts=[]
    for k in range(n):
        t=2*math.pi*k/n
        x=16*math.sin(t)**3
        z=13*math.cos(t)-5*math.cos(2*t)-2*math.cos(3*t)-math.cos(4*t)
        pts.append((x,z))
    cx=(min(p[0] for p in pts)+max(p[0] for p in pts))/2
    cz=(min(p[1] for p in pts)+max(p[1] for p in pts))/2
    return [((x-cx)*scale,(z-cz)*scale) for (x,z) in pts]

# --- アニメ（トラック名 "loop"・frame1=最終で継ぎ目なし） ---
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

def export(name, o):
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
    scene.frame_set(1)
    out=os.path.join(models,name+".glb")
    bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_yup=True,
        export_apply=False,export_animations=True,export_animation_mode='NLA_TRACKS',
        export_optimize_animation_size=True)
    bb=[(o.matrix_world@V(c)) for c in o.bound_box]
    w=max(p.x for p in bb)-min(p.x for p in bb); h=max(p.z for p in bb)-min(p.z for p in bb)
    print("[voxel] %-16s -> %.3f MB  %.2fx%.2fm (W×H)  anim:loop"%(name,os.path.getsize(out)/1048576,w,h))

# ============================================================
# ① fx_ally_star（金の五芒星・横回転＋ふわ上下）王道の「味方」印
# ============================================================
wipe()
GOLD=mat("AllyGold",(0.92,0.70,0.16),0.45,me=0.2,emis=(1.0,0.82,0.26),es=4.2)
star=flat_shape(star_rim(0.32,0.135), GOLD, "fx_ally_star", thick=0.06, bevel=0.014)
act(star,"star")
[krz(star,f,d) for f,d in [(1,0),(96,360)]]              # 1周/4s（ゆっくり）
[kz(star,f,z)  for f,z in [(1,0),(48,0.07),(96,0)]]      # ふわっと上下
push(star); export("fx_ally_star", star)

# ============================================================
# ② fx_ally_heart（桃色ハート・鼓動パルス＋横回転＋上下）親愛の印
# ============================================================
wipe()
PINK=mat("AllyHeart",(0.92,0.18,0.34),0.4,emis=(1.0,0.30,0.44),es=4.0)
heart=flat_shape(heart_rim(scale=0.021), PINK, "fx_ally_heart", thick=0.055, bevel=0.012)
act(heart,"heart")
[krz(heart,f,d) for f,d in [(1,0),(96,360)]]
[kz(heart,f,z)  for f,z in [(1,0),(48,0.06),(96,0)]]
for f,s in [(1,1.0),(12,1.14),(24,1.0),(36,1.10),(60,1.0),(96,1.0)]: ksc(heart,f,s)  # ドクン・ドクン
push(heart); export("fx_ally_heart", heart)

# ============================================================
# ③ fx_ally_halo（光の輪・水平リング＝天使の輪・自転＋ふわ上下）
# ============================================================
wipe()
HALO=mat("AllyHalo",(1.0,0.92,0.6),0.35,emis=(1.0,0.90,0.55),es=5.0)
bpy.ops.mesh.primitive_torus_add(location=(0,0,0),major_radius=0.30,minor_radius=0.045,
    major_segments=32,minor_segments=8)
halo=bpy.context.active_object; halo.name="fx_ally_halo"; halo.data.materials.append(HALO)
bpy.ops.object.shade_smooth()
d=halo.modifiers.new("D",'DECIMATE'); d.decimate_type='COLLAPSE'; d.ratio=0.7; bpy.ops.object.modifier_apply(modifier=d.name)
act(halo,"halo")
[krz(halo,f,d) for f,d in [(1,0),(96,360)]]              # 水平に回る輪
[kz(halo,f,z)  for f,z in [(1,0),(48,0.05),(96,0)]]
push(halo); export("fx_ally_halo", halo)

print("[voxel] ally marker set done: fx_ally_star / fx_ally_heart / fx_ally_halo")

# ---- プレビュー（-- --render 指定時のみ）----
try:
    if "--render" in sys.argv:
        def load(name):
            before=set(scene.objects); bpy.ops.import_scene.gltf(filepath=os.path.join(models,name+".glb"))
            return [o for o in scene.objects if o not in before]
        def setup(bg):
            try: scene.render.engine='BLENDER_EEVEE_NEXT'
            except Exception: scene.render.engine='BLENDER_EEVEE'
            scene.render.resolution_x=512; scene.render.resolution_y=512
            scene.world=bpy.data.worlds.new("W"); scene.world.use_nodes=True
            scene.world.node_tree.nodes["Background"].inputs[0].default_value=(*bg,1)
            scene.world.node_tree.nodes["Background"].inputs[1].default_value=0.5
            bpy.ops.object.light_add(type='SUN',location=(3,-4,6)); bpy.context.active_object.data.energy=2.2
        def shot(name,loc,look=(0,0,0)):
            bpy.ops.object.camera_add(location=loc); cam=bpy.context.active_object
            e=bpy.data.objects.new("E",None); scene.collection.objects.link(e); e.location=look
            cam.constraints.new('TRACK_TO').target=e; scene.camera=cam
            scene.render.filepath=os.path.join(repo,"tools",name); bpy.ops.render.render(write_still=True); print("[voxel] ->",name)
        for nm,bg in [("fx_ally_star",(0.06,0.07,0.10)),("fx_ally_heart",(0.09,0.05,0.07)),("fx_ally_halo",(0.05,0.06,0.09))]:
            wipe(); setup(bg); load(nm); scene.frame_set(30)
            shot("preview_%s_3q.png"%nm,(1.1,-1.3,0.7))
        print("[voxel] ally previews rendered")
except Exception as e:
    print("[voxel] preview skipped:",e)
