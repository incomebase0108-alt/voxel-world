# -*- coding: utf-8 -*-
# VOXEL WORLD - ペット：チンチラ「さくら」（pet_chinchilla）
#   ユーザーの実物チンチラ写真に寄せた専用ペットモデル（リアル造形版）。
#   ※この環境に Blender が無いため、標準ライブラリだけで glTF(GLB) を直接生成する。
#   出力: models/pet_chinchilla_<color>.glb（8色）＋ models/pet_chinchilla.glb（さくら=ベージュ・互換）
#         tools/preview_pet_chinchilla.png（正面/3-4/背面）/ tools/preview_pet_chinchilla_colors.png（8色一覧）
#
#   規約: Y-up / 足元 y=0（接地・原点不変）/ 正面 -Z / 高さ約0.97m / 1ブロック≒1m
#
#   リアル化の方針（写真準拠）:
#     - ブロック調を完全に廃し、頂点を増やしたなめらかな楕円球＋スムーズシェード。
#     - まんまるの体・特大の丸耳（内耳ピンク）・つぶらな黒目・ピンク鼻・長いヒゲ。
#     - 短い前足／座って体を支える大きめの後足・ふさふさ尻尾・ぷっくり頬毛。
#     - 毛並み感: 毛皮パーツに3オクターブのバリューノイズで法線方向の微凹凸を与え、
#                 ふわっとした輪郭にする（簡易ファー）。
#     - ベースカラー＋AO: 頂点カラー(COLOR_0)に簡易アンビエントオクルージョンを焼き込み、
#                 下面や足元を落として立体感・接地感を出す（エンジン側の改修不要）。
#     - ボスの発光赤目/王冠は付けない（普段着の相棒）。
#
#   実行: python tools/build_pet_chinchilla.py
import struct, json, zlib, math, os

# ----------------------------------------------------------------------
# パーツ集積（各パーツ＝1プリミティブ＝1マテリアル）
#   fur: >0 でその振幅の毛皮ノイズ凹凸を付与 / ao: True で頂点カラーにAOを焼く
# ----------------------------------------------------------------------
PARTS = []

def add(verts, faces, color, rough=0.85, metal=0.0, emis=None, fur=0.0, ao=True):
    PARTS.append(dict(verts=verts, faces=faces, color=color, rough=rough, metal=metal,
                      emis=emis, fur=fur, ao=ao))

def uv_sphere(cx, cy, cz, rx, ry, rz, seg=16, ring=10):
    """中心(cx,cy,cz)・半径(rx,ry,rz)の楕円球。seg/ring を上げると滑らかになる。"""
    verts, faces = [], []
    for i in range(ring + 1):
        v = i / ring
        phi = v * math.pi
        y = math.cos(phi)
        r = math.sin(phi)
        for j in range(seg + 1):
            u = j / seg
            th = u * 2 * math.pi
            x = r * math.cos(th)
            z = r * math.sin(th)
            verts.append((cx + x * rx, cy + y * ry, cz + z * rz))
    for i in range(ring):
        for j in range(seg):
            a = i * (seg + 1) + j
            b = a + seg + 1
            faces.append((a, b, a + 1))
            faces.append((a + 1, b, b + 1))
    return verts, faces

def transform(verts, mat):
    out = []
    for (x, y, z) in verts:
        out.append((
            mat[0]*x + mat[1]*y + mat[2]*z + mat[3],
            mat[4]*x + mat[5]*y + mat[6]*z + mat[7],
            mat[8]*x + mat[9]*y + mat[10]*z + mat[11],
        ))
    return out

def rotx(a):
    c, s = math.cos(a), math.sin(a)
    return [1,0,0,0, 0,c,-s,0, 0,s,c,0]
def roty(a):
    c, s = math.cos(a), math.sin(a)
    return [c,0,s,0, 0,1,0,0, -s,0,c,0]
def rotz(a):
    c, s = math.cos(a), math.sin(a)
    return [c,-s,0,0, s,c,0,0, 0,0,1,0]
def matmul(A, B):
    a = [A[0:4], A[4:8], A[8:12], [0,0,0,1]]
    b = [B[0:4], B[4:8], B[8:12], [0,0,0,1]]
    out = [[0]*4 for _ in range(4)]
    for i in range(4):
        for j in range(4):
            out[i][j] = sum(a[i][k]*b[k][j] for k in range(4))
    return out[0] + out[1] + out[2]

def ellipsoid(cx, cy, cz, rx, ry, rz, color, seg=16, ring=10, rough=0.85, metal=0.0,
              emis=None, rotX=0.0, rotY=0.0, rotZ=0.0, fur=0.0, ao=True):
    v, f = uv_sphere(0, 0, 0, rx, ry, rz, seg, ring)
    m = [1,0,0,0, 0,1,0,0, 0,0,1,0]
    if rotZ: m = matmul(rotz(rotZ), m)
    if rotY: m = matmul(roty(rotY), m)
    if rotX: m = matmul(rotx(rotX), m)
    m = matmul([1,0,0,cx, 0,1,0,cy, 0,0,1,cz], m)
    add(transform(v, m), f, color, rough, metal, emis, fur, ao)

