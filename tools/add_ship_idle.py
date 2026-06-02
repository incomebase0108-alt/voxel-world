# -*- coding: utf-8 -*-
# VOXEL WORLD - 船に idle(波揺れ)クリップを内包追記
# blender --background --python tools/add_ship_idle.py
#   ship_sailboat / ship_rowboat を import → ルート(単一メッシュ)に idle のNLAを足して再export。
#   揺れ: 緩やかなロール(Y軸±3°)＋ピッチ(X軸±1.5°)＋z bob(±0.03)・約120フレーム周期。
#   1号機が「乗船時/停泊」で再生（中優先で要望受領済み）。難破船は静的なので対象外。
#   ※glTF import後はrotation_mode=QUATERNIONになりがち→mode判定でquat/euler両対応キー。

import bpy, os, math, mathutils
from mathutils import Quaternion, Euler
V=mathutils.Vector
repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
MODELS=os.path.join(repo,"models")
TARGETS=os.environ.get("SHIPS","ship_sailboat,ship_rowboat").split(",")
scene=bpy.context.scene; scene.render.fps=24

def wipe():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for blk in (bpy.data.meshes,bpy.data.materials,bpy.data.objects,bpy.data.actions):
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
def base_quat(o):
    return o.rotation_quaternion.copy() if o.rotation_mode=='QUATERNION' else Euler(o.rotation_euler).to_quaternion()
def krot(o,f,bq,rx,ry):
    tgt=bq @ Quaternion((1,0,0),math.radians(rx)) @ Quaternion((0,1,0),math.radians(ry))
    if o.rotation_mode=='QUATERNION':
        o.rotation_quaternion=tgt; o.keyframe_insert('rotation_quaternion',frame=f)
    else:
        o.rotation_euler=tgt.to_euler(o.rotation_mode); o.keyframe_insert('rotation_euler',frame=f)

def process(name):
    glb=os.path.join(MODELS,name+".glb")
    if not os.path.exists(glb): print("[voxel] skip",name); return
    wipe(); bpy.ops.import_scene.gltf(filepath=glb)
    objs=[o for o in bpy.context.scene.objects if o.type=='MESH']
    roots=[o for o in objs if o.parent is None]
    if not roots: print("[voxel] no root",name); return
    root=roots[0]; bz=root.location.z; bq=base_quat(root)
    existing=sorted(set(t.name for o in objs if o.animation_data for t in o.animation_data.nla_tracks))
    new_action(root,"ship_idle")
    # 1周期120f：ロール(Y)とピッチ(X)を位相ずらしで波感、zは微bob
    for f,rx,ry in [(1,0,0),(30,1.5,3.0),(60,0,0),(90,-1.5,-3.0),(120,0,0)]: krot(root,f,bq,rx,ry)
    for f,z in [(1,bz),(40,bz+0.03),(80,bz-0.02),(120,bz)]: kz(root,f,z)
    push(root,"idle")
    for o in objs:
        if o.animation_data: o.animation_data.action=None
    if root.rotation_mode=='QUATERNION': root.rotation_quaternion=bq
    else: root.rotation_euler=bq.to_euler(root.rotation_mode)
    root.location.z=bz
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=glb,export_format='GLB',use_selection=True,export_yup=True,
        export_apply=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_optimize_animation_size=True)
    sz=os.path.getsize(glb)
    print("[voxel] %-16s 既存[%s] +idle -> %.3fMB"%(name, ",".join(existing), sz/1048576))

for n in TARGETS: process(n)
print("[voxel] ship idle 付与 完了")
