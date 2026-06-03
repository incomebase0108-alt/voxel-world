# -*- coding: utf-8 -*-
# VOXEL WORLD - 海の魚（世界拡張③）
# Blender 5.1 / headless: blender --background --python tools/build_fish.py [-- --render]
#   規約: Y-up / 最下点z=0(=接地/着水基準) / 正面・進行方向 +Y(=glTF -Z) / 1ブロック≒1m / 2MB以下 / アニメ idle・swim。
#   方針: 魚は Body＋Tail(別ノード)の2部品階層。尾ヒレは関節(尾の付け根)を原点に Z回り(水平)に振る＝
#         armature不使用・他モブと同じNLA内包の型。idle=ゆらぎ／swim=尾を大きく振る。frame1中立rest厳守。
#   出力: models/mob_fish*.glb（複数色・種）。

import bpy, os, math, mathutils, sys
V=mathutils.Vector
scene=bpy.context.scene; scene.render.fps=24
repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."));models=os.path.join(repo,"models");os.makedirs(models,exist_ok=True)

def reset():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for blk in (bpy.data.meshes,bpy.data.materials,bpy.data.objects,bpy.data.actions):
        for it in list(blk):
            try: blk.remove(it)
            except Exception: pass
def mat(n,rgb,r=0.45,me=0.0,emis=None,es=2.0):
    m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*rgb,1.0);b.inputs["Roughness"].default_value=r;b.inputs["Metallic"].default_value=me
    if emis is not None:
        b.inputs["Emission Color"].default_value=(*emis,1.0); b.inputs["Emission Strength"].default_value=es
    return m

