const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process
// to use Electron APIs without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  platform: process.platform,
  versions: {
    node: process.versions.node,
    chrome: process.versions.chrome,
    electron: process.versions.electron
  },
  
  // Listen for backend logs (optional, for debugging)
  onBackendLog: (callback) => {
    ipcRenderer.on('backend-log', (event, message) => callback(message));
  },
  
  onBackendError: (callback) => {
    ipcRenderer.on('backend-error', (event, message) => callback(message));
  },
  
  // Remove listeners
  removeAllListeners: (channel) => {
    ipcRenderer.removeAllListeners(channel);
  }
});

