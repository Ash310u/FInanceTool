const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

let mainWindow;
let backendProcess;
let frontendProcess;
const BACKEND_PORT = 5000;
const FRONTEND_PORT = 8000;

// Get paths based on environment
function getAppPath() {
  if (app.isPackaged) {
    // Production: use resourcesPath
    return path.join(process.resourcesPath, 'app');
  } else {
    // Development: use project root
    return path.join(__dirname, '..');
  }
}

// Get Python executable path
function getPythonExecutable() {
  const appPath = getAppPath();
  
  if (app.isPackaged) {
    // Production: bundled Python executable
    const bundledPython = path.join(process.resourcesPath, 'backend', 'financial-backend.exe');
    if (fs.existsSync(bundledPython)) {
      return bundledPython;
    }
    // Fallback: try system Python
    return 'python';
  } else {
    // Development: use venv Python
    const venvPython = process.platform === 'win32' 
      ? path.join(appPath, 'venv', 'Scripts', 'python.exe')
      : path.join(appPath, 'venv', 'bin', 'python');
    
    if (fs.existsSync(venvPython)) {
      return venvPython;
    }
    // Fallback: system Python
    return 'python';
  }
}

// Get backend script path
function getBackendScript() {
  const appPath = getAppPath();
  
  if (app.isPackaged) {
    // Production: use bundled executable
    return null; // Will use executable directly
  } else {
    // Development: use Python script
    return path.join(appPath, 'backend', 'app.py');
  }
}

// Start backend server
function startBackend() {
  const pythonExec = getPythonExecutable();
  const backendScript = getBackendScript();
  const appPath = getAppPath();
  
  console.log(`[Backend] Starting backend server...`);
  console.log(`[Backend] Python: ${pythonExec}`);
  
  if (app.isPackaged && !backendScript) {
    // Production: run bundled executable
    backendProcess = spawn(pythonExec, [], {
      cwd: path.join(process.resourcesPath, 'backend'),
      stdio: ['ignore', 'pipe', 'pipe'],
      env: {
        ...process.env,
        PORT: BACKEND_PORT.toString()
      }
    });
  } else {
    // Development: run Python script
    backendProcess = spawn(pythonExec, [backendScript], {
      cwd: path.join(appPath, 'backend'),
      stdio: ['ignore', 'pipe', 'pipe'],
      env: {
        ...process.env,
        PORT: BACKEND_PORT.toString(),
        DEBUG: 'False'
      }
    });
  }

  backendProcess.stdout.on('data', (data) => {
    const message = data.toString().trim();
    if (message) {
      console.log(`[Backend] ${message}`);
      // Send to renderer if needed
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('backend-log', message);
      }
    }
  });

  backendProcess.stderr.on('data', (data) => {
    const message = data.toString().trim();
    if (message && !message.includes('INFO')) {
      console.error(`[Backend Error] ${message}`);
    }
  });

  backendProcess.on('close', (code) => {
    console.log(`[Backend] Process exited with code ${code}`);
    if (code !== 0 && code !== null) {
      // Backend crashed, try to restart after delay
      setTimeout(() => {
        if (!app.isQuitting) {
          console.log('[Backend] Attempting to restart...');
          startBackend();
        }
      }, 3000);
    }
  });

  backendProcess.on('error', (error) => {
    console.error(`[Backend] Failed to start: ${error.message}`);
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('backend-error', error.message);
    }
  });
}

// Start frontend server (development only)
function startFrontend() {
  if (app.isPackaged) {
    // Production: frontend is served via file:// protocol, no server needed
    return;
  }

  const appPath = getAppPath();
  const pythonExec = getPythonExecutable();
  const frontendPath = path.join(appPath, 'frontend');
  
  console.log(`[Frontend] Starting frontend server...`);
  
  frontendProcess = spawn(pythonExec, ['-m', 'http.server', FRONTEND_PORT.toString()], {
    cwd: frontendPath,
    stdio: ['ignore', 'pipe', 'pipe']
  });

  frontendProcess.stdout.on('data', (data) => {
    console.log(`[Frontend] ${data.toString().trim()}`);
  });

  frontendProcess.stderr.on('data', (data) => {
    console.error(`[Frontend Error] ${data.toString().trim()}`);
  });

  frontendProcess.on('close', (code) => {
    console.log(`[Frontend] Process exited with code ${code}`);
  });
}

