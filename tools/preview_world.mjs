// チンチラ世界のバイオーム俯瞰マップを描く（index.html の worldgen を複製してPNG出力）
// 実行: node tools/preview_world.mjs   出力: tools/preview_world.png
import fs from 'fs';
import zlib from 'zlib';

// ---- index.html と同一の定数/関数（複製） ----
const HEIGHT = 48, SEA = 14, AMP = 22, WATER_LEVEL = SEA - 2;
function hash2(x, y) {
  let n = (x | 0) * 374761393 + (y | 0) * 668265263;
  n = (n ^ (n >> 13)) * 1274126177;
  n = (n ^ (n >> 16)) >>> 0;
  return n / 4294967295;
}
const fade = t => t*t*t*(t*(t*6-15)+10);
const lerp = (a,b,t) => a + (b-a)*t;
function valueNoise(x, y) {
  const xi = Math.floor(x), yi = Math.floor(y);
  const xf = x - xi, yf = y - yi;
  const u = fade(xf), v = fade(yf);
  return lerp(lerp(hash2(xi,yi), hash2(xi+1,yi), u),
              lerp(hash2(xi,yi+1), hash2(xi+1,yi+1), u), v);
}
function fbm(x, y) {
  let amp=1, freq=1, sum=0, norm=0;
  for (let i=0;i<4;i++){ sum += amp*valueNoise(x*freq, y*freq); norm+=amp; amp*=0.5; freq*=2; }
  return sum / norm;
}
function continental(wx, wz) { return valueNoise(wx*0.006 + 100, wz*0.006 + 100); }
function heightAt(wx, wz) {
  const cont = continental(wx, wz);
  const offset = (cont - 0.33) * 26;
  const h = SEA + Math.floor(fbm(wx*0.018, wz*0.018) * AMP * 0.55 + offset);
  return Math.max(1, Math.min(HEIGHT-8, h));
}
function biomeAt(wx, wz) {
  const h = heightAt(wx, wz);
  if (h <= WATER_LEVEL + 1) return 'ocean';
  const veg  = valueNoise(wx*0.009 - 30, wz*0.009 - 30);
  const temp = valueNoise(wx*0.006 + 50, wz*0.006 + 50);
  if (h >= SEA + 5) return 'rocky';
  if (veg < 0.17) return 'rocky';
  if (veg > 0.29) return 'forest';
  if (temp > 0.33) return 'desert';
  if (temp < 0.155) return 'snow';
  return 'plains';
}
const COLOR = {
  ocean:[58,110,165], desert:[214,196,140], snow:[236,240,245],
  forest:[36,104,52], rocky:[122,120,118], plains:[104,168,86],
};
// ---- 描画（1px = 1ブロック、原点中心の 384x384） ----
const W = 384, H = 384, half = W/2;
const buf = Buffer.alloc(W*H*3);
const count = {};
for (let py=0; py<H; py++) for (let px=0; px<W; px++) {
  const wx = px - half + 8, wz = py - half + 8;     // 原点(8,8)付近を中心に
  const bi = biomeAt(wx, wz);
  count[bi] = (count[bi]||0)+1;
  let [r,g,b] = COLOR[bi];
  // 標高で陰影をつけて起伏を見せる
  const h = heightAt(wx, wz);
  const sh = 0.72 + 0.012 * (h - SEA);
  r = Math.max(0, Math.min(255, r*sh|0)); g = Math.max(0, Math.min(255, g*sh|0)); b = Math.max(0, Math.min(255, b*sh|0));
  const i = (py*W+px)*3; buf[i]=r; buf[i+1]=g; buf[i+2]=b;
}
// 原点マーカー（白十字）
for (let d=-4; d<=4; d++){ const cx=half-8, cy=half-8;
  for (const [x,y] of [[cx+d,cy],[cx,cy+d]]) if(x>=0&&x<W&&y>=0&&y<H){ const i=(y*W+x)*3; buf[i]=255;buf[i+1]=80;buf[i+2]=80; } }

// PNG(RGB) 書き出し
function png(path, W, H, rgb){
  const raw = Buffer.alloc((W*3+1)*H);
  for (let y=0;y<H;y++){ raw[y*(W*3+1)] = 0; rgb.copy(raw, y*(W*3+1)+1, y*W*3, (y+1)*W*3); }
  const comp = zlib.deflateSync(raw, {level:9});
  const chunk = (t, d) => { const len=Buffer.alloc(4); len.writeUInt32BE(d.length);
    const tc = Buffer.concat([Buffer.from(t), d]); const crc=Buffer.alloc(4);
    crc.writeUInt32BE(zlibCrc(tc)>>>0); return Buffer.concat([len, tc, crc]); };
  const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(W,0); ihdr.writeUInt32BE(H,4); ihdr[8]=8; ihdr[9]=2;
  fs.writeFileSync(path, Buffer.concat([Buffer.from([137,80,78,71,13,10,26,10]),
    chunk('IHDR', ihdr), chunk('IDAT', comp), chunk('IEND', Buffer.alloc(0))]));
}
function zlibCrc(buf){ let c=~0; for (let i=0;i<buf.length;i++){ c^=buf[i]; for(let k=0;k<8;k++) c = (c>>>1) ^ (0xEDB88320 & -(c&1)); } return ~c; }
png('tools/preview_world.png', W, H, buf);
const tot = W*H;
console.log('biome%:', Object.fromEntries(Object.entries(count).map(([k,v])=>[k, (100*v/tot).toFixed(1)+'%'])));
console.log('wrote tools/preview_world.png');