def whisker(p0, p1, r, color):
    """p0->p1 の細い四角チューブ（ひげ）。AO/毛皮ノイズは付けない。"""
    ax = [p1[i]-p0[i] for i in range(3)]
    L = math.sqrt(sum(c*c for c in ax)) or 1e-6
    ax = [c/L for c in ax]
    up = [0,1,0] if abs(ax[1]) < 0.9 else [1,0,0]
    n1 = [ax[1]*up[2]-ax[2]*up[1], ax[2]*up[0]-ax[0]*up[2], ax[0]*up[1]-ax[1]*up[0]]
    l1 = math.sqrt(sum(c*c for c in n1)) or 1e-6
    n1 = [c/l1 for c in n1]
    n2 = [ax[1]*n1[2]-ax[2]*n1[1], ax[2]*n1[0]-ax[0]*n1[2], ax[0]*n1[1]-ax[1]*n1[0]]
    verts = []
    for end in (p0, p1):
        for sgn in ((1,1),(-1,1),(-1,-1),(1,-1)):
            verts.append(tuple(end[i] + sgn[0]*r*n1[i] + sgn[1]*r*n2[i] for i in range(3)))
    faces = []
    for k in range(4):
        a = k; b = (k+1)%4; c = 4+b; d = 4+a
        faces.append((a,b,c)); faces.append((a,c,d))
    faces.append((0,1,2)); faces.append((0,2,3))
    faces.append((4,6,5)); faces.append((4,7,6))
    add(verts, faces, color, rough=0.5, fur=0.0, ao=False)

# ----------------------------------------------------------------------
# バリューノイズ（毛並み用）。決定的＝ビルド再現性あり（乱数を使わない）。
# ----------------------------------------------------------------------
def _hash3(i, j, k):
    n = (i * 374761393 + j * 668265263 + k * 1274126177) & 0xffffffff
    n = (n ^ (n >> 13)) * 1274126177 & 0xffffffff
    n = n ^ (n >> 16)
    return (n & 0x7fffffff) / 0x7fffffff

def _vnoise(x, y, z):
    xi, yi, zi = math.floor(x), math.floor(y), math.floor(z)
    xf, yf, zf = x - xi, y - yi, z - zi
    def fade(t): return t * t * (3 - 2 * t)
    u, v, w = fade(xf), fade(yf), fade(zf)
    def L(a, b, t): return a + (b - a) * t
    c000 = _hash3(xi,   yi,   zi);   c100 = _hash3(xi+1, yi,   zi)
    c010 = _hash3(xi,   yi+1, zi);   c110 = _hash3(xi+1, yi+1, zi)
    c001 = _hash3(xi,   yi,   zi+1); c101 = _hash3(xi+1, yi,   zi+1)
    c011 = _hash3(xi,   yi+1, zi+1); c111 = _hash3(xi+1, yi+1, zi+1)
    x00 = L(c000, c100, u); x10 = L(c010, c110, u)
    x01 = L(c001, c101, u); x11 = L(c011, c111, u)
    y0 = L(x00, x10, v); y1 = L(x01, x11, v)
    return L(y0, y1, w)

def _fbm(x, y, z):
    f, a, fr = 0.0, 0.5, 22.0
    for _ in range(3):
        f += a * _vnoise(x * fr, y * fr, z * fr)
        fr *= 2.05; a *= 0.5
    return f  # おおよそ 0..0.875・平均 ~0.44

