# -*- coding: utf-8 -*-
# VOXEL WORLD - インベントリ/ホットバー用 2Dアイコン生成（3号機UI向け）
# Blender 5.1 / headless: blender --background --python tools/gen_icons.py
#   出力: tools/icons/icon_<name>.png
#   既定仕様（3号機回答が来たらここを変えて一括再出力）:
#     128×128 / 透過PNG(背景なし) / 斜め45°(方位45°·仰角30°) / 各モデルを正規化して余白約10%
#   対象: 消費アイテム4＋装備6（glb実体あり）。ブロックは色立方体を別生成（BLOCKS）。
#   ※オルソ投影でモデルごとに枠いっぱい（サイズ正規化）＝UIグリッドで粒が揃う。

import bpy, os, math, mathutils, json
V=mathutils.Vector
MANIFEST=[]   # {name, file, type}
repo=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
MODELS=os.path.join(repo,"models"); ICONS=os.path.join(repo,"tools","icons"); os.makedirs(ICONS,exist_ok=True)
PX=int(os.environ.get("ICON_PX","128")); AZ=math.radians(float(os.environ.get("ICON_AZ","45")))
EL=math.radians(float(os.environ.get("ICON_EL","30"))); MARGIN=float(os.environ.get("ICON_MARGIN","0.10"))

# レンダ共通設定
scene=bpy.context.scene
try: scene.render.engine='BLENDER_EEVEE_NEXT'
except Exception: scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=PX; scene.render.resolution_y=PX
scene.render.film_transparent=True                      # 透過背景
scene.render.image_settings.file_format='PNG'; scene.render.image_settings.color_mode='RGBA'
scene.world=scene.world or bpy.data.worlds.new("W"); scene.world.use_nodes=True
scene.world.node_tree.nodes["Background"].inputs[0].default_value=(0.5,0.5,0.5,1)  # 透過なので寄与なし

def clear():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for blk in (bpy.data.meshes,bpy.data.objects,bpy.data.actions):
        for it in list(blk):
            try: blk.remove(it)
            except Exception: pass

def add_lights():
    bpy.ops.object.light_add(type='SUN', location=(4,-6,8)); bpy.context.active_object.data.energy=4.5
    bpy.ops.object.light_add(type='SUN', location=(-5,5,4)); bpy.context.active_object.data.energy=2.0

def bounds(objs):
    pts=[(o.matrix_world@V(c)) for o in objs if o.type=='MESH' for c in o.bound_box]
    mn=V((min(p.x for p in pts),min(p.y for p in pts),min(p.z for p in pts)))
    mx=V((max(p.x for p in pts),max(p.y for p in pts),max(p.z for p in pts)))
    return mn,mx

def render_icon(objs, out):
    mn,mx=bounds(objs); ctr=(mn+mx)*0.5; diag=(mx-mn).length
    # 斜め45°カメラ（オルソ）。視線方向を方位/仰角から
    dirv=V((math.cos(EL)*math.cos(AZ), -math.cos(EL)*math.sin(AZ)*0+(-math.cos(EL)), math.sin(EL)))
    # 分かりやすく固定方向：右手前・上から
    cam_dir=V((1.0,-1.0,0.78)); cam_dir.normalize()
    cam_loc=ctr+cam_dir*(diag*2.0+1.0)
    bpy.ops.object.camera_add(location=cam_loc); cam=bpy.context.active_object
    cam.data.type='ORTHO'; cam.data.ortho_scale=diag*(1.0+MARGIN*2)   # 余白
    tgt=bpy.data.objects.new("T",None); scene.collection.objects.link(tgt); tgt.location=ctr
    c=cam.constraints.new('TRACK_TO'); c.target=tgt
    scene.camera=cam; scene.render.filepath=out
    bpy.ops.render.render(write_still=True)
    print("[voxel] icon ->", os.path.basename(out))

def icon_from_glb(name, typ):
    clear(); add_lights()
    before=set(scene.objects); bpy.ops.import_scene.gltf(filepath=os.path.join(MODELS,name+".glb"))
    new=[o for o in scene.objects if o not in before]
    for o in new:
        if o.animation_data: o.animation_data_clear()
    fn="icon_%s.png"%name
    render_icon(new, os.path.join(ICONS,fn))
    MANIFEST.append({"name":name,"file":fn,"type":typ})

