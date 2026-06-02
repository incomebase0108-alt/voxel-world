# -*- coding: utf-8 -*-
# VOXEL WORLD - 住人NPC量産（町に住む人々）
# blender --background --python tools/build_npc_townsfolk.py
#   出力: models/npc_blacksmith/merchant/farmer/guard/child/elder/woman/baker.glb
#   規約: Y-up / 足元z=0 / 正面 -Z / 1ブロック≒1m / 2MB以下 / アニメ idle・walk（クリップ名統一）。
#   方針: npc_villager と【完全同一の骨格】(Body/ArmL/ArmR/LegL/LegR・肩z=1.40・股z=0.84)を
#         パラメトリック流用し、職業=服/被り物/持ち物/体格 だけ変える＝1号機が1実装で全員歩かせる。

import bpy, os, math, mathutils
V=mathutils.Vector
scene=bpy.context.scene; scene.render.fps=24
repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."));models=os.path.join(repo,"models");os.makedirs(models,exist_ok=True)

def reset():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for blk in (bpy.data.meshes,bpy.data.materials,bpy.data.objects,bpy.data.actions):
        for it in list(blk):
            try: blk.remove(it)
            except Exception: pass
def mat(n,rgb,r=0.7,me=0.0):
    m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*rgb,1.0);b.inputs["Roughness"].default_value=r;b.inputs["Metallic"].default_value=me;return m

