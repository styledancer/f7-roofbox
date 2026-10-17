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

app.whenReady().then(createWindow);
app.on('window-all-closed', () => app.quit());
