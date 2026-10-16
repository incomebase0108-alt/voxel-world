# -*- coding: utf-8 -*-
# VOXEL WORLD - テーマの象徴：桜の木＋舞う花びら素材
#   ※Blender不要・build_pet_chinchilla のツールキット(ellipsoid/fur/AO/GLB)を流用。
#   出力:
#     models/sakura_tree.glb       … 桜の木（幹＋枝＋ふわふわの花雲）。足元 y=0・正面 -Z。
#     models/fx_petal_sakura.glb   … 舞う花びら1片（粒子インスタンス用・原点中心・軽量）。
#   プレビュー: tools/preview_sakura.png
#   実行: python tools/build_sakura.py
import os, math
import build_pet_chinchilla as ck
E = ck.ellipsoid

BARK  =(0.42,0.30,0.22); BARK2=(0.33,0.23,0.16)
BLOSS =(0.97,0.74,0.82); BLOSS2=(0.99,0.88,0.92); BLOSS3=(0.95,0.60,0.73)
PETAL =(0.99,0.78,0.86)

def build_tree():
    ck.PARTS.clear()
    # --- 幹（根元太く上細く・少し傾ぐ。密に重ねた楕円で“1本の柱”に＝ビーズ化回避）---
    nT=15
    for i in range(nT):
        t=i/(nT-1)
        y=t*2.55; x=0.13*t*t; z=0.035*t
        r=0.34*(1.0-t)+0.115*t                # 根元0.34→梢0.115へテーパ
        E(x,y,z,r,0.22,r,BARK,seg=14,ring=7)  # ry=0.22>間隔0.18で強く重ねる
    E(0.0,-0.05,0.0,0.48,0.17,0.48,BARK2,seg=18,ring=9)          # 根張り
    # --- 枝（上部から放射状に数本）---
    branches=[(0.55,2.55,0.30,0.9,-0.5),(-0.55,2.5,-0.25,-0.9,-0.4),
              (0.25,2.75,-0.55,0.3,-0.9),(-0.30,2.7,0.55,-0.3,0.9),(0.10,2.95,0.0,0.0,0.0)]
    for (x,y,z,rzx,rzz) in branches:
        E(x*0.5,(2.2+y)/2,z*0.5,0.07,0.34,0.07,BARK,seg=10,ring=6,
          rotZ=rzx*0.7, rotX=rzz*0.7)
    # --- 花雲（ふわふわのピンク塊を複数・fur変位で花びら感）---
    canopy=[(0.0,3.05,0.0,1.18,BLOSS),(0.92,2.78,0.42,0.74,BLOSS3),(-0.86,2.85,-0.32,0.78,BLOSS),
            (0.30,3.45,-0.28,0.82,BLOSS2),(-0.34,3.25,0.58,0.72,BLOSS),(0.62,3.15,-0.55,0.62,BLOSS3),
            (-0.62,3.1,0.30,0.64,BLOSS2),(0.0,3.6,0.18,0.66,BLOSS2),(0.18,2.95,0.72,0.58,BLOSS3)]
    for (x,y,z,r,col) in canopy:
        E(x,y,z,r,r*0.92,r,col,seg=18,ring=12,fur=0.015)
    ck.finalize()   # 花雲に fur ノイズ＋AO を焼き、足元を y=0 へ接地

def build_petal():
    ck.PARTS.clear()
    # 桜の花びら1片：先がへこむ小判型を2ローブで近似＋わずかに反らせる。原点中心(粒子用)。
    E(0.018,0.0,0.0, 0.030,0.010,0.052, PETAL, seg=10,ring=6)
    E(-0.018,0.0,0.0,0.030,0.010,0.052, PETAL, seg=10,ring=6)
    E(0.0,0.004,-0.046,0.016,0.008,0.020, PETAL, seg=8,ring=5)   # 付け根側を絞る
    # 粒子素材は接地不要＝finalize(ground)は使わず vcol だけ手当て
    for p in ck.PARTS:
        p['vcol']=[(1.0,1.0,1.0)]*len(p['verts'])

if __name__=='__main__':
    here=os.path.dirname(os.path.abspath(__file__)); models=os.path.join(os.path.dirname(here),'models')
    build_tree();  ck.build_glb(os.path.join(models,'sakura_tree.glb'))
    build_petal(); ck.build_glb(os.path.join(models,'fx_petal_sakura.glb'))
    # プレビュー（木の3面＋花びら拡大）
    build_tree()
    panels=[ck.render_panel(360,460,math.radians(20),math.radians(8)),
            ck.render_panel(360,460,math.radians(120),math.radians(8))]
    build_petal()
    panels.append(ck.render_panel(360,460,math.radians(30),math.radians(20)))
    out,GW,GH=ck.compose(panels,3,360,460); ck.write_png(os.path.join(here,'preview_sakura.png'),out,GW,GH)
    print('wrote preview_sakura.png',GW,GH)