// Wait for backend to be ready
function waitForBackend(callback, maxAttempts = 30) {
  const http = require('http');
  let attempts = 0;

  const check = () => {
    const req = http.get(`http://127.0.0.1:${BACKEND_PORT}/api/health`, { timeout: 2000 }, (res) => {
      if (res.statusCode === 200) {
        console.log('[Backend] Health check passed');
        callback();
      } else {
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(check, 1000);
        } else {
          console.error('[Backend] Health check failed after max attempts');
          if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.webContents.send('backend-error', 'Backend failed to start');
          }
        }
      }
    });

    req.on('error', () => {
      attempts++;
      if (attempts < maxAttempts) {
        setTimeout(check, 1000);
      } else {
        console.error('[Backend] Health check failed after max attempts');
        if (mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.webContents.send('backend-error', 'Backend failed to start');
        }
      }
    });

    req.on('timeout', () => {
      req.destroy();
      attempts++;
      if (attempts < maxAttempts) {
        setTimeout(check, 1000);
      }
    });
  };

  check();
}

function createWindow() {
  const appPath = getAppPath();
  
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: true
    },
    icon: path.join(__dirname, '..', 'assets', 'icon.png'),
    show: false, // Don't show until ready
    titleBarStyle: 'default'
  });

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    if (process.env.NODE_ENV === 'development') {
      mainWindow.webContents.openDevTools();
    }
  });

  // Load frontend - will be set after backend is ready
  // For now, show loading screen or wait

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Start servers
  startBackend();
  
  // Wait for backend, then load frontend
  waitForBackend(() => {
    if (app.isPackaged) {
      // Production: load from bundled frontend files via file://
      const frontendPath = path.join(process.resourcesPath, 'frontend', 'index.html');
      if (fs.existsSync(frontendPath)) {
        console.log(`[Frontend] Loading from file: ${frontendPath}`);
        mainWindow.loadFile(frontendPath);
      } else {
        console.error('[Frontend] Frontend files not found in resources');
      }
    } else {
      // Development: start frontend server and load from URL
      startFrontend();
      setTimeout(() => {
        if (mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.loadURL(`http://127.0.0.1:${FRONTEND_PORT}`);
        }
      }, 1000);
    }
  });
}

// App event handlers
app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// Cleanup on quit
app.on('before-quit', (event) => {
  app.isQuitting = true;
  
  console.log('[App] Shutting down servers...');
  
  if (backendProcess) {
    console.log('[Backend] Terminating...');
    backendProcess.kill('SIGTERM');
    // Force kill after timeout
    setTimeout(() => {
      if (backendProcess && !backendProcess.killed) {
        backendProcess.kill('SIGKILL');
      }
    }, 3000);
  }
  
  if (frontendProcess) {
    console.log('[Frontend] Terminating...');
    frontendProcess.kill('SIGTERM');
    setTimeout(() => {
      if (frontendProcess && !frontendProcess.killed) {
        frontendProcess.kill('SIGKILL');
      }
    }, 2000);
  }
});

// Handle process termination
process.on('SIGTERM', () => {
  if (backendProcess) backendProcess.kill('SIGTERM');
  if (frontendProcess) frontendProcess.kill('SIGTERM');
  app.quit();
});

process.on('SIGINT', () => {
  if (backendProcess) backendProcess.kill('SIGTERM');
  if (frontendProcess) frontendProcess.kill('SIGTERM');
  app.quit();
});