def build_npc(name, cfg):
    reset()
    s = cfg.get('scale',1.0)
    hb = cfg.get('head_boost',1.0)      # 子供=頭大きめ
    skin=mat("Skin",cfg['skin'],0.5); cloth=mat("Cloth",cfg['cloth']); cloth2=mat("Cloth2",cfg.get('cloth2',(0.30,0.28,0.30)))
    accent=mat("Accent",cfg.get('accent',cfg['cloth'])); hair=mat("Hair",cfg.get('hair',(0.22,0.15,0.08)))
    belt=mat("Belt",cfg.get('belt',(0.28,0.18,0.10))); shoe=mat("Shoe",cfg.get('shoe',(0.20,0.14,0.10)))
    eye=mat("Eye",(0.06,0.06,0.08)); mouth=mat("Mouth",(0.55,0.30,0.28))
    metal=mat("Metal",(0.74,0.75,0.78),0.35,0.85); leather=mat("Leather",(0.36,0.24,0.13),0.8)
    wood=mat("Wood",(0.42,0.29,0.16),0.75); gold=mat("Gold",(0.86,0.68,0.24),0.3,0.7); cloth3=mat("Cloth3",cfg.get('accent',(0.7,0.7,0.7)))

    BODY=[];ARML=[];ARMR=[];LEGL=[];LEGR=[]
    # 縮尺ラッパ（全座標/サイズを s 倍）
    def CB(g,n,loc,sz,m,rot=(0,0,0)):
        bpy.ops.mesh.primitive_cube_add(location=tuple(c*s for c in loc))
        o=bpy.context.active_object;o.name=n;o.scale=tuple(c*s for c in sz);o.rotation_euler=rot;o.data.materials.append(m);g.append(o);return o
    def SP(g,n,loc,sz,m,segs=18,rings=12):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=segs,ring_count=rings,location=tuple(c*s for c in loc))
        o=bpy.context.active_object;o.name=n;o.scale=tuple(c*s for c in sz);o.data.materials.append(m);g.append(o);return o
    def CY(g,n,loc,r,d,m,verts=14,rot=(0,0,0)):
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r*s,depth=d*s,location=tuple(c*s for c in loc))
        o=bpy.context.active_object;o.name=n;o.rotation_euler=rot;o.data.materials.append(m);g.append(o);return o

    # ---- 胴 ----
    CB(BODY,"Torso",(0,0,1.12),(0.27*cfg.get('build',1.0),0.17,0.32),cloth)
    CB(BODY,"Belt",(0,0,0.92),(0.29*cfg.get('build',1.0),0.18,0.05),belt)
    SP(BODY,"ShoulderL",(0.26,0,1.40),(0.10,0.11,0.10),cloth)
    SP(BODY,"ShoulderR",(-0.26,0,1.40),(0.10,0.11,0.10),cloth)
    if cfg.get('apron'):
        CB(BODY,"Apron",(0,-0.16,1.00),(0.20,0.03,0.28),mat("Ap",cfg['apron'],0.8))
    if cfg.get('armor'):   # 衛兵：胸甲＋肩当て
        CB(BODY,"Plate",(0,-0.16,1.14),(0.26,0.04,0.30),metal)
        SP(BODY,"PauldL",(0.27,0,1.42),(0.12,0.12,0.10),metal); SP(BODY,"PauldR",(-0.27,0,1.42),(0.12,0.12,0.10),metal)
    if cfg.get('back'):    # 商人：背負い荷
        CB(BODY,"Pack",(0,0.20,1.12),(0.20,0.10,0.22),leather)
        CB(BODY,"PackTie",(0,0.0,1.30),(0.04,0.20,0.03),leather)
    if cfg.get('skirt'):   # 女性：スカート
        CB(BODY,"Skirt",(0,0,0.78),(0.26,0.20,0.16),mat("Skirt",cfg['skirt']))
    # ---- 首・頭・顔 ----
    CY(BODY,"Neck",(0,0,1.52),0.07,0.10,skin)
    SP(BODY,"Head",(0,0,1.66),(0.13*hb,0.14*hb,0.15*hb),skin,segs=24,rings=18)
    FY=0.13*hb
    SP(BODY,"EyeL",(0.05,FY,1.68),(0.022,0.018,0.024),eye,segs=12,rings=10)
    SP(BODY,"EyeR",(-0.05,FY,1.68),(0.022,0.018,0.024),eye,segs=12,rings=10)
    SP(BODY,"Nose",(0,FY+0.02,1.64),(0.02,0.03,0.025),skin,segs=12,rings=10)
    CB(BODY,"Mouth",(0,FY,1.585),(0.04,0.012,0.012),mouth)
    if cfg.get('beard'):
        bm=mat("Beard",cfg['beard'])
        SP(BODY,"Beard",(0,FY-0.01,1.575),(0.10,0.06,0.07),bm,segs=14,rings=10)
    # 髪 or 被り物
    hat=cfg.get('hat')
    if hat!='bald' and not cfg.get('no_hair'):
        SP(BODY,"Hair",(0,-0.02,1.73),(0.145,0.15,0.12),hair,segs=20,rings=14)
        if cfg.get('long_hair'):
            CB(BODY,"HairBack",(0,-0.10,1.55),(0.12,0.05,0.20),hair)
        else:
            CB(BODY,"HairF",(0,FY-0.01,1.74),(0.13,0.03,0.04),hair)
    if hat=='straw':       # 農民：麦わら帽
        CY(BODY,"Brim",(0,0,1.80),0.26,0.03,mat("Straw",(0.82,0.68,0.34),0.85),verts=20)
        CY(BODY,"Dome",(0,0,1.86),0.13,0.10,mat("Straw2",(0.78,0.63,0.30),0.85),verts=16)
    elif hat=='helmet':    # 衛兵：兜
        SP(BODY,"Helm",(0,0,1.74),(0.15,0.155,0.16),metal,segs=18,rings=12)
        CB(BODY,"NoseGuard",(0,FY,1.66),(0.025,0.05,0.10),metal)
    elif hat=='cap':       # 商人：柔帽
        SP(BODY,"Cap",(0,-0.01,1.78),(0.15,0.15,0.10),mat("Cap",cfg.get('accent',(0.4,0.2,0.2))),segs=16,rings=10)
        CB(BODY,"CapBrim",(0,0.12,1.74),(0.13,0.06,0.02),mat("Cap2",cfg.get('accent',(0.4,0.2,0.2))))
    elif hat=='bandana':   # 鍛冶屋：手拭い
        CB(BODY,"Band",(0,0,1.76),(0.145,0.15,0.05),mat("Bnd",cfg.get('accent',(0.6,0.2,0.2))))
    elif hat=='bakerhat':  # パン屋：コック帽
        CY(BODY,"BHat",(0,0,1.84),0.12,0.14,mat("White",(0.95,0.95,0.95),0.8),verts=16)

    # ---- 腕（肩 z=1.40）----
    def arm(g,sgn):
        x=0.30*sgn
        CY(g,"Sleeve",(x,0,1.28),0.075,0.30,cloth)
        CY(g,"Fore",(x,0,0.98),0.06,0.28,skin)
        SP(g,"Hand",(x,0,0.80),(0.065,0.05,0.075),skin)
    arm(ARML,1); arm(ARMR,-1)
    # 右手の持ち物（ARMRに内包＝手に追従）
    prop=cfg.get('prop'); hx=-0.30
    if prop=='hammer':
        CY(ARMR,"HamShaft",(hx,0.06,0.95),0.022,0.34,wood,verts=8)
        CB(ARMR,"HamHead",(hx,0.06,1.14),(0.05,0.05,0.09),metal)
    elif prop=='hoe':
        CY(ARMR,"HoeShaft",(hx,0.06,1.05),0.022,0.85,wood,verts=8)
        CB(ARMR,"HoeBlade",(hx,0.14,1.46),(0.10,0.02,0.05),metal,rot=(math.radians(30),0,0))
    elif prop=='spear':
        CY(ARMR,"SpShaft",(hx,0.05,1.05),0.022,1.5,wood,verts=8)
        bpy.ops.mesh.primitive_cone_add(vertices=8,radius1=0.04*s,radius2=0,depth=0.16*s,location=(hx*s,0.05*s,1.86*s))
        o=bpy.context.active_object;o.name="SpTip";o.data.materials.append(metal);ARMR.append(o)
    elif prop=='cane':
        CY(ARMR,"Cane",(hx-0.02,0.10,0.55),0.02,0.95,wood,verts=8)
        SP(ARMR,"CaneTop",(hx-0.02,0.10,1.02),(0.04,0.04,0.04),wood)

    # ---- 脚（股 z=0.84）----
    def leg(g,sgn):
        x=0.10*sgn
        CY(g,"Thigh",(x,0,0.62),0.09,0.42,cloth2)
        CY(g,"Shin",(x,0,0.22),0.075,0.36,cloth2)
        CB(g,"Shoe",(x,0.05,0.04),(0.085,0.15,0.06),shoe)
    leg(LEGL,1); leg(LEGR,-1)

    # ---- 結合・原点・軽量化・親子・接地 ----
    def join(group,nm):
        bpy.ops.object.select_all(action='DESELECT')
        for o in group:o.select_set(True)
        bpy.context.view_layer.objects.active=group[0];bpy.ops.object.join()
        o=bpy.context.active_object;o.name=nm;return o
    body=join(BODY,"Body");armL=join(ARML,"ArmL");armR=join(ARMR,"ArmR");legL=join(LEGL,"LegL");legR=join(LEGR,"LegR")
    def set_origin(o,p):
        bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
        scene.cursor.location=tuple(c*s for c in p);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    set_origin(body,(0,0,0)); set_origin(armL,(0.28,0,1.40)); set_origin(armR,(-0.28,0,1.40))
    set_origin(legL,(0.10,0,0.84)); set_origin(legR,(-0.10,0,0.84))
    for o in (body,armL,armR,legL,legR):
        bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        sm=o.modifiers.new("S",'SUBSURF');sm.levels=1;sm.render_levels=1
        bpy.ops.object.shade_smooth();bpy.ops.object.modifier_apply(modifier=sm.name)
        d=o.modifiers.new("D",'DECIMATE');d.decimate_type='COLLAPSE';d.ratio=0.42
        bpy.ops.object.modifier_apply(modifier=d.name);bpy.ops.object.shade_smooth()
    def parent(c,p):
        bpy.ops.object.select_all(action='DESELECT');c.select_set(True);p.select_set(True)
        bpy.context.view_layer.objects.active=p;bpy.ops.object.parent_set(type='OBJECT',keep_transform=True)
    for limb in (armL,armR,legL,legR): parent(limb,body)
    bpy.context.view_layer.update()
    minz=min((o.matrix_world@V(c)).z for o in (body,armL,armR,legL,legR) for c in o.bound_box)
    body.location.z -= minz

    # ---- idle / walk（villagerと同一）----
    def new_action(o,n):
        if o.animation_data is None:o.animation_data_create()
        a=bpy.data.actions.new(n);a.use_fake_user=True;o.animation_data.action=a;return a
    def push(o,t):
        ad=o.animation_data;act=ad.action;tr=ad.nla_tracks.new();tr.name=t
        tr.strips.new(act.name,int(act.frame_range[0]),act);ad.action=None
    def kz(o,f,z):o.location.z=z;o.keyframe_insert('location',index=2,frame=f)
    def krx(o,f,d):o.rotation_euler[0]=math.radians(d);o.keyframe_insert('rotation_euler',index=0,frame=f)
    BZ=body.location.z
    # 【重要】全クリップの frame1 を中立(0 / BZ)に揃える。glTFのノード基準姿勢は
    #   export時フレーム(=1)のNLA評価結果になるため、frame1中立＝立ち姿restが正しく出る。
    new_action(body,"body_idle")
    for f,z in [(1,BZ),(30,BZ+0.012*s),(60,BZ)]: kz(body,f,z)
    push(body,"idle")
    for a,sgn in [(armL,1),(armR,-1)]:
        new_action(a,a.name+"_idle")
        for f,d in [(1,0),(30,5*sgn),(60,0)]: krx(a,f,d)
        push(a,"idle")
    LA=20.0; AA=14.0
    # walk: frame1=0 から一往復して0へ戻る（中立始点で循環）
    new_action(legL,"LegL_walk")
    for f,d in [(1,0),(8,LA),(16,0),(24,-LA),(32,0)]: krx(legL,f,d)
    push(legL,"walk")
    new_action(legR,"LegR_walk")
    for f,d in [(1,0),(8,-LA),(16,0),(24,LA),(32,0)]: krx(legR,f,d)
    push(legR,"walk")
    new_action(armL,"ArmL_walk")
    for f,d in [(1,0),(8,-AA),(16,0),(24,AA),(32,0)]: krx(armL,f,d)
    push(armL,"walk")
    new_action(armR,"ArmR_walk")
    for f,d in [(1,0),(8,AA),(16,0),(24,-AA),(32,0)]: krx(armR,f,d)
    push(armR,"walk")
    new_action(body,"body_walk")
    for f,z in [(1,BZ),(8,BZ+0.018*s),(16,BZ),(24,BZ+0.018*s),(32,BZ)]: kz(body,f,z)
    push(body,"walk")
    # ---- 生活AI用の追加クリップ（sit/work/talk・クリップ名統一・全てframe1中立）----
    # sit: 中立→脚を前へ＋胴を下げる（座り込み・以降保持）
    for lg in (legL,legR):
        new_action(lg,lg.name+"_sit")
        for f,d in [(1,0),(15,74),(40,75)]: krx(lg,f,d)
        push(lg,"sit")
    new_action(body,"body_sit")
    for f,z in [(1,BZ),(15,BZ-0.42*s),(40,BZ-0.42*s)]: kz(body,f,z)
    push(body,"sit")
    # work: 右腕の振り下ろし反復（鍛冶/耕作）＋胴の微上下。frame1=0で循環
    new_action(armR,"ArmR_work")
    for f,d in [(1,0),(8,-55),(16,0),(24,-55),(32,0)]: krx(armR,f,d)
    push(armR,"work")
    new_action(body,"body_work")
    for f,z in [(1,BZ),(8,BZ-0.012*s),(16,BZ),(24,BZ-0.012*s),(32,BZ)]: kz(body,f,z)
    push(body,"work")
    # talk: 両腕で身振り＋胴の軽い揺れ。frame1=0
    new_action(armR,"ArmR_talk")
    for f,d in [(1,0),(20,-24),(40,0)]: krx(armR,f,d)
    push(armR,"talk")
    new_action(armL,"ArmL_talk")
    for f,d in [(1,0),(25,20),(50,0)]: krx(armL,f,d)
    push(armL,"talk")
    new_action(body,"body_talk")
    for f,z in [(1,BZ),(30,BZ+0.008*s),(60,BZ)]: kz(body,f,z)
    push(body,"talk")

    scene.frame_set(1)   # rest=frame1（全クリップ中立）でノード基準姿勢を確定
    out=os.path.join(models,name+".glb")
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_yup=True,
        export_apply=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_optimize_animation_size=True)
    zs=[(o.matrix_world@V(v)).z for o in (body,armL,armR,legL,legR) for v in o.bound_box]
    sz=os.path.getsize(out)
    print("[voxel] %-16s -> %.3f MB  H%.2fm  clips: idle/walk"%(name, sz/1048576, max(zs)))

