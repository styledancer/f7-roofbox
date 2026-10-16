// Renders the app in headless Chrome and saves phone-sized screenshots for visual review (rack + packing check).
import { chromium } from 'playwright-core';
import fs from 'fs';
const url = process.argv[2] || 'http://127.0.0.1:8080/index.html';
const out = process.argv[3] || 'shots';
const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 412, height: 860 }, deviceScaleFactor: 2, reducedMotion: 'reduce' });
const logs = [];
page.on('console', m => logs.push(m.type() + ': ' + m.text()));
page.on('pageerror', e => logs.push('PAGEERROR: ' + e.message));
const shot = async (n) => { await page.waitForTimeout(2500); await page.screenshot({ path: `${out}/${n}.png` }); };
const click = (sel) => page.evaluate(s => document.querySelector(s)?.click(), sel);
const view = (v) => click(`.views button[data-view="${v}"]`);
const zoom = async (n) => { await page.mouse.move(206, 330); for (let i = 0; i < n; i++) { await page.mouse.wheel(0, -300); await page.waitForTimeout(120); } };
const setup = async (o) => { await page.evaluate((o) => { localStorage.clear(); for (const k in o) localStorage.setItem('f7box.' + k, JSON.stringify(o[k])); }, o); await page.reload(); await page.waitForTimeout(10000); };
await page.goto(url); await page.waitForTimeout(3000);
await setup({ wxMode: 'off', sel: 'm3-l', items: [] });
await shot('1-rack-q'); await view('side'); await shot('2-rack-side'); await zoom(5); await shot('3-rack-side-close');
await setup({ wxMode: 'off', sel: 'm3-l', items: [], bike: false });
await page.evaluate(() => document.querySelector('#laySw [data-lay="bike"]').click()); await view('rear'); await shot('4-bike-rear'); await view('q'); await shot('5-bike-q');
await view('top'); await shot('6-bike-top');
await setup({ wxMode: 'off', sel: 'm3-xll', items: ['cooler', 'boots', 'suitM', 'duffel', 'tent', 'sleep', 'yoyo'] });
await click('#wireBtn'); await view('side'); await shot('7-pack-xll-side'); await view('q'); await shot('8-pack-xll-q'); await view('rear'); await shot('9-pack-xll-rear');
await setup({ wxMode: 'off', sel: 'm3-l', items: [] });
await page.evaluate(() => document.querySelectorAll('.boxui')[0].click()); await page.waitForTimeout(500);
for (let i = 0; i < 3; i++) { await page.evaluate(() => document.querySelector('.itemsDrop [data-auto]')?.click()); await page.waitForTimeout(800); await page.screenshot({ path: `${out}/1${i}-autofill.png` }); }
await click('#wireBtn'); await view('side'); await shot('13-autofill-side');
fs.writeFileSync(`${out}/console.txt`, logs.join('\n'));
await browser.close();