def build_fish(name, cfg):
    reset()
    L=cfg.get('len',0.52)            # 体長(Y)
    col=mat("Body",cfg['col'],0.4)
    belly=mat("Belly",cfg.get('belly',(0.92,0.92,0.95)),0.4)
    finc=mat("Fin",cfg.get('fin',cfg['col']),0.5)
    eye=mat("Eye",(0.05,0.05,0.07),0.2); pupil=mat("Pup",(0.95,0.95,0.98),0.3)
    stripem=mat("Stripe",cfg.get('stripe',(0.1,0.1,0.12)),0.45)

    BODY=[];TAIL=[]
    def SP(g,n,loc,sz,m,segs=20,rings=14):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=segs,ring_count=rings,location=loc)
        o=bpy.context.active_object;o.name=n;o.scale=sz;o.data.materials.append(m);g.append(o);return o
    def CB(g,n,loc,sz,m,rot=(0,0,0)):
        bpy.ops.mesh.primitive_cube_add(location=loc)
        o=bpy.context.active_object;o.name=n;o.scale=sz;o.rotation_euler=rot;o.data.materials.append(m);g.append(o);return o
    def CO(g,n,loc,r,d,m,verts=10,rot=(0,0,0)):
        bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r,radius2=0,depth=d,location=loc)
        o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);g.append(o);return o

    W=cfg.get('width',0.12); H=cfg.get('height',0.16); cz=cfg.get('cz',0.22)
    # --- 胴（前+Y=頭側を丸く、後-Y=尾側へテーパー）---
    SP(BODY,"Body",(0,0.02,cz),(W,L*0.5,H),col)
    SP(BODY,"Belly",(0,0.02,cz-H*0.45),(W*0.85,L*0.46,H*0.45),belly)
    SP(BODY,"Head",(0,L*0.40,cz),(W*0.92,L*0.22,H*0.92),col)        # 頭の張り
    if cfg.get('puffer'):                                            # フグ：丸い体＋トゲ
        for ax in range(10):
            a=math.radians(ax*36)
            CO(BODY,"Spk%d"%ax,(W*1.0*math.cos(a),0.02,cz+H*1.0*math.sin(a)),0.012,0.06,col,verts=6,
               rot=(0,0,0) if abs(math.sin(a))<0.5 else (math.radians(90),0,0))
    # 口
    CB(BODY,"Mouth",(0,L*0.50,cz-H*0.2),(W*0.4,0.02,0.018),stripem)
    # 目（両側）
    for sx in (1,-1):
        SP(BODY,"Eye%d"%sx,(sx*W*0.78,L*0.36,cz+H*0.2),(0.030,0.030,0.034),eye,segs=12,rings=10)
        SP(BODY,"Pup%d"%sx,(sx*W*0.92,L*0.37,cz+H*0.22),(0.014,0.012,0.016),pupil,segs=10,rings=8)
    # 背びれ（上）
    CO(BODY,"Dorsal",(0,0.0,cz+H*1.05),W*0.5,0.18,finc,verts=4,rot=(math.radians(90),0,0))
    # 胸びれ（両側・薄板）
    for sx in (1,-1):
        CB(BODY,"Pect%d"%sx,(sx*W*0.95,L*0.18,cz-H*0.2),(0.10,0.06,0.012),finc,rot=(0,math.radians(20*sx),math.radians(-12*sx)))
    # 縞（tropical）
    if cfg.get('stripes'):
        for sy in (0.16,0.0,-0.16):
            CB(BODY,"Stripe%g"%sy,(0,sy*L,cz),(W*1.02,0.03,H*1.02),stripem)

    # --- 尾ヒレ（別ノード・付け根 y=-L*0.46 を原点に水平振り）---
    ty=-L*0.46
    CO(TAIL,"TailFin",(0,ty-0.10,cz),H*0.9,0.22,finc,verts=4,rot=(math.radians(90),0,0))
    CB(TAIL,"TailRoot",(0,ty+0.02,cz),(W*0.5,0.06,H*0.5),col)

    # --- 結合・原点・軽量化・親子・接地 ---
    def join(group,nm):
        bpy.ops.object.select_all(action='DESELECT')
        for o in group:o.select_set(True)
        bpy.context.view_layer.objects.active=group[0];bpy.ops.object.join()
        o=bpy.context.active_object;o.name=nm;return o
    body=join(BODY,"Body"); tail=join(TAIL,"Tail")
    def set_origin(o,p):
        bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
        scene.cursor.location=p;bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    set_origin(body,(0,0,0)); set_origin(tail,(0,ty,cz))   # 尾は付け根がピボット
    for o in (body,tail):
        bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
        bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)  # 回転も焼く＝rest単位回転（尾ヒレ向きはメッシュに固定）
        sm=o.modifiers.new("S",'SUBSURF');sm.levels=1;sm.render_levels=1
        bpy.ops.object.shade_smooth();bpy.ops.object.modifier_apply(modifier=sm.name)
        d=o.modifiers.new("D",'DECIMATE');d.decimate_type='COLLAPSE';d.ratio=0.5
        bpy.ops.object.modifier_apply(modifier=d.name);bpy.ops.object.shade_smooth()
    # tail を body の子に
    bpy.ops.object.select_all(action='DESELECT');tail.select_set(True);body.select_set(True)
    bpy.context.view_layer.objects.active=body;bpy.ops.object.parent_set(type='OBJECT',keep_transform=True)
    bpy.context.view_layer.update()
    minz=min((o.matrix_world@V(c)).z for o in (body,tail) for c in o.bound_box)
    body.location.z -= minz

    # --- アニメ（idle/swim・frame1中立）---
    def new_action(o,n):
        if o.animation_data is None:o.animation_data_create()
        a=bpy.data.actions.new(n);a.use_fake_user=True;o.animation_data.action=a;return a
    def push(o,t):
        ad=o.animation_data;act=ad.action;tr=ad.nla_tracks.new();tr.name=t
        tr.strips.new(act.name,int(act.frame_range[0]),act);ad.action=None
    def krz(o,f,d):o.rotation_euler[2]=math.radians(d);o.keyframe_insert('rotation_euler',index=2,frame=f)
    def kz(o,f,z):o.location.z=z;o.keyframe_insert('location',index=2,frame=f)
    BZ=body.location.z
    # idle: 尾を小さくゆらす＋体の上下ボブ。frame1=0で循環
    new_action(tail,"tail_idle")
    for f,d in [(1,0),(20,7),(40,-7),(60,0)]: krz(tail,f,d)
    push(tail,"idle")
    new_action(body,"body_idle")
    for f,z in [(1,BZ),(30,BZ+0.02),(60,BZ)]: kz(body,f,z)
    push(body,"idle")
    # swim: 尾を大きく速く振る＋体を反対へわずかにヨー（くねり）。frame1=0で循環
    new_action(tail,"tail_swim")
    for f,d in [(1,0),(6,20),(12,0),(18,-20),(24,0)]: krz(tail,f,d)
    push(tail,"swim")
    new_action(body,"body_swim")
    for f,d in [(1,0),(6,-5),(12,0),(18,5),(24,0)]: krz(body,f,d)
    push(body,"swim")

    scene.frame_set(1)
    out=os.path.join(models,name+".glb")
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_yup=True,
        export_apply=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_optimize_animation_size=True)
    zs=[(o.matrix_world@V(v)).z for o in (body,tail) for v in o.bound_box]
    print("[voxel] %-18s -> %.3f MB  H%.2fm L%.2fm  clips: idle/swim"%(name, os.path.getsize(out)/1048576, max(zs), L))