# ----------------------------------------------------------------------
# 色プリセット（チンチラの代表的なカラー）。EYE(idx5)/EYE_EMIS(idx6) が目色を決める。
#   ・黒目（つぶら＋白キャッチライト）＝ EYE≈(0.05,0.05,0.07), EYE_EMIS=None
#       → 標準グレー / ホワイト / エボニー / バイオレット / サファイア
#   ・ルビー赤目                     ＝ EYE=赤系, EYE_EMIS=赤系
#       → ベージュ / ブラウン / ピンクホワイト
#   ※実物チンチラの遺伝に準拠。baby は build_parts_baby 側で黒目に上書き（ここは無関係）。
# ----------------------------------------------------------------------
VARIANTS = {
    # key: (FUR, BELLY, EAR_OUT, EAR_IN, NOSE, EYE, EYE_EMIS, PAW, TAIL, TAILTIP)
    'beige':    ((0.66,0.61,0.585),(0.93,0.91,0.87),(0.92,0.72,0.72),(0.85,0.58,0.60),(0.95,0.66,0.68),(0.66,0.07,0.10),(0.50,0.04,0.06),(0.88,0.85,0.80),(0.62,0.57,0.555),(0.92,0.90,0.87)),
    'grey':     ((0.55,0.56,0.60),(0.93,0.93,0.94),(0.74,0.62,0.66),(0.62,0.50,0.54),(0.40,0.40,0.44),(0.05,0.05,0.06),None,            (0.90,0.91,0.93),(0.45,0.46,0.50),(0.93,0.93,0.95)),
    'white':    ((0.94,0.93,0.92),(0.98,0.98,0.97),(0.96,0.80,0.80),(0.88,0.66,0.68),(0.96,0.70,0.72),(0.06,0.05,0.06),None,            (0.97,0.96,0.95),(0.90,0.89,0.88),(0.99,0.99,0.98)),
    'ebony':    ((0.20,0.20,0.23),(0.16,0.16,0.19),(0.34,0.22,0.24),(0.24,0.15,0.17),(0.30,0.22,0.24),(0.04,0.03,0.05),None,            (0.30,0.30,0.34),(0.16,0.16,0.19),(0.34,0.34,0.38)),
    'violet':   ((0.60,0.56,0.64),(0.94,0.93,0.95),(0.90,0.74,0.78),(0.80,0.60,0.66),(0.90,0.66,0.72),(0.05,0.05,0.07),None,            (0.90,0.90,0.94),(0.50,0.47,0.55),(0.94,0.93,0.96)),
    'sapphire': ((0.50,0.55,0.64),(0.93,0.94,0.96),(0.78,0.68,0.74),(0.64,0.54,0.62),(0.70,0.66,0.72),(0.05,0.05,0.07),None,            (0.90,0.92,0.95),(0.42,0.47,0.56),(0.93,0.94,0.97)),
    'brown':    ((0.48,0.38,0.30),(0.90,0.84,0.74),(0.86,0.64,0.62),(0.74,0.50,0.50),(0.86,0.58,0.58),(0.55,0.10,0.10),(0.36,0.05,0.05),(0.84,0.78,0.70),(0.40,0.32,0.26),(0.90,0.84,0.74)),
    'pink':     ((0.95,0.88,0.87),(0.99,0.97,0.96),(0.97,0.78,0.80),(0.90,0.66,0.70),(0.96,0.70,0.74),(0.70,0.10,0.16),(0.50,0.06,0.10),(0.98,0.95,0.94),(0.90,0.84,0.84),(0.99,0.97,0.97)),
}
VARIANT_LABEL = {'beige':'ベージュ','grey':'スタンダードグレー','white':'ホワイト','ebony':'エボニー',
                 'violet':'バイオレット','sapphire':'サファイア','brown':'ブラウン','pink':'ピンクホワイト'}
WHISK = (0.97, 0.96, 0.95)

