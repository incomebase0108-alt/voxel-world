# -*- coding: utf-8 -*-
# VOXEL WORLD - ペット：チンチラ「もふ」（pet_chinchilla）
#   ユーザーの実物チンチラ写真に寄せた専用ペットモデル。
#   ※この環境に Blender が無いため、標準ライブラリだけで glTF(GLB) を直接生成する。
#   出力: models/pet_chinchilla.glb   （Y-up / 足元 y=0 / 正面 -Z / 高さ約0.7m）
#   プレビュー: tools/preview_pet_chinchilla.png （正面＋3/4のソフトレンダ）
#
#   見た目方針（写真準拠）：ベージュ系のふわふわ毛・大きな丸い耳（内耳ピンク）・
#     つぶらな黒目・ピンクの鼻・長いひげ・ちょこんとした前足・ふさふさ尻尾。
#     座って前足を揃えたチンチラらしい姿勢。ボスの発光赤目/王冠は付けない（普段着の相棒）。
#
#   実行: python3 tools/build_pet_chinchilla.py
import struct, json, zlib, math, os

# ----------------------------------------------------------------------
# パーツ集積（各パーツ＝1プリミティブ＝1マテリアル）
# ----------------------------------------------------------------------
PARTS = []  # {verts:[(x,y,z)], faces:[(a,b,c)], color:(r,g,b), rough, metal, emis:(r,g,b)|None}

def add(verts, faces, color, rough=0.85, metal=0.0, emis=None):
    PARTS.append(dict(verts=verts, faces=faces, color=color, rough=rough, metal=metal, emis=emis))

def uv_sphere(cx, cy, cz, rx, ry, rz, seg=16, ring=10, sy=1.0):
    """中心(cx,cy,cz)・半径(rx,ry,rz)の楕円球。sy: 上半分の潰し(尻つぼみ用)は使わず1.0固定。"""
    verts, faces = [], []
    for i in range(ring + 1):
        v = i / ring
        phi = v * math.pi               # 0..pi  (上→下)
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
    R = [0]*12
    a = [A[0:4], A[4:8], A[8:12], [0,0,0,1]]
    b = [B[0:4], B[4:8], B[8:12], [0,0,0,1]]
    out = [[0]*4 for _ in range(4)]
    for i in range(4):
        for j in range(4):
            out[i][j] = sum(a[i][k]*b[k][j] for k in range(4))
    return out[0] + out[1] + out[2]

def ellipsoid(cx, cy, cz, rx, ry, rz, color, seg=16, ring=10, rough=0.85, metal=0.0,
              emis=None, rotX=0.0, rotY=0.0, rotZ=0.0):
    v, f = uv_sphere(0, 0, 0, rx, ry, rz, seg, ring)
    m = [1,0,0,0, 0,1,0,0, 0,0,1,0]
    if rotZ: m = matmul(rotz(rotZ), m)
    if rotY: m = matmul(roty(rotY), m)
    if rotX: m = matmul(rotx(rotX), m)
    m = matmul([1,0,0,cx, 0,1,0,cy, 0,0,1,cz], m)
    add(transform(v, m), f, color, rough, metal, emis)

def whisker(p0, p1, r, color):
    """p0->p1 の細い四角チューブ（ひげ）。"""
    ax = [p1[i]-p0[i] for i in range(3)]
    L = math.sqrt(sum(c*c for c in ax)) or 1e-6
    ax = [c/L for c in ax]
    # 軸に垂直な基底
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
    add(verts, faces, color, rough=0.5)

# ----------------------------------------------------------------------
# 配色（写真2枚目準拠：温かみのあるグレージュ＝バイオレット系ベージュ）
# ----------------------------------------------------------------------
FUR    = (0.66, 0.61, 0.585)  # 本体の毛：温かいグレージュ
FUR_SH = (0.55, 0.50, 0.49)   # 背・後頭の陰
BELLY  = (0.93, 0.91, 0.87)   # 腹・口元のクリーム白
EAR_OUT= (0.92, 0.72, 0.72)   # 大きな耳：地肌のピンク（外）
EAR_IN = (0.85, 0.58, 0.60)   # 内耳の陰ピンク
NOSE   = (0.95, 0.66, 0.68)   # 鼻ピンク
EYE    = (0.045, 0.035, 0.045)# 大きな真っ黒の目
EYEHI  = (1.0, 1.0, 1.0)      # 目のハイライト
PAW    = (0.88, 0.85, 0.80)   # 前足・後足（白っぽい）
WHISK  = (0.97, 0.96, 0.95)   # 長い白ひげ
TAIL   = (0.62, 0.57, 0.555)  # 尻尾（毛と同系・やや暗）
TAILTIP= (0.92, 0.90, 0.87)   # 尻尾の先（クリーム白）

