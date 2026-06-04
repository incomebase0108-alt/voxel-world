// ui.js 単体スモークテスト（Three.js/WebGL を避け、ui.js だけを実ブラウザで検証）
// 検証: 構文/起動エラー無し / 仲間パネル休止→点灯 / commandCompanion 呼出 / 加入・離脱トースト / タッチ要素存在
import { readFileSync, globSync } from 'fs';
import { pathToFileURL } from 'url';
const pwGlob = globSync(process.env.USERPROFILE + '/AppData/Local/npm-cache/_npx/*/node_modules/playwright-core/index.js');
const pw = await import(pathToFileURL(pwGlob[0]).href);
const chromium = (pw.chromium || (pw.default && pw.default.chromium));
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const uiSrc = readFileSync(join(root, 'ui.js'), 'utf8');

const html = `<!doctype html><html><head><meta charset=utf8></head><body>
<canvas id="overlay" style="display:none"></canvas>
<script>
  window.__cmds = [];
  // 最小モック: state() は window.__companions を返すだけ
  window.__companions = undefined;
  window.VoxelGame = {
    state: () => ({ hp:20, maxHp:20, hunger:20, maxHunger:20, breath:10, maxBreath:10,
      hotbar:[], items:[], recipes:[], time:{hh:12,mm:0,phase:'昼'}, weather:'晴', biome:'平原',
      pos:{x:0,y:64,z:0}, yaw:0, mobs:[], companions: window.__companions }),
    commandCompanion: (id, order) => { window.__cmds.push([id, order]); },
  };
</script>
<script>${uiSrc}</script>
</body></html>`;

const errors = [];
// Playwright同梱ブラウザが版ずれする環境向け: システムChrome優先、無ければ channel:'chrome'、最後に既定。
import { existsSync } from 'fs';
const sysChrome = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const launchOpts = existsSync(sysChrome) ? { executablePath: sysChrome } : { channel: 'chrome' };
let browser;
try { browser = await chromium.launch(launchOpts); }
catch (e) { browser = await chromium.launch(); }
const page = await browser.newPage();
page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
page.on('pageerror', e => errors.push('PAGEERROR: ' + e.message));
await page.setContent(html, { waitUntil: 'load' });
await page.waitForTimeout(150); // tick が回るのを待つ

const results = {};
const $ = (sel) => page.$eval(sel, e => ({ display: getComputedStyle(e).display, on: e.classList.contains('on') })).catch(() => null);

// 1) 休止: companions 無し → パネル非表示
results.dormant = await $('#ui-companions');

// 2) 点灯: 仲間2人を注入（1号機の実フォーマット= mode/type を使い、別名経路を検証）
await page.evaluate(() => { window.__companions = [
  { id:'w', name:'相棒ウル', hp:18, maxHp:20, type:'guard',   mode:'follow' },
  { id:'g', name:'パン屋',   hp:5,  maxHp:30, type:'baker',   mode:'attack' },
]; });
await page.waitForTimeout(120);
results.lit = await $('#ui-companions');
results.cardCount = await page.$$eval('#ui-companions .ui-comp', els => els.filter(e => e.style.display !== 'none').length);
results.name0 = await page.$eval('#ui-companions .ui-comp .ui-comp-name', e => e.textContent).catch(() => null);
results.joinToasts = await page.$$eval('#ui-toast-wrap .ui-toast', els => els.length);
// アクティブ指示ボタン（1人目=follow が点灯しているか）
results.activeOrder0 = await page.$eval('#ui-companions .ui-comp .ui-comp-cmd.on .cg', e => e.parentElement.textContent).catch(() => null);

// 3) 指示ボタン押下 → commandCompanion 呼出（1人目の3番目=攻撃をクリック）
await page.$$eval('#ui-companions .ui-comp:first-child .ui-comp-cmd', els => els[2].click());
results.cmds = await page.evaluate(() => window.__cmds);

// 4) 離脱: 1人消す → 離脱トースト & カード1枚
await page.evaluate(() => { window.__companions = [ window.__companions ? null : null ] && [
  { id:'w', name:'相棒ウル', hp:18, maxHp:20, glyph:'🐺', order:'wait' } ]; });
await page.waitForTimeout(120);
results.cardCountAfterLeave = await page.$$eval('#ui-companions .ui-comp', els => els.filter(e => e.style.display !== 'none').length);

// 5) タッチUI 要素の存在（CSS で display:none だが DOM はある）
results.touch = await page.$$eval('#ui-stick, #ui-look, .ui-tbtn.attack, .ui-tbtn.attack .chg', els => els.length);

await browser.close();
console.log('ERRORS:', JSON.stringify(errors));
console.log('RESULTS:', JSON.stringify(results, null, 2));
const ok = errors.length === 0
  && results.dormant && results.dormant.display === 'none'
  && results.lit && results.lit.on === true
  && results.cardCount === 2 && results.name0 === '相棒ウル'
  && results.joinToasts >= 2
  && results.cmds.length === 1 && results.cmds[0][0] === 'w' && results.cmds[0][1] === 'attack'
  && results.cardCountAfterLeave === 1
  && results.touch === 4;
console.log(ok ? 'SMOKE: PASS' : 'SMOKE: FAIL');
process.exit(ok ? 0 : 1);