# ----------------------------------------------------------------------
# チンチラ造形（座り姿勢・造形は正面 +Z で組み、最後に -Z へ180°回す）
#   ※座標: +Y 上 / 後で min(y)=0 へ平行移動して接地
# ----------------------------------------------------------------------
def build_parts(C):
    PARTS.clear()
    (FUR, BELLY, EAR_OUT, EAR_IN, NOSE, EYE, EYE_EMIS, PAW, TAIL, TAILTIP) = C
    SB, RB = 26, 18   # 体・頭：高解像度
    SM, RM = 20, 13   # 中サイズ
    # 体（まんまる・ふわふわ）
    ellipsoid(0.0, 0.255, 0.00, 0.262, 0.260, 0.250, FUR, seg=SB, ring=RB, fur=0.011)
    # 腹〜胸（前面のクリーム）
    ellipsoid(0.0, 0.205, 0.190, 0.150, 0.165, 0.085, BELLY, seg=SM, ring=RM, fur=0.008)
    # 頭（胴の上のもう一つの丸＝「丸二つ」のシルエット）
    ellipsoid(0.0, 0.575, 0.050, 0.205, 0.198, 0.196, FUR, seg=SB, ring=RB, fur=0.011)
    # 頬毛（ぷっくり・左右）
    for sx in (-1, 1):
        ellipsoid(sx*0.160, 0.500, 0.105, 0.082, 0.082, 0.078, FUR, seg=SM, ring=RM, fur=0.013)
    # 口元・頬（白）
    ellipsoid(0.0, 0.488, 0.205, 0.102, 0.082, 0.086, BELLY, seg=SM, ring=RM, fur=0.006)
    # 鼻（ピンク・小さく）
    ellipsoid(0.0, 0.506, 0.292, 0.030, 0.024, 0.024, NOSE, seg=12, ring=9, fur=0.0)
    # 目（左右・つぶら・ツヤ）＋ハイライト
    for sx in (-1, 1):
        ellipsoid(sx*0.101, 0.595, 0.205, 0.045, 0.048, 0.040, EYE, seg=18, ring=13,
                  rough=0.12, emis=EYE_EMIS, fur=0.0)
        ellipsoid(sx*0.085, 0.618, 0.246, 0.018, 0.018, 0.013, (1.0,1.0,1.0), seg=9, ring=7,
                  rough=0.05, emis=(0.9, 0.9, 0.9), fur=0.0, ao=False)
    # 耳（特大の丸耳：地肌のピンク）＋内耳の陰
    for sx in (-1, 1):
        ellipsoid(sx*0.178, 0.805, -0.005, 0.132, 0.182, 0.052, EAR_OUT,
                  seg=18, ring=12, rotZ=sx*0.10, rotX=-0.05, rough=0.6, fur=0.004)
        ellipsoid(sx*0.178, 0.805, 0.026, 0.084, 0.128, 0.030, EAR_IN,
                  seg=16, ring=10, rotZ=sx*0.10, rotX=-0.05, rough=0.6, fur=0.0)
    # 前足（持つポーズ：腕を前に曲げ、両手を顎〜胸の上で中央に揃える＝何か持つ高さ）
    for sx in (-1, 1):
        # 前腕（毛色・肘を前に出し、手先を内側＝中央へ向ける）
        ellipsoid(sx*0.090, 0.315, 0.212, 0.050, 0.106, 0.057, FUR,
                  seg=14, ring=10, rotZ=sx*0.42, rotX=0.34, fur=0.007)
        # 手のひら（口より少し下・中央寄りで軽く合わせる。顔との間に隙間を残す）
        ellipsoid(sx*0.045, 0.397, 0.262, 0.044, 0.040, 0.048, PAW, seg=14, ring=9, fur=0.003)
        # 指4本（上前方へ向け、正面から見える）
        for fx in (0.018, 0.040, 0.062, 0.083):
            ellipsoid(sx*fx, 0.431, 0.278, 0.013, 0.024, 0.015, PAW,
                      seg=8, ring=6, rotX=0.5, fur=0.0)
    # 後足（座って体を支える・前へ投げ出す・大きめ）＋指
    for sx in (-1, 1):
        ellipsoid(sx*0.140, 0.034, 0.075, 0.074, 0.034, 0.135, PAW, seg=14, ring=9, fur=0.005)
        for fz in (0.150, 0.178, 0.206):
            ellipsoid(sx*0.140, 0.026, fz, 0.020, 0.018, 0.026, PAW, seg=8, ring=6, fur=0.0)
    # 尻尾（ふさふさ・後ろへ跳ね上げ・先はクリーム＝後ろ姿の差し色）
    ellipsoid(0.0, 0.185, -0.255, 0.100, 0.140, 0.120, TAIL, seg=SM, ring=RM, fur=0.018)
    ellipsoid(0.0, 0.360, -0.305, 0.086, 0.114, 0.094, TAIL, seg=SM, ring=RM, fur=0.018)
    ellipsoid(0.0, 0.500, -0.325, 0.066, 0.085, 0.072, TAILTIP, seg=SM, ring=RM, fur=0.016)
    # ひげ（左右に長め・数本）
    for sx in (-1, 1):
        base = (sx*0.06, 0.478, 0.275)
        for (dx, dy, dz) in [(0.40, 0.06, 0.07), (0.42, -0.01, 0.05),
                             (0.39, -0.08, 0.07), (0.35, 0.12, 0.06)]:
            whisker(base, (sx*dx, 0.478+dy, 0.275+dz), 0.005, WHISK)
    # --- 毛皮ノイズ＋AO焼き込み＋接地 ---
    finalize()