FISH = {
 "mob_fish":          {"col":(0.45,0.58,0.70),"belly":(0.90,0.92,0.95),"fin":(0.38,0.50,0.62),"len":0.52},        # 一般の銀青魚
 "mob_fish_tropical": {"col":(0.95,0.72,0.12),"belly":(0.98,0.95,0.80),"fin":(0.12,0.45,0.70),"stripes":True,
    "stripe":(0.10,0.12,0.20),"len":0.44,"height":0.18,"width":0.10},                                            # 黄×藍縞の熱帯魚
 "mob_fish_koi":      {"col":(0.92,0.40,0.16),"belly":(0.98,0.96,0.94),"fin":(0.98,0.96,0.94),"len":0.60,"height":0.17},  # 紅白の鯉
 "mob_fish_puffer":   {"col":(0.86,0.78,0.42),"belly":(0.96,0.94,0.82),"fin":(0.70,0.62,0.34),"puffer":True,
    "len":0.40,"width":0.16,"height":0.18,"cz":0.20},                                                            # 丸いフグ
}
ONLY=os.environ.get("ONLY","")
n=0
for nm,cfg in FISH.items():
    if ONLY and ONLY not in nm: continue
    build_fish(nm,cfg); n+=1
print("[voxel] fish built: %d"%n)

# ---- プレビュー（--render 時のみ・swimの尾振りを2フレーム）----
try:
    if "--render" in sys.argv:
        try: scene.render.engine='BLENDER_EEVEE_NEXT'
        except Exception: scene.render.engine='BLENDER_EEVEE'
        scene.render.resolution_x=900; scene.render.resolution_y=520
        world=bpy.data.worlds.new("W"); scene.world=world; world.use_nodes=True
        world.node_tree.nodes["Background"].inputs[0].default_value=(0.10,0.32,0.46,1)   # 水中
        world.node_tree.nodes["Background"].inputs[1].default_value=1.1
        bpy.ops.object.light_add(type='SUN',location=(3,-5,8)); bpy.context.active_object.data.energy=4.0
        # 直近ビルドの個体(=最後のmob_fish_puffer等)が残っているのでシーン全体を上から俯瞰
        def shot(name,loc,rot,lens=50):
            bpy.ops.object.camera_add(location=loc,rotation=rot)
            cam=bpy.context.active_object; scene.camera=cam; cam.data.lens=lens
            scene.render.filepath=os.path.join(repo,"tools",name)
            bpy.ops.render.render(write_still=True); bpy.data.objects.remove(cam,do_unlink=True)
        scene.frame_set(6)
        shot("hero_fish_3q.png",(1.4,-1.4,1.0),(math.radians(64),0,math.radians(-45)))
        print("[voxel] fish preview rendered: tools/hero_fish_3q.png")
except Exception as e:
    print("[voxel] fish preview skipped:", e)
