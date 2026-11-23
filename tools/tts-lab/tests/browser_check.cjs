// Optional local UI verification. Uses an existing Playwright/Chrome installation.
// No package installation, HTTP server, vendor access or generated Git artifacts.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

async function main() {
  const [dryDirectory, mockDirectory, outputDirectory] = process.argv.slice(2);
  const repository = path.resolve(__dirname, '../../..');
  const allowed = fs.realpathSync(path.join(repository, '.local-test-data/tts-auditions'));
  function checked(value) {
    assert(value, 'Pass dry-run, mock and verification output directories.');
    const resolved = fs.realpathSync(value);
    assert(resolved.startsWith(allowed + path.sep), 'UI artifacts must stay under ignored tts-auditions.');
    return resolved;
  }
  const dry = checked(dryDirectory), mock = checked(mockDirectory), output = checked(outputDirectory);
  const moduleName = process.env.PLAYWRIGHT_MODULE || 'playwright';
  const { chromium } = require(moduleName);
  const playwrightVersion = require(moduleName + '/package.json').version;
  const browser = await chromium.launch({
    executablePath: process.env.CHROME_EXECUTABLE || undefined, headless: true,
    args: ['--disable-background-networking', '--disable-component-update', '--disable-sync',
           '--disable-domain-reliability', '--no-first-run', '--autoplay-policy=no-user-gesture-required']
  });
  try {
    const context = await browser.newContext({ viewport: { width: 1280, height: 1000 } });
    await context.setOffline(true);
    const blocked = [], errors = [];
    await context.route('**/*', route => {
      if (route.request().url().startsWith('file:')) return route.continue();
      blocked.push(route.request().url()); return route.abort();
    });
    const page = await context.newPage();
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(pathToFileURL(path.join(dry, 'index.html')).href);
    await page.getByRole('heading', { name: '慢一点，听清楚。' }).waitFor();
    fs.writeFileSync(path.join(output, 'dry-accessibility.txt'), await page.locator('body').ariaSnapshot());
    assert.equal(await page.locator('audio').count(), 2);
    assert.equal(await page.locator('audio[src]').count(), 0);
    assert.equal(await page.locator('#candidate-a option').count(), 32);
    await page.getByLabel('选择原创片段').selectOption('names');
    assert((await page.locator('#text').textContent()).includes('𠮷'));
    assert(!/minimax|fish audio|elevenlabs|azure/i.test(await page.locator('body').innerText()));
    const viewports = [];
    for (const width of [1280, 390, 320]) {
      await page.setViewportSize({ width, height: width > 600 ? 1000 : 844 });
      const sizes = await page.evaluate(() => ({ content: document.documentElement.scrollWidth, viewport: innerWidth }));
      assert(sizes.content <= sizes.viewport + 1, `Horizontal overflow at ${width}px`);
      await page.screenshot({ path: path.join(output, `dry-${width}.png`), fullPage: true });
      viewports.push({ width, horizontalOverflow: false });
    }
    await page.setViewportSize({ width: 1280, height: 1000 });
    await page.goto(pathToFileURL(path.join(mock, 'index.html')).href);
    await page.getByText('这些是相同的 0.16 秒测试音，不含语音，不能用来评价供应商。').waitFor();
    const visible = JSON.parse(await page.locator('#audition-data').textContent());
    const available = visible.tracks.filter(t => t.case === visible.samples[0].id && t.audio).map(t => t.alias);
    assert(available.length >= 2);
    await page.locator('#candidate-a').selectOption(available[0]);
    await page.locator('#candidate-b').selectOption(available[1]);
    await page.locator('#audio-a').evaluate(audio => { audio.loop = true; return audio.play(); });
    await page.waitForFunction(() => !document.getElementById('audio-a').paused);
    await page.locator('#audio-b').evaluate(audio => { audio.loop = true; return audio.play(); });
    await page.waitForFunction(() => document.getElementById('audio-a').paused && !document.getElementById('audio-b').paused);
    const duration = await page.locator('#audio-b').evaluate(audio => audio.duration);
    assert(Math.abs(duration - 0.32) < 0.001); // First case has two shared chunks, two 0.16 s mock tones.
    await page.getByRole('button', { name: '暂停全部播放' }).click();
    assert(await page.locator('#audio-b').evaluate(audio => audio.paused));
    await page.locator('#candidate-b').selectOption(available[0]);
    assert.notEqual(await page.locator('#candidate-a').inputValue(), await page.locator('#candidate-b').inputValue());
    await page.screenshot({ path: path.join(output, 'mock-player.png'), fullPage: true });
    assert.deepEqual(errors, []); assert.deepEqual(blocked, []);
    const result = { result: 'PASS', node: process.version, playwright: playwrightVersion,
      chrome: browser.version(), realVendorRequests: 0, pageErrors: errors, httpRequests: blocked.length,
      viewports, blindMappingVisible: false, mockPlaybackAndExclusiveAB: true,
      audioProvenance: 'identical test tones only; no vendor speech or human scores', mockJoinedDurationSeconds: duration };
    fs.writeFileSync(path.join(output, 'browser-results.json'), JSON.stringify(result, null, 2) + '\n');
    console.log(JSON.stringify(result));
  } finally { await browser.close(); }
}
main().catch(error => { console.error(error.message); process.exitCode = 1; });
