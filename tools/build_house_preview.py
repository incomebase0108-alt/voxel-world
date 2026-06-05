# -*- coding: utf-8 -*-
# VOXEL WORLD - 「さくらの家」1F 間取りの確認用 俯瞰図（ユーザー提供の間取りPDFを近似）
#   ※まずレイアウトの当たりを確認するためのラフ。OKならこの座標をそのままゲーム内ボクセル建築に使う。
#   出力: tools/preview_house_1f.png
#   実行: python3 tools/build_house_preview.py
import struct, zlib, os

# 1ユニット=1ブロック(≒1m)想定のグリッド。プランの左→右/上→下の配置を近似。
# room: (label, x, z, w, h, colorkey)   ※x=東, z=南
ROOMS = [
    ('GARAGE',     26, 2, 13, 11, 'garage'),
    ('PORCH',      24, 0,  4,  2, 'porch'),
    ('ENT/HALL',   20, 6,  5,  9, 'hall'),
    ('UP',         18, 6,  2,  3, 'stair'),
    ('WC/UTIL',    17, 2,  3,  4, 'water'),
    ('VANITY',     17,12,  3,  3, 'water'),
    ('LDK 50J',    10, 2,  9,  8, 'ldk'),
    ('LIVING',     10,10,  5,  5, 'living'),
    ('KITCHEN',    15,10,  3,  4, 'kitchen'),
    ('DINING',     15,14,  5,  4, 'dining'),
    ('JP-RM(SAKURA)', 4, 2, 6, 7, 'tatami'),   # 和室＋水槽置場＝さくらの居場所（スタート）
    ('BEDRM',       0,10,  6,  6, 'bed'),
    ('JP-RM 6J',    0, 2,  4,  5, 'tatami'),
    ('PATIO',       0,17,  6,  4, 'patio'),
    ('JP-RM/仏間', 10,17,  5,  4, 'tatami'),
]
# さくらのケージ（水槽置場）と玄関の出口（脱走ゴール）
CAGE = (6, 4)            # JP-RM(SAKURA) 内
EXIT = (22, 15)         # ENT/HALL 南の玄関＝外への出口

COL = {
    'garage':(150,150,156), 'porch':(176,168,150), 'hall':(214,205,180),
    'stair':(190,180,150), 'water':(150,200,210), 'ldk':(232,210,160),
    'living':(220,196,150), 'kitchen':(210,190,160), 'dining':(214,200,168),
    'tatami':(150,196,120), 'bed':(196,180,210), 'patio':(170,210,160),
}
WALL = (40, 36, 32); BG = (238, 236, 232); CAGEC = (235, 120, 150); EXITC = (90, 200, 110)

UNIT = 20
GX = 40; GZ = 22
W = GX*UNIT; H = GZ*UNIT
img = [[BG[:] for _ in range(W)] for _ in range(H)]

def fillrect(gx, gz, gw, gh, col, border=True):
    x0, z0 = gx*UNIT, gz*UNIT
    x1, z1 = (gx+gw)*UNIT, (gz+gh)*UNIT
    for y in range(max(0,z0), min(H,z1)):
        for x in range(max(0,x0), min(W,x1)):
            edge = border and (x < x0+2 or x >= x1-2 or y < z0+2 or y >= z1-2)
            img[y][x] = list(WALL if edge else col)

def marker(gx, gz, col):
    cx, cy = int((gx+0.5)*UNIT), int((gz+0.5)*UNIT)
    for y in range(cy-7, cy+8):
        for x in range(cx-7, cx+8):
            if 0<=x<W and 0<=y<H and (x-cx)**2+(y-cy)**2 <= 49: img[y][x] = list(col)

for (lab, x, z, w, h, ck) in ROOMS:
    fillrect(x, z, w, h, COL.get(ck, (200,200,200)))
marker(*CAGE, CAGEC)   # さくら
marker(*EXIT, EXITC)   # 出口

def write_png(path):
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        for x in range(W):
            r,g,b = img[y][x]; raw += bytes((r&255,g&255,b&255))
    comp = zlib.compress(bytes(raw), 9)
    def chunk(t,d): return struct.pack('>I',len(d))+t+d+struct.pack('>I', zlib.crc32(t+d)&0xffffffff)
    with open(path,'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n')
        f.write(chunk(b'IHDR', struct.pack('>IIBBBBB', W,H,8,2,0,0,0)))
        f.write(chunk(b'IDAT', comp)); f.write(chunk(b'IEND', b''))

if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    write_png(os.path.join(here, 'preview_house_1f.png'))
    print('wrote tools/preview_house_1f.png', f'{GX}x{GZ} units')
