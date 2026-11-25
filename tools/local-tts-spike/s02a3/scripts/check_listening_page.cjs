// Reuse an existing Playwright module and Chrome; installs nothing.
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
let activeBrowser;

(async () => {
  const filename = path.resolve(process.argv[2]);
  const output = path.join(path.dirname(filename), 'output', 'playwright');
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({
    executablePath: process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: true,
  });
  activeBrowser = browser;
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, locale: 'zh-CN' });
  const page = await context.newPage();
  const externalRequests = [], errors = [];
  page.on('request', request => { if (/^https?:/.test(request.url())) externalRequests.push(request.url()); });
  page.on('pageerror', error => errors.push(error.message));
  await page.route(/^https?:/, route => route.abort());
  await page.goto(pathToFileURL(filename).href, { waitUntil: 'load' });
  const snapshot = await page.locator('h1,h2,h3,audio,button,select').evaluateAll(nodes => nodes.map(node => ({
    tag: node.tagName, name: node.textContent.trim(), src: node.getAttribute('src'),
  })));
  fs.writeFileSync(path.join(output, 'initial-ui.json'), JSON.stringify(snapshot, null, 2));
  await page.waitForFunction(() => document.querySelectorAll('audio').length === 10 &&
    [...document.querySelectorAll('audio')].every(a => a.readyState >= 1 && a.duration > 1 && !a.error));
  const initialScoresBlank = await page.locator('select,textarea').evaluateAll(nodes => nodes.every(n => n.value === ''));
  if (!initialScoresBlank) throw Error('Owner ratings must start empty');
  const audio = [];
  for (let i = 0; i < 10; i++) {
    await page.locator('audio').nth(i).evaluate(async element => { element.muted = true; await element.play(); });
    await page.waitForFunction(index => document.querySelectorAll('audio')[index].currentTime > .1, i);
    audio.push(await page.locator('audio').nth(i).evaluate(element => ({
      file: element.getAttribute('src'), duration: element.duration, currentTime: element.currentTime,
      paused: element.paused, readyState: element.readyState, mediaError: element.error,
    })));
  }
  const singlePlayer = await page.locator('audio').evaluateAll(nodes => nodes.filter(n => !n.paused).length === 1);
  await page.locator('audio').last().evaluate(element => element.pause());
  await page.screenshot({ path: path.join(output, 'desktop.png'), fullPage: false });
  await page.setViewportSize({ width: 375, height: 812 });
  await page.screenshot({ path: path.join(output, 'mobile.png'), fullPage: false });
  const mobileNoOverflow = await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth);
  const result = { state: 'PASS_PRIVATE_PAGE_REAL_BROWSER_DECODE_MUTED_PLAYBACK',
    browser: browser.version(), audio, initialScoresBlank, singlePlayer, mobileNoOverflow,
    externalRequests, errors, acousticPlayback: 'NOT_MEASURED_MUTED_BROWSER',
    sourceHtmlSha256: require('node:crypto').createHash('sha256').update(fs.readFileSync(filename)).digest('hex') };
  if (externalRequests.length || errors.length || !singlePlayer || !mobileNoOverflow) throw Error(JSON.stringify(result));
  fs.writeFileSync(path.join(output, 'validation.json'), JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result, null, 2));
  await browser.close();
})().catch(async error => { console.error(error); if (activeBrowser) await activeBrowser.close(); process.exitCode = 1; });