def build_parts_baby(C):
    """子チンチラ（赤ちゃん体型）。大人の比率を変えた上で全体0.8倍を焼き込む。
       ・頭：体 を頭寄りに（まんまる頭）・目を大きく丸く下＆前へ・うるうるキャッチライト
       ・マズル短く丸く鼻パッド小・ヒゲ短く控えめ・手足ずんぐり短く・体ぷっくり
       ・目は黒目固定（violet babyは黒が正）"""
    PARTS.clear()
    (FUR, BELLY, EAR_OUT, EAR_IN, NOSE, EYE, EYE_EMIS, PAW, TAIL, TAILTIP) = C
    EYE = (0.05, 0.05, 0.07)   # 赤ちゃんは黒目で固定（あどけなさ）
    EYE_EMIS = None
    SB, RB = 24, 16
    SM, RM = 18, 12
    # 体（小さめ・ぷっくりまんまる。頭を相対的に大きく見せる）
    ellipsoid(0.0, 0.205, 0.00, 0.232, 0.218, 0.222, FUR, seg=SB, ring=RB, fur=0.010)
    # 腹〜胸（クリーム）
    ellipsoid(0.0, 0.165, 0.165, 0.130, 0.140, 0.078, BELLY, seg=SM, ring=RM, fur=0.007)
    # 頭（特大・まんまる。体のすぐ上＝首は短い）
    ellipsoid(0.0, 0.520, 0.040, 0.238, 0.230, 0.228, FUR, seg=SB, ring=RB, fur=0.011)
    # 頬毛（ぷっくり・大きめ）
    for sx in (-1, 1):
        ellipsoid(sx*0.180, 0.450, 0.105, 0.092, 0.090, 0.085, FUR, seg=SM, ring=RM, fur=0.013)
    # マズル（短く丸く・低め）
    ellipsoid(0.0, 0.420, 0.205, 0.110, 0.090, 0.072, BELLY, seg=SM, ring=RM, fur=0.006)
    # 鼻パッド（小さめ）
    ellipsoid(0.0, 0.438, 0.262, 0.024, 0.019, 0.018, NOSE, seg=12, ring=9, fur=0.0)
    # 目（大きく・丸く・やや下＆前。あどけなさの核）＋強めキャッチライト
    for sx in (-1, 1):
        ellipsoid(sx*0.108, 0.500, 0.210, 0.078, 0.080, 0.066, EYE, seg=20, ring=14,
                  rough=0.10, emis=EYE_EMIS, fur=0.0)
        # 大きめキャッチライト（うるうる感）
        ellipsoid(sx*0.088, 0.528, 0.258, 0.028, 0.028, 0.020, (1.0,1.0,1.0), seg=10, ring=8,
                  rough=0.04, emis=(1.0, 1.0, 1.0), fur=0.0, ao=False)
        # 小さな副ハイライト（下側）
        ellipsoid(sx*0.122, 0.476, 0.252, 0.013, 0.013, 0.010, (1.0,1.0,1.0), seg=8, ring=6,
                  rough=0.04, emis=(0.85, 0.85, 0.9), fur=0.0, ao=False)
    # 耳（大きいまま・頭が大きいので相対的に丸く可愛く）＋内耳
    for sx in (-1, 1):
        ellipsoid(sx*0.198, 0.752, 0.000, 0.140, 0.152, 0.050, EAR_OUT,
                  seg=18, ring=12, rotZ=sx*0.12, rotX=-0.05, rough=0.6, fur=0.004)
        ellipsoid(sx*0.198, 0.752, 0.028, 0.092, 0.106, 0.030, EAR_IN,
                  seg=16, ring=10, rotZ=sx*0.12, rotX=-0.05, rough=0.6, fur=0.0)
    # 前足（ずんぐり短い手・体の前で軽く合わせる・指は短く3本）
    for sx in (-1, 1):
        ellipsoid(sx*0.060, 0.150, 0.215, 0.052, 0.050, 0.052, PAW, seg=14, ring=9, fur=0.003)
        for fx in (0.030, 0.058, 0.086):
            ellipsoid(sx*fx, 0.180, 0.232, 0.015, 0.020, 0.016, PAW, seg=8, ring=6, rotX=0.3, fur=0.0)
    # 後足（座って支える・ずんぐり）＋短い指
    for sx in (-1, 1):
        ellipsoid(sx*0.130, 0.030, 0.070, 0.072, 0.032, 0.118, PAW, seg=14, ring=9, fur=0.005)
        for fz in (0.140, 0.168):
            ellipsoid(sx*0.130, 0.024, fz, 0.020, 0.017, 0.024, PAW, seg=8, ring=6, fur=0.0)
    # 尻尾（ふさふさ・赤ちゃんは短め2節）
    ellipsoid(0.0, 0.150, -0.215, 0.088, 0.110, 0.098, TAIL, seg=SM, ring=RM, fur=0.016)
    ellipsoid(0.0, 0.300, -0.245, 0.062, 0.078, 0.066, TAILTIP, seg=SM, ring=RM, fur=0.014)
    # ヒゲ（短く・細く・本数控えめ＝左右2本ずつ）
    for sx in (-1, 1):
        base = (sx*0.05, 0.420, 0.250)
        for (dx, dy, dz) in [(0.24, 0.04, 0.05), (0.23, -0.05, 0.05)]:
            whisker(base, (sx*dx, 0.420+dy, 0.250+dz), 0.004, WHISK)
    # 比率変更後に全体スケールを焼き込む（“一回り小さい”を固定。総高が大人の約0.8になる係数）
    finalize(scale=0.85)

def finalize(scale=1.0):
    """毛皮ノイズ→接地(y=0)→任意の全体スケール→AO焼き込み。scale<1で“一回り小さい”を焼く。"""
    # 毛皮ノイズ：素体の法線方向へ ±amp 変位（毛のふわつき）
    for p in PARTS:
        if p['fur'] > 0.0:
            nrm = smooth_normals(p['verts'], p['faces'])
            amp = p['fur']
            nv = []
            for (vx, vy, vz), (nx, ny, nz) in zip(p['verts'], nrm):
                d = (_fbm(vx, vy, vz) - 0.44) * 2.3 * amp
                nv.append((vx + nx*d, vy + ny*d, vz + nz*d))
            p['verts'] = nv
    # 接地：ノイズ後の最下点を y=0 に（足元の接地Y＝原点を厳密に保つ）
    miny = min(v[1] for p in PARTS for v in p['verts'])
    for p in PARTS:
        p['verts'] = [(x, y - miny, z) for (x, y, z) in p['verts']]
    # 全体スケール（原点=足元 y=0 を中心に拡縮するので接地Yは0のまま不変）
    if scale != 1.0:
        for p in PARTS:
            p['verts'] = [(x*scale, y*scale, z*scale) for (x, y, z) in p['verts']]
    # AO：天空遮蔽（上ほど明るい）＋下向き面のキャビティ。頂点カラーCOLOR_0に格納。
    ys = [v[1] for p in PARTS for v in p['verts']]
    ymin, ymax = min(ys), max(ys)
    span = (ymax - ymin) or 1.0
    for p in PARTS:
        nrm = smooth_normals(p['verts'], p['faces'])
        if not p['ao']:
            p['vcol'] = [(1.0, 1.0, 1.0)] * len(p['verts'])
            continue
        vcol = []
        for (vx, vy, vz), (nx, ny, nz) in zip(p['verts'], nrm):
            t = (vy - ymin) / span
            sky = 0.60 + 0.40 * (t * t * (3 - 2 * t))   # 下面ほど暗く・接地感
            down = max(0.0, -ny)                          # 下向き面はさらに落とす
            ao = sky * (1.0 - 0.20 * down)
            ao = max(0.55, min(1.0, ao))
            vcol.append((ao, ao, ao))
        p['vcol'] = vcol

