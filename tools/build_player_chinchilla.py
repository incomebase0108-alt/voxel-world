# -*- coding: utf-8 -*-
# VOXEL WORLD - プレイヤー主人公：さくら（チンチラ）＝立ち/歩き姿勢
#   ★最初の可愛いさくら(pet_chinchilla)と“同一造形”。顔・毛皮・つぶら目・耳・比率・色は
#     build_pet_chinchilla の値を「そのまま」流用し、変えるのは姿勢だけ（座り→立ち）。
#   違い: 相棒=座って手を持つ / プレイヤー=移動するので立ち脚＋腕を下ろす＋尾を後ろへ。
#   出力: models/player_chinchilla.glb（既定=ベージュ/さくら）＋ player_chinchilla_<色>.glb 8色
#   規約: Y-up / 足元 y=0 / 正面 -Z / 1ブロック≒1m。武器手持ちは腕ボーン無のため非表示でOK。
#   実行: python tools/build_player_chinchilla.py
import os, math
import build_pet_chinchilla as ck
E = ck.ellipsoid

# 胴から上を“そのままの形”で持ち上げる量（立ち脚を入れる隙間）。比率・顔は不変。
LIFT = 0.20

def build_standing(C):
    ck.PARTS.clear()
    (FUR, BELLY, EAR_OUT, EAR_IN, NOSE, EYE, EYE_EMIS, PAW, TAIL, TAILTIP) = C
    SB, RB = 26, 18
    SM, RM = 20, 13
    L = LIFT
    # ===== ここから下は pet_chinchilla.build_parts と同一値（y に +L して平行移動するだけ）=====
    E(0.0, 0.255+L, 0.00, 0.262, 0.260, 0.250, FUR, seg=SB, ring=RB, fur=0.011)     # 体
    E(0.0, 0.205+L, 0.190, 0.150, 0.165, 0.085, BELLY, seg=SM, ring=RM, fur=0.008)  # 腹〜胸
    E(0.0, 0.575+L, 0.050, 0.205, 0.198, 0.196, FUR, seg=SB, ring=RB, fur=0.011)    # 頭
    for sx in (-1, 1):                                                              # 頬毛
        E(sx*0.160, 0.500+L, 0.105, 0.082, 0.082, 0.078, FUR, seg=SM, ring=RM, fur=0.013)
    E(0.0, 0.488+L, 0.205, 0.102, 0.082, 0.086, BELLY, seg=SM, ring=RM, fur=0.006)  # 口元・頬（白）
    E(0.0, 0.506+L, 0.292, 0.030, 0.024, 0.024, NOSE, seg=12, ring=9, fur=0.0)      # 鼻
    for sx in (-1, 1):                                                              # 目＋ハイライト（不変）
        E(sx*0.101, 0.595+L, 0.205, 0.038, 0.040, 0.034, EYE, seg=18, ring=13,
          rough=0.12, emis=EYE_EMIS, fur=0.0)
        E(sx*0.085, 0.618+L, 0.246, 0.018, 0.018, 0.013, (1.0,1.0,1.0), seg=9, ring=7,
          rough=0.05, emis=(0.9, 0.9, 0.9), fur=0.0, ao=False)
    for sx in (-1, 1):                                                              # 特大の丸耳＋内耳
        E(sx*0.178, 0.805+L, -0.005, 0.132, 0.182, 0.052, EAR_OUT,
          seg=18, ring=12, rotZ=sx*0.10, rotX=-0.05, rough=0.6, fur=0.004)
        E(sx*0.178, 0.805+L, 0.026, 0.084, 0.128, 0.030, EAR_IN,
          seg=16, ring=10, rotZ=sx*0.10, rotX=-0.05, rough=0.6, fur=0.0)
    for sx in (-1, 1):                                                              # ヒゲ（不変・+L）
        base = (sx*0.06, 0.478+L, 0.270)
        for (dx, dy, dz) in [(0.40, 0.06, 0.07), (0.42, -0.01, 0.05),
                             (0.39, -0.08, 0.07), (0.35, 0.12, 0.06)]:
            ck.whisker(base, (sx*dx, 0.478+L+dy, 0.270+dz), 0.005, ck.WHISK)
    # ===== ここまで“同一造形” / 以下が立ち姿勢への差し替え（脚・腕・尾）=====
    # 腕（体側に下ろす＝移動向き。毛色の上腕＋肉球の手）
    for sx in (-1, 1):
        E(sx*0.205, 0.45, 0.095, 0.055, 0.120, 0.066, FUR, seg=14, ring=10, fur=0.006, rotZ=sx*0.06)
        E(sx*0.210, 0.335, 0.120, 0.046, 0.052, 0.052, PAW, seg=12, ring=8, fur=0.003)
    # 立ち脚（後足を下に伸ばして接地。毛色の脚＋平らな足＋指）
    for sx in (-1, 1):
        E(sx*0.120, 0.205, 0.020, 0.082, 0.175, 0.092, FUR, seg=14, ring=9, fur=0.006)  # 脚（毛）
        E(sx*0.120, 0.040, 0.072, 0.092, 0.044, 0.140, PAW, seg=14, ring=9, fur=0.0)     # 足（平ら・前向き）
        for fz in (0.150, 0.180, 0.210):
            E(sx*0.120, 0.030, fz, 0.022, 0.018, 0.028, PAW, seg=8, ring=6, fur=0.0)     # 指
    # 尻尾（形・毛は同じ／バランス用に後ろへ下ろす）
    E(0.0, 0.300, -0.215, 0.100, 0.140, 0.115, TAIL, seg=SM, ring=RM, fur=0.018)
    E(0.0, 0.165, -0.300, 0.086, 0.114, 0.094, TAIL, seg=SM, ring=RM, fur=0.018)
    E(0.0, 0.055, -0.345, 0.066, 0.085, 0.072, TAILTIP, seg=SM, ring=RM, fur=0.016)
    ck.finalize()   # 毛皮ノイズ＋AO＋足元 y=0 接地（pet と同じ仕上げ）

if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    models = os.path.join(os.path.dirname(here), 'models')
    for key, col in ck.VARIANTS.items():
        build_standing(col)
        ck.build_glb(os.path.join(models, f'player_chinchilla_{key}.glb'))
    build_standing(ck.VARIANTS['beige'])   # 既定＝さくら（ベージュ）
    ck.build_glb(os.path.join(models, 'player_chinchilla.glb'))
    # プレビュー（正面/3-4/横＝歩き姿勢が分かる）
    build_standing(ck.VARIANTS['beige'])
    panels = [ck.render_panel(360, 480, 0.0, math.radians(4)),
              ck.render_panel(360, 480, math.radians(34), math.radians(8)),
              ck.render_panel(360, 480, math.radians(90), math.radians(6))]
    out, GW, GH = ck.compose(panels, 3, 360, 480)
    ck.write_png(os.path.join(here, 'preview_player_chinchilla.png'), out, GW, GH)
    print(f"wrote preview_player_chinchilla.png ({GW}x{GH})")
