const { spawn, execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

console.log('🔨 Building Python backend...\n');

const backendPath = path.join(__dirname, '..', 'backend');
const distPath = path.join(backendPath, 'dist');
const specPath = path.join(backendPath, 'financial-backend.spec');

// Check if PyInstaller is installed
try {
  execSync('pyinstaller --version', { stdio: 'ignore' });
  console.log('✅ PyInstaller found\n');
} catch (error) {
  console.error('❌ PyInstaller not found. Installing...\n');
  try {
    execSync('pip install pyinstaller', { stdio: 'inherit' });
    console.log('✅ PyInstaller installed\n');
  } catch (installError) {
    console.error('❌ Failed to install PyInstaller');
    console.error('Please install it manually: pip install pyinstaller');
    process.exit(1);
  }
}

// Check if virtual environment exists and activate it
const venvPath = path.join(__dirname, '..', 'venv');
const venvPython = process.platform === 'win32'
  ? path.join(venvPath, 'Scripts', 'python.exe')
  : path.join(venvPath, 'bin', 'python');

let pythonCmd = 'python';
if (fs.existsSync(venvPython)) {
  pythonCmd = venvPython;
  console.log(`✅ Using virtual environment: ${venvPython}\n`);
} else {
  console.log('⚠️  Virtual environment not found, using system Python\n');
}

// Clean previous build
if (fs.existsSync(distPath)) {
  console.log('🧹 Cleaning previous build...\n');
  fs.rmSync(distPath, { recursive: true, force: true });
}

// Check if spec file exists
if (!fs.existsSync(specPath)) {
  console.error('❌ PyInstaller spec file not found:', specPath);
  process.exit(1);
}

// Build with PyInstaller
console.log('📦 Building executable with PyInstaller...\n');
console.log(`Command: ${pythonCmd} -m PyInstaller ${specPath}\n`);

const buildProcess = spawn(pythonCmd, ['-m', 'PyInstaller', specPath], {
  cwd: backendPath,
  stdio: 'inherit',
  shell: true
});

buildProcess.on('close', (code) => {
  if (code === 0) {
    const exePath = path.join(distPath, 'financial-backend.exe');
    if (fs.existsSync(exePath)) {
      console.log('\n✅ Backend build successful!');
      console.log(`   Executable: ${exePath}\n`);
    } else {
      console.error('\n❌ Build completed but executable not found');
      process.exit(1);
    }
  } else {
    console.error(`\n❌ Build failed with code ${code}`);
    process.exit(1);
  }
});

buildProcess.on('error', (error) => {
  console.error('❌ Failed to start build process:', error.message);
  process.exit(1);
});

