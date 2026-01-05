# Building Nimble Encounter Builder to EXE

This guide explains how to package the Nimble Encounter Builder into a standalone executable (.exe) file.

## Quick Start

**Option 1: Use the batch file (Easiest)**
1. Double-click `Build App/BUILD.bat`
2. Wait for the build to complete
3. Find your executable in the `dist` folder

**Option 2: Use Python directly**
```bash
python "Build App/build_exe_advanced.py"
```

**Option 3: Simple build**
```bash
python "Build App/build_exe.py"
```

## Requirements

- Python 3.7 or higher
- PyInstaller (`pip install pyinstaller`)
- All dependencies installed (`pip install -r requirements.txt` if you have one)

## Build Scripts

### BUILD.bat
- Automatically checks for and installs PyInstaller
- Runs the advanced build script
- Easiest option for Windows users

### build_exe_advanced.py
- Creates a PyInstaller spec file for more control
- Includes UI file and README.html
- Optimizes the build
- Recommended for most users

### build_exe.py
- Simple one-command build
- Quick and straightforward
- Good for testing

## What Gets Included

The executable will include:
- All Python code
- PySide6 Qt libraries
- UI file (nimbleHandy.ui)
- README.html for the help tab

## What You Need to Distribute

When sharing the application, you'll need to provide:

1. **The .exe file** from the `dist` folder
2. **The Bestiary folder** with all monster JSON files
3. **Config file** (optional - app will create defaults)

### Recommended distribution structure:
```
NimbleEncounterBuilder/
├── Nimble Encounter Builder vYYMMDDNN.exe
├── Bestiary/
│   ├── monster1.json
│   ├── monster2.json
│   └── ...
├── config.json (optional)
└── README.txt (optional - user guide)
```

## Troubleshooting

### "PyInstaller not found"
Install it with:
```bash
pip install pyinstaller
```

### "Module not found" errors
Make sure all dependencies are installed:
```bash
pip install PySide6
```

### Executable is too large
This is normal - PyInstaller bundles the entire Python runtime and Qt libraries.
Expect 80-150 MB for a PySide6 application.

### Antivirus false positives
PyInstaller executables sometimes trigger false positives. You may need to:
- Add an exception in your antivirus
- Sign the executable with a code signing certificate (advanced)

## Advanced Options

### Creating an icon
1. Create or download an `icon.ico` file
2. Place it in the project root
3. The build script will automatically include it

### Console mode (for debugging)
Edit `Build App/build_exe_advanced.py` and change:
```python
console=False,  # Change to True to see console output
```

### Custom spec file
After running `build_exe_advanced.py` once, you can edit the generated
`Build App/NimbleEncounterBuilder.spec` file and rebuild with:
```bash
pyinstaller --clean --noconfirm "Build App/NimbleEncounterBuilder.spec"
```

## Build Output

After a successful build:
- `dist/` - Contains the final executable
- `build/` - Temporary build files (can be deleted)
- `Build App/NimbleEncounterBuilder.spec` - PyInstaller specification (keep for custom builds)

## File Size Optimization

To reduce executable size:
1. Use UPX compression (enabled by default)
2. Remove unused imports from your code
3. Consider using PyInstaller's `--exclude-module` option for modules you don't need

## Additional Resources

- [PyInstaller Documentation](https://pyinstaller.org/en/stable/)
- [PySide6 Deployment Guide](https://doc.qt.io/qtforpython/deployment-pyinstaller.html)


