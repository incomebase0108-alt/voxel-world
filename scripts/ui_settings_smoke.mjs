// コアが ui.js の UI_SETTINGS（画質）を読むかのスモークテスト（4号機・2026-10-16）
// 本物の index.html を http で開き、画面の倍率2の端末で:
//   ① 起動してページの例外が0  ② 既定(high)は canvas が CSS 幅の2倍  ③ quality='low'＋uisettingschange で1倍に下がる
//   ④ 'high' に戻すと2倍に戻る
// 使い方: node scripts/ui_settings_smoke.mjs   （three は CDN から読むのでネットが要る）
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';
import { globSync } from 'node:fs';

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const require = createRequire(import.meta.url);
let chromium;
// 探索先を機体に依らず広げる（3号機の scripts/ui_smoke.mjs と同じ npx キャッシュ経路を追加）。
// 固定パスだけだと、playwright をそこに持っていない機では exit 2 になる。
const home = (process.env.USERPROFILE || process.env.HOME || '').split(path.sep).join('/');
const candidates = ['playwright', 'playwright-core'];
for (const pat of ['/AppData/Local/npm-cache/_npx/*/node_modules/playwright/index.js',
                   '/AppData/Local/npm-cache/_npx/*/node_modules/playwright-core/index.js']) {
  if (home) candidates.push(...globSync(home + pat));
}
candidates.push('C:/Users/soraj/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
for (const p of candidates) {
  try { const m = require(p); chromium = m.chromium || (m.default && m.default.chromium); if (chromium) break; } catch (e) {}
}
if (!chromium) { console.error('playwright が見つからない'); process.exit(2); }
// Edge が無い機でも システム Chrome → 同梱 chromium の順で落とす
const BROWSERS = ['C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
                  'C:/Program Files/Google/Chrome/Application/chrome.exe',
                  'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe'];
const EXE = BROWSERS.find(b => fs.existsSync(b));
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.glb': 'model/gltf-binary', '.json': 'application/json', '.png': 'image/png', '.ogg': 'audio/ogg', '.mp3': 'audio/mpeg', '.wav': 'audio/wav' };
const srv = http.createServer((q, r) => {
  const u = decodeURIComponent(q.url.split('?')[0]);
  const f = path.join(root, u === '/' ? 'index.html' : u);
  if (!f.startsWith(root) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { r.writeHead(404); r.end(); return; }
  r.writeHead(200, { 'content-type': TYPES[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(r);
});
await new Promise(ok => srv.listen(0, '127.0.0.1', ok));
const url = 'http://127.0.0.1:' + srv.address().port + '/';
let ok = true; const A = (c, l) => { console.log((c ? 'OK   ' : 'FAIL ') + l); if (!c) ok = false; };
const br = await chromium.launch({ executablePath: EXE, headless: true, args: ['--enable-unsafe-swiftshader', '--use-angle=swiftshader'] });
try {
  const ctx = await br.newContext({ viewport: { width: 800, height: 500 }, deviceScaleFactor: 2 });
  const pg = await ctx.newPage(); const errs = [];
  pg.on('pageerror', e => errs.push(String(e && e.message || e)));
  await pg.goto(url, { waitUntil: 'load', timeout: 90000 });
  await pg.waitForFunction(() => { const c = document.getElementById('c'); return c && c.width > 0; }, null, { timeout: 90000 });
  await pg.waitForTimeout(1500);
  const w = () => pg.evaluate(() => ({ cw: document.getElementById('c').width, css: document.getElementById('c').clientWidth || innerWidth }));
  const w0 = await w();
  A(w0.cw === w0.css * 2, '② 既定(high)は canvas が CSS 幅の2倍 (canvas ' + w0.cw + ' / CSS ' + w0.css + ')');
  await pg.evaluate(() => { window.UI_SETTINGS = Object.assign({}, window.UI_SETTINGS || {}, { quality: 'low' }); window.dispatchEvent(new CustomEvent('uisettingschange', { detail: window.UI_SETTINGS })); });
  await pg.waitForTimeout(300);
  const w1 = await w();
  A(w1.cw === w1.css, '③ low で canvas が1倍に下がる (canvas ' + w1.cw + ' / CSS ' + w1.css + ')');
  await pg.evaluate(() => { window.UI_SETTINGS.quality = 'high'; window.dispatchEvent(new CustomEvent('uisettingschange', { detail: window.UI_SETTINGS })); });
  await pg.waitForTimeout(300);
  const w2 = await w();
  A(w2.cw === w2.css * 2, '④ high に戻すと2倍に戻る (canvas ' + w2.cw + ')');
  A(errs.length === 0, '① ページの例外 0 (' + errs.length + (errs.length ? '・' + errs.slice(0, 2).join(' / ') : '') + ')');
} finally { await br.close(); srv.close(); }
console.log(ok ? 'ぜんぶ OK' : '★ 落ちた項目がある'); process.exit(ok ? 0 : 1);
