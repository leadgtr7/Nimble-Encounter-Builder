# Building Nimble Encounter Builder


Nimble Encounter Builder is an independent product published under the Nimble 3rd Party Creator License. Nimble © Nimble Co.
This guide explains how to build the Nimble Encounter Builder into a standalone executable.

## Prerequisites

### 1. Python Installation
- **Python 3.12** (or compatible version)
- Verify installation: `python --version`

### 2. Required Python Packages

Install all required packages:

```bash
pip install PySide6 pyinstaller
```

**Individual package descriptions:**
- **PySide6**: Qt framework for the GUI (required for running and building)
- **pyinstaller**: Package application into standalone executable

### 3. Verify Installation

Check that packages are installed:

```bash
python -c "import PySide6; print('PySide6:', PySide6.__version__)"
python -c "import PyInstaller; print('PyInstaller OK')"
```

## Building the Executable

### Option 1: Quick Build (Recommended)

Use the fixed build script which handles all PySide6 dependencies:

```bash
python "Build App/_ClickMeToBuild.py"
```

This will:
1. Check for required dependencies
2. Create a PyInstaller spec file with proper PySide6 configuration
3. Build a standalone executable
4. Place the result in the `dist/` folder

### Option 2: Advanced Build

For more control, use the advanced build script:

```bash
python "Build App/build_exe_advanced.py"
```

### Option 3: Simple Build

Basic build with minimal configuration:

```bash
python "Build App/build_exe.py"
```

## Build Output

After a successful build, you'll find:

```
dist/
  └── Nimble Encounter Builder vMMDDYYYY_HHMMSS.exe  (standalone executable)
```

## Distribution

To distribute your application:

1. **Copy the executable**: `dist/Nimble Encounter Builder vMMDDYYYY_HHMMSS.exe`

2. **Include supporting files** (optional):
   - `Bestiary/` folder (if you have custom monsters)
   - `config.json` (if you want to include default settings)
   - `README.html` (user documentation)

3. **Create a distribution folder structure**:
   ```
   NimbleEncounterBuilder/
     ├── Nimble Encounter Builder vMMDDYYYY_HHMMSS.exe
     ├── Bestiary/
     │   └── (monster JSON files)
     └── README.html
   ```

## Troubleshooting

### Build Error: "No module named 'PySide6'"

**Solution**: Install PySide6:
```bash
pip install PySide6
```

### Build Error: "No module named 'PyInstaller'"

**Solution**: Install PyInstaller:
```bash
pip install pyinstaller
```

### Executable Doesn't Run

1. **Try running from command line** to see error messages:
   ```bash
   cd dist
   Nimble Encounter Builder vMMDDYYYY_HHMMSS.exe
   ```

2. **Check antivirus**: Some antivirus software flags PyInstaller executables. Add an exception.

3. **Rebuild with console mode** for debugging:
   - Edit the spec file
   - Change `console=False` to `console=True`
   - Rebuild: `pyinstaller --clean --noconfirm "Build App/NimbleEncounterBuilder.spec"`

### Missing UI Elements

If the UI doesn't load:
- Ensure `uiDesign/nimbleHandy.ui` exists
- Check the build script included it: look for `add-data` in the command output

### Import Errors in Executable

If modules are missing:
- Add them to `hiddenimports` in the spec file
- Rebuild

## Build from Scratch

If you need to start fresh:

```bash
# Clean previous builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "Build App\\NimbleEncounterBuilder.spec" del "Build App\\NimbleEncounterBuilder.spec"

# Rebuild
python "Build App/_ClickMeToBuild.py"
```

## Testing the Executable

Before distributing:

1. **Test on your machine**:
   ```bash
   cd dist
   Nimble Encounter Builder vMMDDYYYY_HHMMSS.exe
   ```

2. **Test all features**:
   - Add/delete heroes
   - Add/delete monsters
   - Import/export parties
   - Save/load encounters
   - All tabs (Combat, Heroes, Bestiary, Config)

3. **Test on a clean machine** (recommended):
   - Use a VM or another computer
   - Ensure it works without Python installed
   - Check all features work

## Build Configuration

The build process uses a PyInstaller spec file that:

- Includes all PySide6 modules and plugins
- Bundles the UI file (`nimbleHandy.ui`)
- Includes README for help tab
- Excludes unnecessary packages (matplotlib, numpy, etc.)
- Creates a single-file executable
- Disables console window (GUI mode)

You can customize the spec file for your needs.

## Advanced: Custom Icon

To use a custom icon:

1. Create or obtain an `.ico` file
2. Name it `icon.ico` and place it in the project root
3. The build script will automatically use it

## Getting Help

If you encounter issues:

1. Check this guide's troubleshooting section
2. Run the test suite: `python test_full_app.py`
3. Ensure the app runs normally: `python NimbleEncounterBuilder.py`
4. Check PyInstaller documentation: https://pyinstaller.org/



