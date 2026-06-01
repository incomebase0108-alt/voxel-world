// テスト用ダミー player.glb 生成スクリプト（Blender不使用・Node標準のみ）
//   目的: GLB読み込み口の検証＋4号機への「原点/向き/スケール」見本
//   仕様: Y-up / 足元中心が原点(0,0,0) / 正面 -Z / 身長 約2m / 1ブロック≒1m
//   箱の組み合わせで人型を表現（最小構成）。4号機の本番モデルで上書きされる前提。
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(__dirname, '..', 'models', 'player.glb');

// ---- 単位立方体（-0.5..0.5）の面データ ----
const FACES = [
  { n:[ 1,0,0], c:[[.5,-.5,-.5],[.5,.5,-.5],[.5,.5,.5],[.5,-.5,.5]] },
  { n:[-1,0,0], c:[[-.5,-.5,.5],[-.5,.5,.5],[-.5,.5,-.5],[-.5,-.5,-.5]] },
  { n:[0, 1,0], c:[[-.5,.5,-.5],[-.5,.5,.5],[.5,.5,.5],[.5,.5,-.5]] },
  { n:[0,-1,0], c:[[-.5,-.5,.5],[-.5,-.5,-.5],[.5,-.5,-.5],[.5,-.5,.5]] },
  { n:[0,0, 1], c:[[.5,-.5,.5],[.5,.5,.5],[-.5,.5,.5],[-.5,-.5,.5]] },
  { n:[0,0,-1], c:[[-.5,-.5,-.5],[-.5,.5,-.5],[.5,.5,-.5],[.5,-.5,-.5]] },
];
const positions = [], normals = [], indices = [];
for (const f of FACES) {
  const b = positions.length / 3;
  for (const c of f.c) positions.push(...c);
  for (let i=0;i<4;i++) normals.push(...f.n);
  indices.push(b,b+1,b+2, b,b+2,b+3);
}
const posArr  = new Float32Array(positions); // 24*3 = 288 bytes
const normArr = new Float32Array(normals);   // 288 bytes
const idxArr  = new Uint16Array(indices);    // 36*2 = 72 bytes
const bin = Buffer.concat([
  Buffer.from(posArr.buffer),
  Buffer.from(normArr.buffer),
  Buffer.from(idxArr.buffer),
]);
const POS_LEN = posArr.byteLength, NRM_LEN = normArr.byteLength, IDX_LEN = idxArr.byteLength;

// ---- 体のパーツ（mesh: 0=胴体色, 1=肌色 / 単位立方体を scale+translate で配置）----
// translation = パーツ中心, scale = [幅, 高さ, 奥行]
const parts = [
  { name:'legL',  mesh:0, t:[-0.16, 0.45, 0],   s:[0.22, 0.90, 0.28] },
  { name:'legR',  mesh:0, t:[ 0.16, 0.45, 0],   s:[0.22, 0.90, 0.28] },
  { name:'torso', mesh:0, t:[ 0.00, 1.28, 0],   s:[0.60, 0.75, 0.32] },
  { name:'armL',  mesh:0, t:[-0.39, 1.25, 0],   s:[0.18, 0.70, 0.22] },
  { name:'armR',  mesh:0, t:[ 0.39, 1.25, 0],   s:[0.18, 0.70, 0.22] },
  { name:'head',  mesh:1, t:[ 0.00, 1.86, 0],   s:[0.42, 0.42, 0.42] },
  { name:'nose',  mesh:1, t:[ 0.00, 1.82,-0.27],s:[0.12, 0.10, 0.12] }, // 正面(-Z)の目印
];

