# Windows Deployment Guide

## Ports Used

When you build and run the Electron app on Windows, here's what runs where:

### Backend Server
- **Port:** `5000`
- **URL:** `http://127.0.0.1:5000`
- **What it does:** Flask API server that processes Excel files
- **Runs:** Automatically when Electron app starts
- **Location:** Bundled Python executable runs in background

### Frontend
- **Port:** `8000` (development only)
- **Production:** Loaded via `file://` protocol (no server needed)
- **What it does:** Web UI that users interact with
- **Runs:** Inside Electron window (no separate server in production)

## Installation Location

When users install the app on Windows:

### Default Installation Path
```
C:\Users\<Username>\AppData\Local\Programs\financial-reporting-tool\
```

Or if user chooses custom location:
```
C:\Program Files\Financial Reporting Tool\
```

### Where Files Are Located

```
Installation Directory/
├── Financial Reporting Tool.exe          # Main executable (launch this)
├── resources/
│   ├── app/
│   │   ├── electron/
│   │   │   ├── main.js                   # Electron main process
│   │   │   └── preload.js
│   │   ├── frontend/
│   │   │   ├── index.html
│   │   │   ├── css/
│   │   │   └── js/
│   │   └── package.json
│   └── backend/
│       └── financial-backend.exe          # Bundled Python backend
└── ... (other Electron files)
```

## How It Works

1. **User launches:** `Financial Reporting Tool.exe`
2. **Electron starts:** Creates window and loads `main.js`
3. **Backend launches:** `main.js` starts `financial-backend.exe` from `resources/backend/`
4. **Backend runs:** Flask server starts on `http://127.0.0.1:5000`
5. **Frontend loads:** Electron window loads `frontend/index.html` via `file://` protocol
6. **Frontend connects:** JavaScript in frontend makes API calls to `http://127.0.0.1:5000/api`

## Network Behavior

- ✅ **All traffic is local** - `127.0.0.1` (localhost only)
- ✅ **No external connections** - Everything runs on user's machine
- ✅ **No firewall issues** - Localhost doesn't require firewall rules
- ✅ **No port conflicts** - If port 5000 is busy, app will fail to start (you can change this)

## Changing Ports (If Needed)

If port 5000 is already in use, edit `electron/main.js`:

```javascript
const BACKEND_PORT = 5000;  // Change to 5001, 5002, etc.
```

Then also update `frontend/js/app.js`:

```javascript
const API_BASE_URL = 'http://127.0.0.1:5000/api';  // Match the port above
```

Rebuild the app after changes.

## Process Details

When the app is running, you'll see:

1. **Electron process:** `Financial Reporting Tool.exe` (main window)
2. **Python backend:** `financial-backend.exe` (background, no window)
3. **No frontend server:** Frontend is loaded directly from files

## Troubleshooting

### Port 5000 Already in Use
**Error:** Backend fails to start

**Solution:**
1. Close other apps using port 5000
2. Or change the port in `electron/main.js` and `frontend/js/app.js`
3. Rebuild the app

### Can't Find Backend
**Error:** "Backend failed to start"

**Check:**
- `resources/backend/financial-backend.exe` exists
- Antivirus isn't blocking it
- Windows Defender allows the app

### App Won't Start
**Check:**
- Installation completed successfully
- No error messages in Windows Event Viewer
- Try running as administrator (though shouldn't be needed)

## Summary

| Component | Port | Protocol | Location |
|-----------|------|----------|----------|
| Backend API | 5000 | HTTP | `127.0.0.1:5000` |
| Frontend (dev) | 8000 | HTTP | `127.0.0.1:8000` |
| Frontend (prod) | N/A | file:// | Local files |
| Electron | N/A | N/A | Desktop window |

**Everything runs locally on the user's machine - no internet required!**

