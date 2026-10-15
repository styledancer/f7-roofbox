// Renders the app in headless Chrome and saves phone-sized screenshots for visual review.
import { chromium } from 'playwright-core';
const url = process.argv[2] || 'http://127.0.0.1:8080/index.html';
const out = process.argv[3] || 'shots';
const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 412, height: 860 }, deviceScaleFactor: 2, reducedMotion: 'reduce' });
const logs = [];
page.on('console', m => logs.push(m.type() + ': ' + m.text()));
page.on('pageerror', e => logs.push('PAGEERROR: ' + e.message));
await page.goto(url);
await page.waitForTimeout(9000);
const shot = async (n) => { await page.waitForTimeout(2500); await page.screenshot({ path: `${out}/${n}.png` }); };
const click = (sel) => page.evaluate(s => document.querySelector(s)?.click(), sel);
const view = (v) => click(`.views button[data-view="${v}"]`);
await shot('1-q');
await view('side'); await shot('2-side');
await page.evaluate(() => { const b=document.querySelector('#lidSw [data-lid="1"]'); b&&b.click(); }); await view('q'); await shot('3-lid-person');
await page.evaluate(() => { const b=document.querySelector('#lidSw [data-lid="0"]'); b&&b.click(); });
await click('#offBtn'); await page.waitForTimeout(4000); await shot('4-offroad');
await click('#offBtn'); await click('#hwBtn'); await page.waitForTimeout(3000); await shot('5-highway');
await click('#hwBtn');
// close-up of the front wheel and headlight
await page.evaluate(() => { const c = window.__cam; });
await page.mouse.move(206, 400); for (let i = 0; i < 6; i++) { await page.mouse.wheel(0, -300); await page.waitForTimeout(150); }
await shot('6-close');
await page.evaluate(() => { document.querySelector('#snapGo')?.click(); }); await page.waitForTimeout(3000);
await page.screenshot({ path: `${out}/7-snap-preview.png` });
require_fs: {
  const fs = await import('fs'); fs.writeFileSync(`${out}/console.txt`, logs.join('\n'));
}
await browser.close();
