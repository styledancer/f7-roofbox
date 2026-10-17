const { contextBridge, ipcRenderer } = require('electron');
contextBridge.exposeInMainWorld('desk', {
  load: () => ipcRenderer.invoke('load'),
  save: d => ipcRenderer.invoke('save', d),
  openExternal: u => ipcRenderer.invoke('openExternal', u),
  openDataFolder: () => ipcRenderer.invoke('openDataFolder'),
  exportJson: d => ipcRenderer.invoke('exportJson', d),
  importJson: () => ipcRenderer.invoke('importJson'),
  exportKp: o => ipcRenderer.invoke('exportKp', o),
  fetchSite: u => ipcRenderer.invoke('fetchSite', u),
  aiGenerate: o => ipcRenderer.invoke('aiGenerate', o)
});