# ===== 住人定義（villager骨格・職業=見た目だけ）=====
NPCS = {
 "npc_blacksmith": {"skin":(0.80,0.58,0.45),"cloth":(0.30,0.30,0.32),"cloth2":(0.24,0.22,0.22),
    "apron":(0.40,0.26,0.14),"hat":"bandana","accent":(0.55,0.18,0.16),"build":1.12,"hair":(0.20,0.14,0.08),
    "beard":(0.20,0.14,0.08),"prop":"hammer","belt":(0.30,0.20,0.10)},
 "npc_merchant": {"skin":(0.84,0.64,0.50),"cloth":(0.24,0.20,0.45),"cloth2":(0.20,0.18,0.30),
    "accent":(0.55,0.42,0.16),"hat":"cap","back":True,"belt":(0.55,0.42,0.16),"hair":(0.25,0.18,0.10)},
 "npc_farmer": {"skin":(0.82,0.60,0.46),"cloth":(0.56,0.44,0.26),"cloth2":(0.34,0.28,0.18),
    "hat":"straw","prop":"hoe","accent":(0.62,0.55,0.42),"hair":(0.30,0.20,0.10)},
 "npc_guard": {"skin":(0.82,0.62,0.48),"cloth":(0.26,0.26,0.30),"cloth2":(0.22,0.22,0.26),
    "armor":True,"hat":"helmet","prop":"spear","no_hair":True,"build":1.08,"belt":(0.25,0.20,0.14)},
 "npc_child": {"skin":(0.88,0.70,0.56),"cloth":(0.40,0.58,0.30),"cloth2":(0.30,0.30,0.40),
    "scale":0.72,"head_boost":1.18,"hair":(0.35,0.22,0.10),"accent":(0.40,0.58,0.30)},
 "npc_elder": {"skin":(0.80,0.66,0.56),"cloth":(0.40,0.38,0.42),"cloth2":(0.32,0.30,0.34),
    "hair":(0.88,0.88,0.86),"beard":(0.88,0.88,0.86),"prop":"cane","build":0.95,"belt":(0.30,0.26,0.22)},
 "npc_woman": {"skin":(0.86,0.66,0.52),"cloth":(0.55,0.30,0.40),"cloth2":(0.40,0.24,0.30),
    "skirt":(0.50,0.26,0.36),"long_hair":True,"hair":(0.30,0.18,0.08),"apron":(0.80,0.78,0.72),
    "accent":(0.80,0.78,0.72),"belt":(0.45,0.30,0.20)},
 "npc_baker": {"skin":(0.85,0.64,0.50),"cloth":(0.85,0.84,0.80),"cloth2":(0.40,0.30,0.22),
    "apron":(0.92,0.90,0.86),"hat":"bakerhat","accent":(0.80,0.30,0.24),"hair":(0.25,0.16,0.08),"build":1.05},
}
for nm,cfg in NPCS.items(): build_npc(nm,cfg)
print("[voxel] all townsfolk done (%d)"%len(NPCS))