# ---- glb実体のあるアイテム＋装備 ----
CONSUM=["item_meat","item_egg","item_coin","item_apple","item_coal","item_iron","item_gold","item_gem"]
EQUIP=["item_sword","item_pickaxe","item_axe","item_bow","item_shield","item_armor"]
for n in CONSUM: icon_from_glb(n,"item")
for n in EQUIP:  icon_from_glb(n,"equipment")

# ---- ブロックアイコン（色立方体・エンジンのブロック種に対応・色は仮で調整可）----
def mat(n,rgb,r=0.7,me=0.0,alpha=1.0):
    m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*rgb,alpha);b.inputs["Roughness"].default_value=r;b.inputs["Metallic"].default_value=me
    if alpha<1.0:
        b.inputs["Alpha"].default_value=alpha
        try: m.blend_method='BLEND'
        except Exception: pass
    return m
BLOCKS={
 "grass":(0.36,0.62,0.26),"dirt":(0.48,0.34,0.20),"stone":(0.55,0.55,0.57),
 "sand":(0.86,0.80,0.55),"wood":(0.45,0.31,0.17),"leaves":(0.28,0.52,0.22),
 "planks":(0.66,0.45,0.26),"stonebrick":(0.50,0.50,0.53),"glass":(0.62,0.78,0.86),
 "snow":(0.93,0.95,0.99),   # 3号機要望: ホットバー7番・雪（清色の白＋3/4陰影で立体）
}
for bn,rgb in BLOCKS.items():
    clear(); add_lights()
    alpha=0.45 if bn=="glass" else 1.0
    bpy.ops.mesh.primitive_cube_add(location=(0,0,0)); o=bpy.context.active_object
    o.scale=(0.5,0.5,0.5); o.data.materials.append(mat(bn,rgb,alpha=alpha))
    bv=o.modifiers.new("B",'BEVEL'); bv.width=0.02; bv.segments=1; bpy.ops.object.modifier_apply(modifier=bv.name)
    fn="icon_block_%s.png"%bn
    render_icon([o], os.path.join(ICONS,fn))
    MANIFEST.append({"name":"block_"+bn,"file":fn,"type":"block"})

# ---- マニフェスト（3号機UIが参照）----
spec={"px":PX,"format":"PNG RGBA(透過)","angle":"方位%g°/仰角%g°(斜め45°)"%(math.degrees(AZ),math.degrees(EL)),
      "margin":"%g%%"%(MARGIN*100),"normalized":"各モデルを枠いっぱいに正規化(オルソ投影)"}
with open(os.path.join(ICONS,"icons.json"),"w",encoding="utf-8") as f:
    json.dump({"spec":spec,"icons":MANIFEST},f,ensure_ascii=False,indent=2)
md=["# VOXEL WORLD アイコン一覧（3号機 インベントリ/ホットバーUI 用）\n",
    "`blender --background --python tools/gen_icons.py` で再生成。`tools/icons/icons.json` が機械可読版。\n",
    "**仕様**: %d×%d / 透過PNG(RGBA) / 斜め45°(方位%g°·仰角%g°) / 余白約%g%% / モデルごとに枠いっぱい正規化。"
      %(PX,PX,math.degrees(AZ),math.degrees(EL),MARGIN*100),
    "サイズ/形式/アングルの変更は環境変数 `ICON_PX/ICON_AZ/ICON_EL/ICON_MARGIN` で一括再出力可。\n",
    "| name | file | type |","|---|---|---|"]
for m in MANIFEST: md.append("| `%s` | `%s` | %s |"%(m["name"],m["file"],m["type"]))
with open(os.path.join(ICONS,"ICONS.md"),"w",encoding="utf-8") as f: f.write("\n".join(md)+"\n")
print("[voxel] all icons done (%d) ->"%len(MANIFEST), ICONS)
print("[voxel] -> tools/icons/icons.json, tools/icons/ICONS.md")
