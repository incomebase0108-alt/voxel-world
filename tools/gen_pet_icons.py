# -*- coding: utf-8 -*-
# VOXEL WORLD - ペット用アイテムのアイコン生成（標準ライブラリのみ・透過RGBA PNG 128px）
#   出力: tools/icons/icon_item_himawari.png  （ひまわり＝ペットの大好物）
#   実行: python3 tools/gen_pet_icons.py
import struct, zlib, math, os

N = 128
CX = CY = N / 2.0

def blank():
    return [[(0, 0, 0, 0) for _ in range(N)] for _ in range(N)]

def over(dst, x, y, rgba):
    if 0 <= x < N and 0 <= y < N:
        r, g, b, a = rgba
        dr, dg, db, da = dst[y][x]
        ia = a / 255.0
        dst[y][x] = (int(r*ia + dr*(1-ia)), int(g*ia + dg*(1-ia)),
                     int(b*ia + db*(1-ia)), max(da, a))

def sunflower(img):
    pet = (250, 196, 40, 255); peted = (224, 158, 26, 255)
    cen = (96, 60, 28, 255); cen2 = (60, 36, 16, 255)
    petals = 12
    for k in range(petals):
        ang = k * 2*math.pi/petals
        pcx = CX + math.cos(ang)*40; pcy = CY + math.sin(ang)*40
        ca, sa = math.cos(ang), math.sin(ang)
        amaj, amin = 27.0, 12.0
        for y in range(N):
            for x in range(N):
                dx, dy = x - pcx, y - pcy
                lx = dx*ca + dy*sa            # 放射方向（長軸）
                ly = -dx*sa + dy*ca           # 接線方向（短軸）
                e = (lx/amaj)**2 + (ly/amin)**2
                if e <= 1.0:
                    over(img, x, y, peted if e > 0.74 else pet)
    # 中心の種盤
    for y in range(N):
        for x in range(N):
            d = math.hypot(x-CX, y-CY)
            if d <= 30:
                over(img, x, y, cen if d > 24 else cen2)
    # 種の粒（市松っぽい点）
    for gy in range(-5, 6):
        for gx in range(-5, 6):
            px = CX + gx*4.4; py = CY + gy*4.4
            if math.hypot(px-CX, py-CY) <= 22 and (gx+gy) % 2 == 0:
                for yy in range(int(py-1), int(py+2)):
                    for xx in range(int(px-1), int(px+2)):
                        over(img, xx, yy, (38, 22, 10, 255))

def write_png_rgba(path, img):
    raw = bytearray()
    for y in range(N):
        raw.append(0)
        for x in range(N):
            r, g, b, a = img[y][x]
            raw += bytes((r & 255, g & 255, b & 255, a & 255))
    comp = zlib.compress(bytes(raw), 9)
    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n')
        f.write(chunk(b'IHDR', struct.pack('>IIBBBBB', N, N, 8, 6, 0, 0, 0)))  # color type 6 = RGBA
        f.write(chunk(b'IDAT', comp))
        f.write(chunk(b'IEND', b''))

if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, 'icons', 'icon_item_himawari.png')
    img = blank(); sunflower(img); write_png_rgba(out, img)
    print('wrote', out)