# ----------------------------------------------------------------------
# チンチラ造形（座り姿勢・正面 -Z）
#   ※座標: +Y 上 / -Z 正面 / 後で min(y)=0 へ平行移動
# ----------------------------------------------------------------------
# 体（まんまるの胴・座っているので下が広い）
ellipsoid(0.0, 0.27, 0.00, 0.250, 0.285, 0.230, FUR, ring=12)
# 腹〜胸（前面のクリーム・控えめに）
ellipsoid(0.0, 0.215, 0.180, 0.140, 0.180, 0.085, BELLY, ring=10)
# 頭（大きめ・胴と繋がる・前へ少し出す）
ellipsoid(0.0, 0.520, 0.075, 0.205, 0.195, 0.195, FUR, ring=12)
# 口元・頬（白・小さめ）
ellipsoid(0.0, 0.450, 0.215, 0.105, 0.088, 0.090, BELLY, ring=10)
# 鼻（ピンク・小さな逆三角）
ellipsoid(0.0, 0.468, 0.300, 0.030, 0.024, 0.024, NOSE, ring=8)
# 目（左右・大きく真っ黒・顔の表面に出す）＋ハイライト
for sx in (-1, 1):
    ellipsoid(sx*0.105, 0.565, 0.215, 0.076, 0.082, 0.060, EYE, seg=18, ring=12, rough=0.16)
    ellipsoid(sx*0.085, 0.595, 0.262, 0.023, 0.023, 0.016, EYEHI, seg=8, ring=6,
              rough=0.06, emis=(0.9, 0.9, 0.9))
# 耳（特大の丸耳：地肌のピンク。立ち気味＝写真2準拠）＋内耳の陰
for sx in (-1, 1):
    ellipsoid(sx*0.175, 0.770, -0.010, 0.130, 0.180, 0.050, EAR_OUT,
              seg=16, ring=11, rotZ=sx*0.10, rotX=-0.04, rough=0.6)
    ellipsoid(sx*0.175, 0.770, 0.020, 0.082, 0.126, 0.030, EAR_IN,
              seg=14, ring=9, rotZ=sx*0.10, rotX=-0.04, rough=0.6)
# 前足（ちょこんと揃える・胸の前・白っぽい）
for sx in (-1, 1):
    ellipsoid(sx*0.085, 0.115, 0.205, 0.050, 0.060, 0.066, PAW, seg=12, ring=8)
# 後足（座って前へ投げ出す）
for sx in (-1, 1):
    ellipsoid(sx*0.140, 0.035, 0.095, 0.072, 0.034, 0.125, PAW, seg=12, ring=8)
# 尻尾（ふさふさ・後ろへ跳ね上げ・先はクリーム白）
ellipsoid(0.0, 0.20, -0.255, 0.095, 0.135, 0.115, TAIL, ring=10)
ellipsoid(0.0, 0.370,-0.305, 0.082, 0.108, 0.090, TAIL, ring=10)
ellipsoid(0.0, 0.500,-0.320, 0.066, 0.082, 0.070, TAILTIP, ring=10)
# ひげ（左右に長め・数本）
for sx in (-1, 1):
    base = (sx*0.06, 0.455, 0.285)
    for (dx, dy, dz) in [(0.40, 0.06, 0.07), (0.42, -0.01, 0.05),
                         (0.39, -0.08, 0.07), (0.35, 0.12, 0.06)]:
        whisker(base, (sx*dx, 0.455+dy, 0.285+dz), 0.005, WHISK)