const gltf = {
  asset: { version:'2.0', generator:'voxel-world gen_dummy_player.mjs' },
  scene: 0,
  scenes: [{ nodes: parts.map((_,i)=>i) }],
  nodes: parts.map(p => ({ name:p.name, mesh:p.mesh, translation:p.t, scale:p.s })),
  meshes: [
    { name:'body', primitives:[{ attributes:{POSITION:0,NORMAL:1}, indices:2, material:0 }] },
    { name:'skin', primitives:[{ attributes:{POSITION:0,NORMAL:1}, indices:2, material:1 }] },
  ],
  materials: [
    { name:'body', doubleSided:true, pbrMetallicRoughness:{ baseColorFactor:[0.20,0.45,0.85,1], metallicFactor:0, roughnessFactor:0.9 } },
    { name:'skin', doubleSided:true, pbrMetallicRoughness:{ baseColorFactor:[0.95,0.78,0.62,1], metallicFactor:0, roughnessFactor:0.9 } },
  ],
  accessors: [
    { bufferView:0, componentType:5126, count:24, type:'VEC3', min:[-0.5,-0.5,-0.5], max:[0.5,0.5,0.5] }, // POSITION
    { bufferView:1, componentType:5126, count:24, type:'VEC3' }, // NORMAL
    { bufferView:2, componentType:5123, count:36, type:'SCALAR' }, // indices
  ],
  bufferViews: [
    { buffer:0, byteOffset:0,                 byteLength:POS_LEN, target:34962 },
    { buffer:0, byteOffset:POS_LEN,           byteLength:NRM_LEN, target:34962 },
    { buffer:0, byteOffset:POS_LEN+NRM_LEN,   byteLength:IDX_LEN, target:34963 },
  ],
  buffers: [{ byteLength: bin.length }],
};

// ---- GLB バイナリ組み立て ----
let jsonBuf = Buffer.from(JSON.stringify(gltf), 'utf8');
while (jsonBuf.length % 4 !== 0) jsonBuf = Buffer.concat([jsonBuf, Buffer.from(' ')]); // 空白で4バイト整列
let binBuf = bin;
while (binBuf.length % 4 !== 0) binBuf = Buffer.concat([binBuf, Buffer.from([0])]);

const totalLen = 12 + 8 + jsonBuf.length + 8 + binBuf.length;
const header = Buffer.alloc(12);
header.writeUInt32LE(0x46546C67, 0); // 'glTF'
header.writeUInt32LE(2, 4);
header.writeUInt32LE(totalLen, 8);
const jsonHead = Buffer.alloc(8);
jsonHead.writeUInt32LE(jsonBuf.length, 0);
jsonHead.writeUInt32LE(0x4E4F534A, 4); // 'JSON'
const binHead = Buffer.alloc(8);
binHead.writeUInt32LE(binBuf.length, 0);
binHead.writeUInt32LE(0x004E4942, 4); // 'BIN\0'
const glb = Buffer.concat([header, jsonHead, jsonBuf, binHead, binBuf]);

fs.mkdirSync(path.dirname(OUT), { recursive: true });
fs.writeFileSync(OUT, glb);

// ---- 自己検証（構造の正しさを再パースで確認）----
const r = fs.readFileSync(OUT);
const magic = r.readUInt32LE(0), ver = r.readUInt32LE(4), tlen = r.readUInt32LE(8);
const jlen = r.readUInt32LE(12), jtype = r.readUInt32LE(16);
const jstr = r.slice(20, 20+jlen).toString('utf8');
const parsed = JSON.parse(jstr); // 失敗すれば例外で落ちる
const blen = r.readUInt32LE(20+jlen), btype = r.readUInt32LE(24+jlen);
const ok =
  magic === 0x46546C67 && ver === 2 && tlen === r.length &&
  jtype === 0x4E4F534A && btype === 0x004E4942 &&
  blen === binBuf.length && parsed.meshes.length === 2;

console.log(`生成: ${OUT}`);
console.log(`サイズ: ${glb.length} bytes / JSONチャンク: ${jlen} / BINチャンク: ${blen}`);
console.log(`ノード数: ${parsed.nodes.length}（身長 約2.07m / 原点=足元中心 / 正面 -Z）`);
console.log(`構造検証: ${ok ? 'OK ✅' : 'NG ❌'}`);
if (!ok) process.exit(1);
