# -*- coding: utf-8 -*-
# VOXEL WORLD - 任意の .glb を読み込み、build_pet_chinchilla のソフトレンダで
#   プレビューPNGにする共通ツール（Blender出力mob/ボス/NPCの確認用）。
#   使い方:
#     import glb_preview as gp
#     gp.render_views('models/mob_cow.glb', 'tools/preview_cow_detail.png')
#   ※ノード階層のTRSを合成して頂点をワールド化し、各primitiveのbaseColorで塗る。
#     法線はスムーズ法線を再計算（プレビュー専用・元GLBは無加工）。
import struct, json, math
import build_pet_chinchilla as ck

def _read_glb(path):
    with open(path, 'rb') as f:
        data = f.read()
    assert data[:4] == b'glTF'
    off = 12; gltf = None; bin_blob = b''
    n = len(data)
    while off < n:
        clen, ctype = struct.unpack_from('<II', data, off); off += 8
        chunk = data[off:off+clen]; off += clen
        if ctype == 0x4E4F534A:  # JSON
            gltf = json.loads(chunk.decode('utf-8'))
        elif ctype == 0x004E4942:  # BIN
            bin_blob = chunk
    return gltf, bin_blob

_CT = {5120:('b',1),5121:('B',1),5122:('h',2),5123:('H',2),5125:('I',4),5126:('f',4)}
_NC = {'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}

def _accessor(gltf, blob, idx):
    a = gltf['accessors'][idx]
    bv = gltf['bufferViews'][a['bufferView']]
    base = bv.get('byteOffset',0) + a.get('byteOffset',0)
    fmt, size = _CT[a['componentType']]; nc = _NC[a['type']]
    stride = bv.get('byteStride') or size*nc
    out = []
    for i in range(a['count']):
        o = base + i*stride
        out.append(struct.unpack_from('<'+fmt*nc, blob, o))
    return out

def _mat_mul(A, B):
    R = [0.0]*16
    for r in range(4):
        for c in range(4):
            R[r*4+c] = sum(A[r*4+k]*B[k*4+c] for k in range(4))
    return R

def _identity(): return [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]

def _trs(node):
    if 'matrix' in node:
        m = node['matrix']  # column-major in glTF
        return [m[0],m[4],m[8],m[12], m[1],m[5],m[9],m[13],
                m[2],m[6],m[10],m[14], m[3],m[7],m[11],m[15]]
    t = node.get('translation',[0,0,0]); q = node.get('rotation',[0,0,0,1]); s = node.get('scale',[1,1,1])
    x,y,z,w = q
    xx,yy,zz = x*x,y*y,z*z; xy,xz,yz = x*y,x*z,y*z; wx,wy,wz = w*x,w*y,w*z
    R = [1-2*(yy+zz), 2*(xy-wz),   2*(xz+wy),   0,
         2*(xy+wz),   1-2*(xx+zz), 2*(yz-wx),   0,
         2*(xz-wy),   2*(yz+wx),   1-2*(xx+yy), 0,
         0,0,0,1]
    S = [s[0],0,0,0, 0,s[1],0,0, 0,0,s[2],0, 0,0,0,1]
    M = _mat_mul(R, S)
    M[3]=t[0]; M[7]=t[1]; M[11]=t[2]
    return M

def _apply(M, v):
    x,y,z = v
    return (M[0]*x+M[1]*y+M[2]*z+M[3], M[4]*x+M[5]*y+M[6]*z+M[7], M[8]*x+M[9]*y+M[10]*z+M[11])

def load_parts(path):
    """GLB を build_pet_chinchilla のPARTS互換 list に変換（ワールド座標・baseColor）。"""
    gltf, blob = _read_glb(path)
    parts = []
    scene = gltf.get('scene', 0)
    roots = gltf['scenes'][scene]['nodes']
    def walk(ni, parent):
        node = gltf['nodes'][ni]
        world = _mat_mul(parent, _trs(node))
        if 'mesh' in node:
            mesh = gltf['meshes'][node['mesh']]
            for prim in mesh['primitives']:
                pos = _accessor(gltf, blob, prim['attributes']['POSITION'])
                verts = [_apply(world, p) for p in pos]
                idx = _accessor(gltf, blob, prim['indices'])
                faces = [(idx[i][0], idx[i+1][0], idx[i+2][0]) for i in range(0, len(idx), 3)]
                col = (0.7,0.7,0.7); emis = None
                mi = prim.get('material')
                if mi is not None:
                    m = gltf['materials'][mi]
                    pbr = m.get('pbrMetallicRoughness', {})
                    bc = pbr.get('baseColorFactor', [0.7,0.7,0.7,1])
                    col = (bc[0], bc[1], bc[2])
                    if m.get('emissiveFactor') and sum(m['emissiveFactor'])>0.02:
                        emis = tuple(m['emissiveFactor'])
                parts.append(dict(verts=verts, faces=faces, color=col,
                                  vcol=[(1.0,1.0,1.0)]*len(verts), emis=emis, fur=0.0,
                                  rough=0.8, metal=0.0))
        for c in node.get('children', []):
            walk(c, world)
    for r in roots:
        walk(r, _identity())
    return parts

def render_views(glb_path, out_png, W=360, H=400, angles=None):
    """正面/3-4/真横の3面を1枚に。"""
    if angles is None:
        angles = [(0.0, math.radians(6)), (math.radians(34), math.radians(10)), (math.radians(90), math.radians(6))]
    parts = load_parts(glb_path)
    ck.PARTS.clear(); ck.PARTS.extend(parts)
    panels = [ck.render_panel(W, H, ry, rx) for (ry, rx) in angles]
    out, GW, GH = ck.compose(panels, len(panels), W, H)
    ck.write_png(out_png, out, GW, GH)
    print(f"wrote {out_png} ({GW}x{GH}) from {glb_path}")

if __name__ == '__main__':
    import sys
    render_views(sys.argv[1], sys.argv[2])