# ======================================================================
# GLB 書き出し
# ======================================================================
def smooth_normals(verts, faces):
    nrm = [[0.0, 0.0, 0.0] for _ in verts]
    for (a, b, c) in faces:
        ax, ay, az = verts[a]; bx, by, bz = verts[b]; cx, cy, cz = verts[c]
        ux, uy, uz = bx-ax, by-ay, bz-az
        vx, vy, vz = cx-ax, cy-ay, cz-az
        nx, ny, nz = uy*vz-uz*vy, uz*vx-ux*vz, ux*vy-uy*vx
        for idx in (a, b, c):
            nrm[idx][0] += nx; nrm[idx][1] += ny; nrm[idx][2] += nz
    out = []
    for (nx, ny, nz) in nrm:
        l = math.sqrt(nx*nx + ny*ny + nz*nz) or 1.0
        out.append((nx/l, ny/l, nz/l))
    return out

def build_glb(path):
    bin_blob = bytearray()
    bufferViews = []
    accessors = []
    materials = []
    primitives = []

    def align4():
        while len(bin_blob) % 4:
            bin_blob.append(0)

    def add_view(data_bytes, target):
        align4()
        off = len(bin_blob)
        bin_blob.extend(data_bytes)
        bufferViews.append(dict(buffer=0, byteOffset=off, byteLength=len(data_bytes), target=target))
        return len(bufferViews) - 1

    yflip = roty(math.pi)  # 造形は正面+Zで組んだ→ゲーム規約の正面-Zへ180°回す（巻き順は保たれる）
    for p in PARTS:
        verts = transform(p['verts'], yflip); faces = p['faces']; vcol = p['vcol']
        norms = smooth_normals(verts, faces)
        # POSITION
        pos = bytearray()
        for (x, y, z) in verts:
            pos += struct.pack('<3f', x, y, z)
        pv = add_view(pos, 34962)
        mins = [min(v[i] for v in verts) for i in range(3)]
        maxs = [max(v[i] for v in verts) for i in range(3)]
        accessors.append(dict(bufferView=pv, componentType=5126, count=len(verts),
                              type="VEC3", min=mins, max=maxs))
        pos_acc = len(accessors) - 1
        # NORMAL
        nb = bytearray()
        for (x, y, z) in norms:
            nb += struct.pack('<3f', x, y, z)
        nv = add_view(nb, 34962)
        accessors.append(dict(bufferView=nv, componentType=5126, count=len(norms), type="VEC3"))
        nrm_acc = len(accessors) - 1
        # COLOR_0（AOを焼いた頂点カラー・VEC3 float）
        cb = bytearray()
        for (r, g, b) in vcol:
            cb += struct.pack('<3f', r, g, b)
        cv = add_view(cb, 34962)
        accessors.append(dict(bufferView=cv, componentType=5126, count=len(vcol), type="VEC3"))
        col_acc = len(accessors) - 1
        # INDICES
        ib = bytearray()
        for (a, b, c) in faces:
            ib += struct.pack('<3H', a, b, c)
        iv = add_view(ib, 34963)
        accessors.append(dict(bufferView=iv, componentType=5123, count=len(faces)*3, type="SCALAR"))
        idx_acc = len(accessors) - 1
        # MATERIAL
        col = p['color']
        m = dict(name=f"mat{len(materials)}",
                 pbrMetallicRoughness=dict(
                     baseColorFactor=[col[0], col[1], col[2], 1.0],
                     metallicFactor=p['metal'], roughnessFactor=p['rough']))
        if p['emis']:
            m["emissiveFactor"] = list(p['emis'])
        materials.append(m)
        primitives.append(dict(attributes=dict(POSITION=pos_acc, NORMAL=nrm_acc, COLOR_0=col_acc),
                               indices=idx_acc, material=len(materials) - 1))

    gltf = dict(
        asset=dict(version="2.0", generator="voxel-world build_pet_chinchilla.py"),
        scene=0,
        scenes=[dict(nodes=[0])],
        nodes=[dict(name="chinchilla", mesh=0)],
        meshes=[dict(name="chinchilla", primitives=primitives)],
        materials=materials,
        accessors=accessors,
        bufferViews=bufferViews,
        buffers=[dict(byteLength=len(bin_blob))],
    )
    json_bytes = json.dumps(gltf, separators=(',', ':')).encode('utf-8')
    while len(json_bytes) % 4:
        json_bytes += b' '
    while len(bin_blob) % 4:
        bin_blob.append(0)
    total = 12 + 8 + len(json_bytes) + 8 + len(bin_blob)
    with open(path, 'wb') as fh:
        fh.write(b'glTF')
        fh.write(struct.pack('<II', 2, total))
        fh.write(struct.pack('<I', len(json_bytes))); fh.write(b'JSON'); fh.write(json_bytes)
        fh.write(struct.pack('<I', len(bin_blob))); fh.write(b'BIN\x00'); fh.write(bin_blob)
    tris = sum(len(p['faces']) for p in PARTS)
    print(f"wrote {path}  parts={len(PARTS)} tris={tris} size={total/1024:.1f}KB")