# ----------------------------------------------------------------------
# 足元を y=0 に合わせる
# ----------------------------------------------------------------------
miny = min(v[1] for p in PARTS for v in p['verts'])
for p in PARTS:
    p['verts'] = [(x, y - miny, z) for (x, y, z) in p['verts']]

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
        verts = transform(p['verts'], yflip); faces = p['faces']
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
        primitives.append(dict(attributes=dict(POSITION=pos_acc, NORMAL=nrm_acc),
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
# プレビュー（標準ライブラリだけのソフトレンダ：3/4 と 正面）
# ======================================================================
def render_preview(path, W=440, H=520):
    panels = []
    for (ry, rx, label) in [(math.radians(28), math.radians(12), "3/4"),
                            (0.0, math.radians(6), "front")]:
        buf = [[(238, 236, 232) for _ in range(W)] for _ in range(H)]
        depth = [[-1e9]*W for _ in range(H)]  # +Z がカメラ手前。大きいほど手前。
        R = matmul(rotx(rx), roty(ry))
        light = (-0.4, 0.75, 0.55)
        ll = math.sqrt(sum(c*c for c in light)); light = tuple(c/ll for c in light)
        # ワールド境界（フィット用）
        allv = []
        for p in PARTS:
            for v in p['verts']:
                x, y, z = v
                allv.append((R[0]*x+R[1]*y+R[2]*z, R[4]*x+R[5]*y+R[6]*z, R[8]*x+R[9]*y+R[10]*z))
        minx = min(v[0] for v in allv); maxx = max(v[0] for v in allv)
        miny = min(v[1] for v in allv); maxy = max(v[1] for v in allv)
        cxw = (minx+maxx)/2; cyw = (miny+maxy)/2
        span = max(maxx-minx, maxy-miny) * 1.18
        scale = min(W, H) / span
        ox, oy = W/2, H/2 + 6
        def project(v):
            x, y, z = v
            vx = R[0]*x+R[1]*y+R[2]*z; vy = R[4]*x+R[5]*y+R[6]*z; vz = R[8]*x+R[9]*y+R[10]*z
            sx = ox + (vx-cxw)*scale
            sy = oy - (vy-cyw)*scale
            return sx, sy, vz
        def rotn(n):
            return (R[0]*n[0]+R[1]*n[1]+R[2]*n[2],
                    R[4]*n[0]+R[5]*n[1]+R[6]*n[2],
                    R[8]*n[0]+R[9]*n[1]+R[10]*n[2])
        for p in PARTS:
            verts = p['verts']; faces = p['faces']
            col = p['color']; emis = p['emis']
            vn = [rotn(n) for n in smooth_normals(verts, faces)]  # スムーズ法線（縞を消す）
            proj = [project(v) for v in verts]
            for (a, b, c) in faces:
                ax, ay, az = proj[a]; bx, by, bz = proj[b]; cx, cy, cz = proj[c]
                na, nb, nc = vn[a], vn[b], vn[c]
                # おおまかな裏面除去（3頂点とも手前を向いていない面は捨てる）
                if na[2] <= -0.05 and nb[2] <= -0.05 and nc[2] <= -0.05:
                    continue
                minX = max(0, int(min(ax, bx, cx))); maxX = min(W-1, int(max(ax, bx, cx))+1)
                minY = max(0, int(min(ay, by, cy))); maxY = min(H-1, int(max(ay, by, cy))+1)
                denom = (by-cy)*(ax-cx) + (cx-bx)*(ay-cy)
                if abs(denom) < 1e-7:
                    continue
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
                        rim = max(0.0, 1.0 - nz/nl) ** 2 * 0.12   # ふちの柔らかな明かり
                        shade = 0.46 + 0.58*diff + rim
                        r = min(255, int(col[0]*255*shade + (emis[0]*70 if emis else 0)))
                        g = min(255, int(col[1]*255*shade + (emis[1]*70 if emis else 0)))
                        bb = min(255, int(col[2]*255*shade + (emis[2]*70 if emis else 0)))
                        depth[py][px] = zz
                        buf[py][px] = (r, g, bb)
        panels.append(buf)
    # 2枚を横に連結
    GW = W*2 + 12
    out = [[(238, 236, 232) for _ in range(GW)] for _ in range(H)]
    for y in range(H):
        for x in range(W):
            out[y][x] = panels[0][y][x]
            out[y][x+W+12] = panels[1][y][x]
    write_png(path, out, GW, H)
    print(f"wrote {path}  ({GW}x{H})")

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
    build_glb(os.path.join(root, 'models', 'pet_chinchilla.glb'))
    render_preview(os.path.join(here, 'preview_pet_chinchilla.png'))
