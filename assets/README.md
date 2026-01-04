# Assets Directory

This directory contains application assets like icons.

## Icon Requirements

For Windows builds, you need:
- `icon.ico` - Windows icon file (256x256 or larger, multi-resolution)

### Creating an Icon

1. **Online Tools:**
   - Use [ICO Convert](https://icoconvert.com/) or [ConvertICO](https://convertico.com/)
   - Upload a PNG image (512x512 or 1024x1024 recommended)
   - Download the `.ico` file

2. **From PNG:**
   ```bash
   # Using ImageMagick (if installed)
   convert icon.png -resize 256x256 icon.ico
   ```

3. **Place the file:**
   - Save as `icon.ico` in this directory
   - The build process will automatically use it

## Current Status

⚠️ **No icon file found** - The app will use the default Electron icon.

To add an icon:
1. Create or download an `.ico` file
2. Save it as `icon.ico` in this directory
3. Rebuild the application