# ======================================================================
# プレビュー（標準ライブラリだけのソフトレンダ・AO頂点カラー反映）
# ======================================================================
def _raster(buf, depth, W, H, parts, R, light, scale, cxw, cyw, ox, oy):
    """parts を指定スケール・指定中心で buf へ描画（比較用に scale/baseline を外から固定可能）。"""
    def project(v):
        x, y, z = v
        vx = R[0]*x+R[1]*y+R[2]*z; vy = R[4]*x+R[5]*y+R[6]*z; vz = R[8]*x+R[9]*y+R[10]*z
        return ox + (vx-cxw)*scale, oy - (vy-cyw)*scale, vz
    def rotn(n):
        return (R[0]*n[0]+R[1]*n[1]+R[2]*n[2], R[4]*n[0]+R[5]*n[1]+R[6]*n[2], R[8]*n[0]+R[9]*n[1]+R[10]*n[2])
    for p in parts:
        verts = p['verts']; faces = p['faces']
        col = p['color']; emis = p['emis']; vcol = p['vcol']
        vn = [rotn(n) for n in smooth_normals(verts, faces)]
        proj = [project(v) for v in verts]
        for (a, b, c) in faces:
            ax, ay, az = proj[a]; bx, by, bz = proj[b]; cx, cy, cz = proj[c]
            na, nb, nc = vn[a], vn[b], vn[c]
            if na[2] <= -0.05 and nb[2] <= -0.05 and nc[2] <= -0.05:
                continue
            minX = max(0, int(min(ax, bx, cx))); maxX = min(W-1, int(max(ax, bx, cx))+1)
            minY = max(0, int(min(ay, by, cy))); maxY = min(H-1, int(max(ay, by, cy))+1)
            denom = (by-cy)*(ax-cx) + (cx-bx)*(ay-cy)
            if abs(denom) < 1e-7:
                continue
            ao_a = vcol[a][0]; ao_b = vcol[b][0]; ao_c = vcol[c][0]
            for py in range(minY, maxY+1):
                for px in range(minX, maxX+1):
                    w0 = ((by-cy)*(px-cx) + (cx-bx)*(py-cy)) / denom
                    w1 = ((cy-ay)*(px-cx) + (ax-cx)*(py-cy)) / denom
                    w2 = 1 - w0 - w1
                    if w0 < -0.001 or w1 < -0.001 or w2 < -0.001:
                        continue
                    zz = w0*az + w1*bz + w2*cz
                    if zz <= depth[py][px]:
                        continue
                    nx = w0*na[0] + w1*nb[0] + w2*nc[0]
                    ny = w0*na[1] + w1*nb[1] + w2*nc[1]
                    nz = w0*na[2] + w1*nb[2] + w2*nc[2]
                    nl = math.sqrt(nx*nx+ny*ny+nz*nz) or 1.0
                    diff = max(0.0, (nx*light[0]+ny*light[1]+nz*light[2])/nl)
                    rim = max(0.0, 1.0 - nz/nl) ** 2 * 0.12
                    ao = w0*ao_a + w1*ao_b + w2*ao_c
                    shade = (0.46 + 0.58*diff + rim) * ao
                    r = min(255, int(col[0]*255*shade + (emis[0]*70 if emis else 0)))
                    g = min(255, int(col[1]*255*shade + (emis[1]*70 if emis else 0)))
                    bb = min(255, int(col[2]*255*shade + (emis[2]*70 if emis else 0)))
                    depth[py][px] = zz
                    buf[py][px] = (r, g, bb)

def _light():
    light = (-0.4, 0.75, 0.55)
    ll = math.sqrt(sum(c*c for c in light)); return tuple(c/ll for c in light)

def _rot_bounds(parts, R):
    xs, ys = [], []
    for p in parts:
        for (x, y, z) in p['verts']:
            xs.append(R[0]*x+R[1]*y+R[2]*z); ys.append(R[4]*x+R[5]*y+R[6]*z)
    return min(xs), max(xs), min(ys), max(ys)

def render_panel(W, H, ry, rx, parts=None):
    parts = PARTS if parts is None else parts
    buf = [[(238, 236, 232) for _ in range(W)] for _ in range(H)]
    depth = [[-1e9]*W for _ in range(H)]
    R = matmul(rotx(rx), roty(ry))
    minx, maxx, miny, maxy = _rot_bounds(parts, R)
    cxw = (minx+maxx)/2; cyw = (miny+maxy)/2
    span = max(maxx-minx, maxy-miny) * 1.18
    scale = min(W, H) / span
    _raster(buf, depth, W, H, parts, R, _light(), scale, cxw, cyw, W/2, H/2 + 6)
    return buf

