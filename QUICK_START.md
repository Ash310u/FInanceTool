# Quick Start Guide

## For Development (You have Python installed)

### Option 1: Using Shell Scripts (Linux/Mac/WSL)
```bash
./start.sh
```

### Option 2: Using Electron in Dev Mode
```bash
npm install          # First time only
npm run dev          # Starts Python backend + Electron
```

### Option 3: Manual Start
```bash
# Terminal 1: Backend
cd backend
python app.py

# Terminal 2: Frontend
cd frontend
python -m http.server 8000

# Terminal 3: Electron (optional)
npm start
```

## For End Users (No Python Required)

### Building the Standalone App

1. **Install dependencies:**
   ```bash
   npm install
   pip install pyinstaller
   ```

2. **Build the app:**
   ```bash
   npm run build:win
   ```

3. **Find the installer:**
   - Location: `dist/Financial Reporting Tool Setup x.x.x.exe`
   - Size: ~150-200MB

### Installing for End Users

1. **Download** the installer
2. **Run** the installer (double-click)
3. **Launch** from Start Menu
4. **Done!** - No Python, no dependencies needed

## Troubleshooting

### "npm: command not found"
Install Node.js from [nodejs.org](https://nodejs.org/)

### "PyInstaller not found"
```bash
pip install pyinstaller
```

### Build fails with missing modules
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install all dependencies
pip install -r backend/requirements.txt
pip install pyinstaller
```

### Electron app won't start backend
- Check that `backend/dist/financial-backend.exe` exists
- Rebuild: `npm run build:backend`

## File Structure

```
rg-data/
├── start.sh              # Quick start (Linux/Mac/WSL)
├── stop.sh               # Stop servers
├── electron/             # Electron app files
│   ├── main.js          # Main process
│   └── preload.js       # Security bridge
├── backend/             # Python Flask backend
│   ├── app.py           # Main backend
│   └── dist/            # Built executable (after build)
├── frontend/            # Web UI
├── scripts/             # Build scripts
└── package.json         # npm configuration
```

## Next Steps

- See `ELECTRON_BUILD.md` for detailed build instructions
- See `README.md` for application features and usage

