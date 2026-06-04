// スマホ実機「動けない・地形→空色」の再現（モバイルエミュレーション）
import { globSync } from 'fs';
import { pathToFileURL } from 'url';
import { existsSync } from 'fs';
const g = globSync(process.env.USERPROFILE + '/AppData/Local/npm-cache/_npx/*/node_modules/playwright-core/index.js');
const pw = await import(pathToFileURL(g[0]).href); const chromium = pw.chromium || (pw.default && pw.default.chromium);
const sysChrome = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const browser = await chromium.launch(existsSync(sysChrome) ? { executablePath: sysChrome } : { channel: 'chrome' });

// iPhone風: タッチ・モバイルviewport
const ctx = await browser.newContext({
  viewport: { width: 390, height: 844 }, deviceScaleFactor: 3,
  isMobile: true, hasTouch: true,
  userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
});
// 実機スマホ相当: Pointer Lock API を無効化（desktop Chrome エミュは常にロック対応のため明示的に殺す）
await ctx.addInitScript(() => {
  try { Object.defineProperty(Element.prototype, 'requestPointerLock', { value: function () { return undefined; }, configurable: true }); } catch (e) {}
  try { Object.defineProperty(Document.prototype, 'exitPointerLock', { value: function () {}, configurable: true }); } catch (e) {}
  try { Object.defineProperty(Document.prototype, 'pointerLockElement', { get: () => null, configurable: true }); } catch (e) {}
});
const page = await ctx.newPage();
const errs = [];
page.on('pageerror', e => errs.push('PAGEERROR: ' + e.message));
page.on('console', m => { if (m.type() === 'error') errs.push('CONSOLE.ERR: ' + m.text()); });

const target = process.argv[2] || 'index.html';
await page.goto(pathToFileURL(process.cwd() + '/' + target).href, { waitUntil: 'load', timeout: 30000 });
console.log('### TARGET:', target, '###');
await page.waitForTimeout(1500);

const probe = async (tag) => {
  const s = await page.evaluate(() => {
    const ov = document.getElementById('overlay');
    let st = null; try { st = window.VoxelGame && window.VoxelGame.state ? window.VoxelGame.state() : null; } catch (e) {}
    return {
      overlayDisplay: ov ? getComputedStyle(ov).display : '(no overlay)',
      pointerLocked: document.pointerLockElement ? document.pointerLockElement.id || 'el' : null,
      touchPoints: navigator.maxTouchPoints,
      uiTouch: window.UI_TOUCH,
      pos: st && st.pos ? { x:+st.pos.x.toFixed(2), y:+st.pos.y.toFixed(2), z:+st.pos.z.toFixed(2) } : null,
    };
  });
  console.log(tag, JSON.stringify(s));
  return s;
};

console.log('--- ロード直後（タイトル表示中）---');
const before = await probe('init ');

// タイトルの「はじめる」をタップ（overlay クリック＝requestLock 発火）
console.log('--- overlay を tap（はじめる）---');
await page.locator('#overlay').click({ position: { x: 195, y: 600 } }).catch(() => {});
await page.waitForTimeout(800);
const afterTapA = await probe('tap+0.8s ');
// 移動入力をシミュレート（ui.js の仮想スティックを上方向へドラッグ＝前進WASD合成）
await page.waitForTimeout(1500);
const afterTapB = await probe('tap+2.3s ');

// プレイヤーが動いたか（updatePlayer が走っているか）の判定
const moved = before.pos && afterTapB.pos &&
  (Math.abs(before.pos.x - afterTapB.pos.x) > 0.01 || Math.abs(before.pos.y - afterTapB.pos.y) > 0.01 || Math.abs(before.pos.z - afterTapB.pos.z) > 0.01);

await browser.close();
console.log('\n=== ERRORS (' + errs.length + ') ===');
console.log(errs.slice(0, 30).join('\n') || '(なし)');
console.log('\n=== 判定 ===');
console.log('overlay がタップ後も表示されたまま:', afterTapB.overlayDisplay !== 'none');
console.log('pointer lock 成立:', !!afterTapB.pointerLocked);
console.log('シミュ稼働(player.pos が変化/落下):', moved, '| init.y=', before.pos && before.pos.y, '→', afterTapB.pos && afterTapB.pos.y);
