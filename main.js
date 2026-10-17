const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const fs = require('fs');
const path = require('path');
const os = require('os');

const dataFile = () => path.join(app.getPath('userData'), 'leads.json');
const backupDir = () => path.join(app.getPath('userData'), 'backups');

function createWindow() {
  const win = new BrowserWindow({
    width: 1360, height: 860, minWidth: 980, minHeight: 600,
    title: 'Лиды конфигуратора', backgroundColor: '#F2F4F3', autoHideMenuBar: true,
    webPreferences: { preload: path.join(__dirname, 'preload.js'), contextIsolation: true, nodeIntegration: false }
  });
  win.loadFile('index.html');
  win.webContents.setWindowOpenHandler(({ url }) => { shell.openExternal(url); return { action: 'deny' }; });
}

ipcMain.handle('load', () => { try { return JSON.parse(fs.readFileSync(dataFile(), 'utf8')); } catch (e) { return null; } });
ipcMain.handle('save', (e, data) => {
  const f = dataFile(); fs.mkdirSync(path.dirname(f), { recursive: true });
  fs.writeFileSync(f + '.tmp', JSON.stringify(data, null, 1)); fs.renameSync(f + '.tmp', f);
  // one backup per day, last 30 kept
  fs.mkdirSync(backupDir(), { recursive: true });
  const bf = path.join(backupDir(), 'leads-' + new Date().toISOString().slice(0, 10) + '.json');
  if (!fs.existsSync(bf)) fs.copyFileSync(f, bf);
  const old = fs.readdirSync(backupDir()).filter(n => n.endsWith('.json')).sort().slice(0, -30);
  old.forEach(n => { try { fs.unlinkSync(path.join(backupDir(), n)); } catch (_) {} });
  return true;
});
ipcMain.handle('openExternal', (e, url) => { if (/^https?:\/\//.test(url)) shell.openExternal(url); });
ipcMain.handle('openDataFolder', () => shell.openPath(app.getPath('userData')));
ipcMain.handle('exportJson', async (e, data) => {
  const { filePath } = await dialog.showSaveDialog({ defaultPath: 'лиды-' + new Date().toISOString().slice(0, 10) + '.json', filters: [{ name: 'JSON', extensions: ['json'] }] });
  if (!filePath) return null; fs.writeFileSync(filePath, JSON.stringify(data, null, 1)); return filePath;
});
ipcMain.handle('importJson', async () => {
  const { filePaths } = await dialog.showOpenDialog({ properties: ['openFile'], filters: [{ name: 'JSON', extensions: ['json'] }] });
  if (!filePaths || !filePaths[0]) return null; return JSON.parse(fs.readFileSync(filePaths[0], 'utf8'));
});
async function htmlToPdf(html) {
  const tmp = path.join(os.tmpdir(), 'kp-' + Date.now() + '.html'); fs.writeFileSync(tmp, html);
  const w = new BrowserWindow({ show: false }); await w.loadFile(tmp);
  const pdf = await w.webContents.printToPDF({ pageSize: 'A4', printBackground: true, margins: { top: 0.6, bottom: 0.6, left: 0.7, right: 0.7 } });
  w.destroy(); try { fs.unlinkSync(tmp); } catch (_) {} return pdf;
}
ipcMain.handle('exportKp', async (e, { html, name, kind }) => {
  const ext = kind === 'pdf' ? 'pdf' : 'doc';
  const { filePath } = await dialog.showSaveDialog({ defaultPath: name + '.' + ext, filters: [{ name: kind === 'pdf' ? 'PDF' : 'Word', extensions: [ext] }] });
  if (!filePath) return null;
  if (kind === 'pdf') fs.writeFileSync(filePath, await htmlToPdf(html));
  else fs.writeFileSync(filePath, '﻿' + html);   // Word opens HTML saved as .doc
  shell.showItemInFolder(filePath); return filePath;
});


/* ---------- AI and web helpers ---------- */
const https = require('https');
const crypto = require('crypto');
// Sber's GigaChat endpoints use the Russian national root CA, which Node does not ship with; skip verification only for those hosts
const SBER = /(^|\.)(sberbank\.ru|giga\.chat)$/;
function request(url, { method = 'GET', headers = {}, body = null, timeout = 60000 } = {}) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const req = https.request({ method, hostname: u.hostname, port: u.port || 443, path: u.pathname + u.search, headers,
      rejectUnauthorized: !SBER.test(u.hostname), timeout }, res => {
      const chunks = []; res.on('data', c => chunks.push(c));
      res.on('end', () => resolve({ status: res.statusCode, headers: res.headers, text: Buffer.concat(chunks).toString('utf8') }));
    });
    req.on('timeout', () => req.destroy(new Error('Нет ответа от сервера')));
    req.on('error', reject); if (body) req.write(body); req.end();
  });
}
async function getFollow(url, n = 4) {
  let r = await request(url, { headers: { 'User-Agent': 'Mozilla/5.0 LeadDesk', 'Accept-Language': 'ru' }, timeout: 20000 });
  while (n-- > 0 && r.status >= 300 && r.status < 400 && r.headers.location) { url = new URL(r.headers.location, url).href; r = await request(url, { headers: { 'User-Agent': 'Mozilla/5.0 LeadDesk' }, timeout: 20000 }); }
  return r;
}
ipcMain.handle('fetchSite', async (e, url) => {
  try {
    const r = await getFollow(url); if (r.status >= 400) return { error: 'Сайт ответил ошибкой ' + r.status };
    const t = r.text.replace(/<script[\s\S]*?<\/script>|<style[\s\S]*?<\/style>|<noscript[\s\S]*?<\/noscript>/gi, ' ')
      .replace(/<(br|p|div|li|h\d|tr)[^>]*>/gi, '\n').replace(/<[^>]+>/g, ' ').replace(/&nbsp;/g, ' ').replace(/&quot;/g, '"').replace(/&amp;/g, '&')
      .replace(/[ \t]+/g, ' ').replace(/\n\s*\n+/g, '\n').trim();
    const title = (r.text.match(/<title[^>]*>([^<]*)/i) || [])[1] || '';
    const desc = (r.text.match(/<meta[^>]+name=["']description["'][^>]+content=["']([^"']*)/i) || [])[1] || '';
    return { text: [title, desc, t].filter(Boolean).join('\n').slice(0, 7000) };
  } catch (err) { return { error: 'Не удалось открыть сайт: ' + err.message }; }
});
let gigaToken = { v: '', exp: 0 };
async function gigaAuth(cfg) {
  if (gigaToken.v && Date.now() < gigaToken.exp - 60000) return gigaToken.v;
  const r = await request('https://ngw.devices.sberbank.ru:9443/api/v2/oauth', { method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json', 'RqUID': crypto.randomUUID(), 'Authorization': 'Basic ' + cfg.gigaKey.trim() },
    body: 'scope=' + encodeURIComponent(cfg.gigaScope || 'GIGACHAT_API_PERS') });
  if (r.status !== 200) throw new Error('GigaChat не принял ключ (' + r.status + '): ' + r.text.slice(0, 200));
  const j = JSON.parse(r.text); gigaToken = { v: j.access_token, exp: j.expires_at || Date.now() + 25 * 60000 }; return gigaToken.v;
}
ipcMain.handle('aiGenerate', async (e, { cfg, system, user }) => {
  try {
    const messages = [{ role: 'system', content: system }, { role: 'user', content: user }];
    let r;
    if (cfg.aiProvider === 'giga') {
      if (!cfg.gigaKey) return { error: 'Не указан ключ авторизации GigaChat' };
      const tok = await gigaAuth(cfg);
      const base = (cfg.gigaBase || 'https://gigachat.devices.sberbank.ru/api/v1').replace(/\/$/, '');
      r = await request(base + '/chat/completions', { method: 'POST', headers: { 'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': 'Bearer ' + tok },
        body: JSON.stringify({ model: cfg.gigaModel || 'GigaChat-2-Max', messages, temperature: 0.6, max_tokens: 2000 }) });
      if (r.status === 401) { gigaToken = { v: '', exp: 0 }; }
    } else {
      if (!cfg.ycKey || !cfg.ycFolder) return { error: 'Не указаны API-ключ или ID каталога Yandex Cloud' };
      r = await request('https://ai.api.cloud.yandex.net/v1/chat/completions', { method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': 'Api-Key ' + cfg.ycKey.trim(), 'OpenAI-Project': cfg.ycFolder.trim() },
        body: JSON.stringify({ model: 'gpt://' + cfg.ycFolder.trim() + '/' + (cfg.ycModel || 'yandexgpt/latest'), messages, temperature: 0.6, max_tokens: 2000 }) });
    }
    if (r.status !== 200) return { error: 'Сервис ответил ' + r.status + ': ' + r.text.slice(0, 300) };
    const j = JSON.parse(r.text); const text = j.choices && j.choices[0] && j.choices[0].message && j.choices[0].message.content;
    return text ? { text: text.trim() } : { error: 'Пустой ответ: ' + r.text.slice(0, 200) };
  } catch (err) { return { error: err.message }; }
});

app.whenReady().then(createWindow);
app.on('window-all-closed', () => app.quit());
