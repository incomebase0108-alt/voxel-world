# -*- coding: utf-8 -*-
# VOXEL WORLD - 「さくらの家」1F 間取りの確認用 俯瞰図（ユーザー提供の間取りPDFを近似）
#   ※まずレイアウトの当たりを確認するためのラフ。OKならこの座標をそのままゲーム内ボクセル建築に使う。
#   出力: tools/preview_house_1f.png
#   実行: python3 tools/build_house_preview.py
import struct, zlib, os

# 1ユニット=1ブロック(≒1m)想定のグリッド。プランの左→右/上→下の配置を近似。
# room: (label, x, z, w, h, colorkey)   ※x=東, z=南
ROOMS_1F = [
    ('GARAGE',     26, 2, 13, 11, 'garage'),
    ('PORCH',      24, 0,  4,  2, 'porch'),
    ('ENT/HALL',   20, 6,  5,  9, 'hall'),
    ('UP(階段)',   18, 6,  2,  3, 'stair'),    # 1F→2Fの階段
    ('WC/UTIL',    17, 2,  3,  4, 'water'),
    ('VANITY',     17,12,  3,  3, 'water'),
    ('LDK 50J',    10, 2,  9,  8, 'ldk'),
    ('LIVING',     10,10,  5,  5, 'living'),
    ('KITCHEN',    15,10,  3,  4, 'kitchen'),
    ('DINING',     15,14,  5,  4, 'dining'),
    ('JP-RM(水槽)', 4, 2, 6, 7, 'tatami'),     # 和室＋水槽置場
    ('BEDRM',       0,10,  6,  6, 'bed'),
    ('JP-RM 6J',    0, 2,  4,  5, 'tatami'),
    ('PATIO',       0,17,  6,  4, 'patio'),
    ('JP-RM/仏間', 10,17,  5,  4, 'tatami'),
]
# 2F：子供部屋にさくらのケージ（スタート）。階段(DN)で1Fへ降りる。
ROOMS_2F = [
    ('M.BEDRM',     27, 4, 11, 8, 'bed'),
    ('KIDS-A(子供)', 4, 2, 6, 6, 'kids'),       # ★さくらのケージ（子供部屋）
    ('KIDS-B(子供)', 4, 9, 6, 6, 'kids'),
    ('JP-RM',        0, 2, 4, 6, 'tatami'),
    ('GUEST RM',    27,13, 8, 6, 'guest'),
    ('WINECELLAR',  35, 2, 4, 4, 'wine'),
    ('HALL',        12, 4, 9, 12, 'hall'),
    ('DN(階段)',    18, 6, 2, 3, 'stair'),       # 2F→1Fの階段
    ('UTIL/VANITY', 11, 2, 5, 2, 'water'),
    ('WC',          11,16, 3, 2, 'water'),
    ('WIC',         22, 4, 4, 5, 'bed'),
    ('VOID(吹抜)',  22,10, 5, 6, 'void'),
    ('BALCONY.A',   30,20, 5, 2, 'porch'),
    ('BALCONY.B',    0,16, 6, 2, 'porch'),
]
# さくらのケージ（2F 子供部屋A）と玄関の出口（1F）
CAGE = (6, 4)            # KIDS-A 内＝スタート
EXIT = (22, 15)         # 1F ENT/HALL 南の玄関＝外への出口

COL = {
    'garage':(150,150,156), 'porch':(176,168,150), 'hall':(214,205,180),
    'stair':(120,110,150), 'water':(150,200,210), 'ldk':(232,210,160),
    'living':(220,196,150), 'kitchen':(210,190,160), 'dining':(214,200,168),
    'tatami':(150,196,120), 'bed':(196,180,210), 'patio':(170,210,160),
    'kids':(245,200,120), 'guest':(200,190,215), 'wine':(150,90,90), 'void':(220,220,222),
}
WALL = (40, 36, 32); BG = (238, 236, 232); CAGEC = (235, 120, 150); EXITC = (90, 200, 110); STAIRC = (120,110,150)

UNIT = 18
GX = 40; GZ = 22
PW = GX*UNIT; PH = GZ*UNIT
GAP = 24
W = PW*2 + GAP; H = PH
img = [[BG[:] for _ in range(W)] for _ in range(H)]

def fillrect(ox, gx, gz, gw, gh, col, border=True):
    x0, z0 = ox + gx*UNIT, gz*UNIT
    x1, z1 = ox + (gx+gw)*UNIT, (gz+gh)*UNIT
    for y in range(max(0,z0), min(H,z1)):
        for x in range(max(0,x0), min(W,x1)):
            edge = border and (x < x0+2 or x >= x1-2 or y < z0+2 or y >= z1-2)
            img[y][x] = list(WALL if edge else col)

def marker(ox, gx, gz, col, r=8):
    cx, cy = ox + int((gx+0.5)*UNIT), int((gz+0.5)*UNIT)
    for y in range(cy-r-1, cy+r+1):
        for x in range(cx-r-1, cx+r+1):
            if 0<=x<W and 0<=y<H and (x-cx)**2+(y-cy)**2 <= r*r: img[y][x] = list(col)

# 左パネル=1F、右パネル=2F
for (lab, x, z, w, h, ck) in ROOMS_1F: fillrect(0, x, z, w, h, COL.get(ck,(200,200,200)))
marker(0, *EXIT, EXITC)            # 1F 玄関の出口
marker(0, 18.5, 7, STAIRC, 6)      # 1F 階段位置
for (lab, x, z, w, h, ck) in ROOMS_2F: fillrect(PW+GAP, x, z, w, h, COL.get(ck,(200,200,200)))
marker(PW+GAP, *CAGE, CAGEC)       # 2F 子供部屋＝さくらのケージ（スタート）
marker(PW+GAP, 18.5, 7, STAIRC, 6) # 2F 階段(DN)

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
    print('wrote tools/preview_house_1f.png (左=1F / 右=2F)', f'{GX}x{GZ} units x2')
