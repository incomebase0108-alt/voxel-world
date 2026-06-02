# -*- coding: utf-8 -*-
# VOXEL WORLD - 既存モブGLBに die(死亡)・hit(被弾) クリップを追記
# Blender 5.1 / headless: blender --background --python tools/add_mob_deathhit.py
#   既存 models/mob_*.glb / npc_villager.glb を import → ルート(Body=親なしmesh)に
#   die/hit のNLAトラックを足して同名で再export。既存クリップ(idle/walk/attack/heavy)は維持。
#   方式: ルートを回す/沈めるだけ＝四肢はBody子なので追従。全モブ統一・低リスク。
#     die : 横向きに倒れて沈む（rotY 0→82°, z沈下, 後半保持）— 二足/四足とも自然に絶命
#     hit : 後ろへ素早く仰け反って戻る（rotX 0→-16°→0 ＋微小に沈む）— 被弾フリンチ
#   環境変数 MOBS でカンマ区切り対象指定可（既定=全モブ＋villager）。

import bpy, os, math, mathutils
from mathutils import Quaternion, Euler
V=mathutils.Vector
repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
MODELS=os.path.join(repo,"models")
DEFAULT="mob_cow,mob_sheep,mob_chicken,mob_pig,mob_horse,mob_slime,mob_zombie,mob_skeleton,mob_golem,npc_villager"
TARGETS=os.environ.get("MOBS",DEFAULT).split(",")
scene=bpy.context.scene; scene.render.fps=24

def wipe():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for blk in (bpy.data.meshes,bpy.data.materials,bpy.data.objects,bpy.data.actions,bpy.data.armatures):
        for it in list(blk):
            try: blk.remove(it)
            except Exception: pass

def new_action(o,n):
    if o.animation_data is None:o.animation_data_create()
    a=bpy.data.actions.new(n);a.use_fake_user=True;o.animation_data.action=a;return a
def push(o,t):
    ad=o.animation_data;act=ad.action;tr=ad.nla_tracks.new();tr.name=t
    tr.strips.new(act.name,int(act.frame_range[0]),act);ad.action=None

def kz(o,f,z):o.location.z=z;o.keyframe_insert('location',index=2,frame=f)
# 回転キー：ルートの rotation_mode（glTF importはQUATERNIONになりがち）を判定し両対応。
# base_q（rest基準）に axis 回り deg の回転を合成して絶対姿勢でキー。既存クリップを壊さない。
def krot(o,f,base_q,axis,deg):
    tgt=base_q @ Quaternion(axis, math.radians(deg))
    if o.rotation_mode=='QUATERNION':
        o.rotation_quaternion=tgt; o.keyframe_insert('rotation_quaternion',frame=f)
    else:
        o.rotation_euler=tgt.to_euler(o.rotation_mode); o.keyframe_insert('rotation_euler',frame=f)
def base_quat(o):
    return o.rotation_quaternion.copy() if o.rotation_mode=='QUATERNION' else Euler(o.rotation_euler).to_quaternion()

def process(name):
    glb=os.path.join(MODELS,name+".glb")
    if not os.path.exists(glb):
        print("[voxel] skip(not found):",name); return
    wipe()
    bpy.ops.import_scene.gltf(filepath=glb)
    objs=[o for o in bpy.context.scene.objects if o.type=='MESH']
    roots=[o for o in objs if o.parent is None]
    if len(roots)!=1:
        print("[voxel] !! %s: root数=%d (期待1) -> %s"%(name,len(roots),[r.name for r in roots]))
        if not roots: return
    root=roots[0]
    # 既存クリップ名（NLAトラック）を確認
    existing=[]
    for o in objs:
        if o.animation_data:
            existing+= [t.name for t in o.animation_data.nla_tracks]
    existing=sorted(set(existing))
    # ルートのrest（基準）を退避：importでrotation/locが入っている場合に備える
    base_z=root.location.z; bq=base_quat(root)
    AY=(0,1,0); AX=(1,0,0)
    # die ：横向きに倒れて沈む（Y軸ロール＝二足/四足とも自然に絶命）
    new_action(root,"root_die")
    for f,d in [(1,0),(14,55),(24,82),(40,82)]: krot(root,f,bq,AY,d)
    for f,z in [(1,base_z),(24,base_z-0.12),(40,base_z-0.12)]: kz(root,f,z)
    push(root,"die")
    # hit ：後方へ素早く仰け反って戻る（X軸ピッチ）
    new_action(root,"root_hit")
    for f,d in [(1,0),(4,-16),(10,0)]: krot(root,f,bq,AX,d)
    for f,z in [(1,base_z),(4,base_z-0.04),(10,base_z)]: kz(root,f,z)
    push(root,"hit")
    # 念のためactiveアクションを外す＆restへ戻す（rest姿勢でexportされるように）
    for o in objs:
        if o.animation_data: o.animation_data.action=None
    if root.rotation_mode=='QUATERNION': root.rotation_quaternion=bq
    else: root.rotation_euler=bq.to_euler(root.rotation_mode)
    root.location.z=base_z
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=glb,export_format='GLB',use_selection=True,export_yup=True,
        export_apply=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_optimize_animation_size=True)
    sz=os.path.getsize(glb)
    print("[voxel] %-16s 既存[%s] +die/hit -> %.3fMB"%(name, ",".join(existing), sz/1048576))

for n in TARGETS: process(n)
print("[voxel] die/hit 付与 完了")
