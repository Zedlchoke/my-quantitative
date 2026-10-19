'use strict';
// Bridge: renderer asks, main answers. No node in the page (contextIsolation).
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('paperdesk', {
  getState: cb => ipcRenderer.on('state', (_e, s) => cb(s)),
  setSection: s => ipcRenderer.invoke('section:set', s),
  startRunner: () => ipcRenderer.invoke('runner:start'),
  pauseRunner: (p, reason) => ipcRenderer.invoke('runner:pause', p, reason),
  stopRunner: () => ipcRenderer.invoke('runner:stop'),
  takeover: () => ipcRenderer.invoke('runner:takeover'),
  setPolicy: p => ipcRenderer.invoke('policy:set', p),
  aiSetMode: m => ipcRenderer.invoke('ai:setMode', m),
  aiRun: match => ipcRenderer.invoke('ai:run', match),
  aiRefresh: () => ipcRenderer.invoke('ai:refreshEntitlement'),
  pmProbe: () => ipcRenderer.invoke('pm:probe'),
  pmEvents: () => ipcRenderer.invoke('pm:events'),
});