def compose(panels, cols, W, H, gap=12):
    rows = (len(panels) + cols - 1) // cols
    GW = W*cols + gap*(cols-1); GH = H*rows + gap*(rows-1)
    out = [[(238, 236, 232) for _ in range(GW)] for _ in range(GH)]
    for i, pn in enumerate(panels):
        ox0 = (i % cols)*(W+gap); oy0 = (i // cols)*(H+gap)
        for y in range(H):
            row = out[oy0+y]; src = pn[y]
            for x in range(W):
                row[ox0+x] = src[x]
    return out, GW, GH

def render_preview(path, W=440, H=520):
    panels = [render_panel(W, H, math.radians(28), math.radians(12)),
              render_panel(W, H, 0.0, math.radians(6)),
              render_panel(W, H, math.radians(180), math.radians(10))]
    out, GW, GH = compose(panels, 3, W, H)
    write_png(path, out, GW, GH)
    print(f"wrote {path}  ({GW}x{GH})")

def render_contact_sheet(path, keys, W=300, H=340):
    panels = []
    for k in keys:
        build_parts(VARIANTS[k])
        panels.append(render_panel(W, H, math.radians(20), math.radians(10)))
    out, GW, GH = compose(panels, 4, W, H)
    write_png(path, out, GW, GH)
    print(f"wrote {path}  ({GW}x{GH})  variants={','.join(keys)}")

def render_compare(path, partsA, partsB, W=460, H=580):
    """大人(左)と赤ちゃん(右)を同一スケール・同一ベースラインで並べ、体格差が分かる比較1枚。"""
    R = matmul(rotx(math.radians(8)), roty(math.radians(26)))
    light = _light()
    _, _, ayL, ayH = _rot_bounds(partsA, R)        # 大人の高さでスケールを決める
    scale = (H * 0.80) / (ayH - ayL)               # 両者共通スケール（赤ちゃんが小さく写る）
    oy = H - 46                                     # 共通ベースライン（足元 y=0）
    def panel(parts):
        buf = [[(238, 236, 232) for _ in range(W)] for _ in range(H)]
        depth = [[-1e9]*W for _ in range(H)]
        minx, maxx, miny, _ = _rot_bounds(parts, R)
        _raster(buf, depth, W, H, parts, R, light, scale, (minx+maxx)/2, miny, W/2, oy)
        return buf
    out, GW, GH = compose([panel(partsA), panel(partsB)], 2, W, H)
    write_png(path, out, GW, GH)
    print(f"wrote {path}  ({GW}x{GH})  compare: adult-violet | baby-violet")

def write_png(path, buf, W, H):
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        for x in range(W):
            r, g, b = buf[y][x]
            raw += bytes((r & 255, g & 255, b & 255))
    comp = zlib.compress(bytes(raw), 9)
    def chunk(typ, data):
        return (struct.pack('>I', len(data)) + typ + data +
                struct.pack('>I', zlib.crc32(typ + data) & 0xffffffff))
    with open(path, 'wb') as fh:
        fh.write(b'\x89PNG\r\n\x1a\n')
        fh.write(chunk(b'IHDR', struct.pack('>IIBBBBB', W, H, 8, 2, 0, 0, 0)))
        fh.write(chunk(b'IDAT', comp))
        fh.write(chunk(b'IEND', b''))

if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    models = os.path.join(root, 'models')
    # 各カラーの GLB を生成（pet_chinchilla_<key>.glb）
    for key, col in VARIANTS.items():
        build_parts(col)
        build_glb(os.path.join(models, f'pet_chinchilla_{key}.glb'))
    # ベージュを「さくら」用の基本ファイルにも複製（pet_chinchilla.glb・セーブ互換）
    build_parts(VARIANTS['beige'])
    build_glb(os.path.join(models, 'pet_chinchilla.glb'))
    # プレビュー：さくら（ベージュ）の3面＋全カラーのコンタクトシート（PARTS=ベージュのまま描画）
    render_preview(os.path.join(here, 'preview_pet_chinchilla.png'))
    render_contact_sheet(os.path.join(here, 'preview_pet_chinchilla_colors.png'), list(VARIANTS.keys()))
    # 子チンチラ（まぐろ専用・バイオレット／黒目・赤ちゃん体型・大人の約0.8）
    build_parts_baby(VARIANTS['violet'])
    build_glb(os.path.join(models, 'pet_chinchilla_violet_baby.glb'))
    # プレビュー：大人violet と 子baby の体格比較（1枚）
    build_parts(VARIANTS['violet']);      adult = [dict(p) for p in PARTS]
    build_parts_baby(VARIANTS['violet']); baby = [dict(p) for p in PARTS]
    render_compare(os.path.join(here, 'preview_pet_chinchilla_baby_compare.png'), adult, baby)
