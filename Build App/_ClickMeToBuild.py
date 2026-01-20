"""
Fixed build script for Nimble Encounter Builder with improved PySide6 handling.

This script ensures PySide6 is properly included in the executable.

Usage:
    python _ClickMeToBuild.py

Requirements:
    pip install pyinstaller PySide6
"""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

def check_dependencies():
    """Check that required packages are installed."""
    print("Checking dependencies...")

    missing = []

    try:
        import PyInstaller
        print("  [OK] PyInstaller found")
    except ImportError:
        print("  [MISSING] PyInstaller not found")
        missing.append("pyinstaller")

    try:
        import PySide6
        print("  [OK] PySide6 found")
        # Get PySide6 location
        pyside_path = Path(PySide6.__file__).parent
        print(f"       Location: {pyside_path}")
    except ImportError:
        print("  [MISSING] PySide6 not found")
        missing.append("PySide6")
        pyside_path = None

    if missing:
        print()
        print("Missing dependencies! Install with:")
        print(f"    pip install {' '.join(missing)}")
        print()
        return False, None

    print()
    return True, pyside_path


def _next_build_name(project_root: Path) -> str:
    timestamp = datetime.now().strftime("%H%M-%b%d-%Y")
    return f"Nimble Encounter Builder {timestamp}"


def create_spec_file(pyside_path):
    """Create an enhanced spec file with proper PySide6 handling."""
    project_root = Path(__file__).resolve().parents[1]
    app_name = _next_build_name(project_root)
    main_script = project_root / "NimbleEncounterBuilder.py"
    ui_dir = project_root / "uiDesign"
    ui_file = ui_dir / "nimbleHandy.ui"
    readme_file = project_root / "README.html"
    icon_file = project_root / "EncounterBuilderIconImage.png"
    splash_file = project_root / "EncounterBuilderAppImage.png"
    spec_file = Path(__file__).resolve().parent / "NimbleEncounterBuilder.spec"

    # Check required files
    if not main_script.exists():
        print(f"ERROR: Main script not found: {main_script}")
        return None

    if not ui_file.exists():
        print(f"ERROR: UI file not found: {ui_file}")
        return None

    # Prepare paths for spec file (use forward slashes for cross-platform)
    main_script_str = str(main_script).replace('\\', '/')
    project_root_str = str(project_root).replace('\\', '/')
    ui_file_str = str(ui_file).replace('\\', '/')
    readme_file_str = str(readme_file).replace('\\', '/') if readme_file.exists() else ""

    # Icon line (optional) keeps Windows build branded.
    icon_line = f"icon='{str(icon_file).replace(chr(92), '/')}',  # Application icon" if icon_file.exists() else ""

    # Data files bundled into the app (UI, README, splash).
    ui_files = sorted(ui_dir.glob("*.ui")) if ui_dir.exists() else []
    datas = []
    if ui_files:
        for ui_path in ui_files:
            ui_path_str = str(ui_path).replace('\\', '/')
            datas.append(f"('{ui_path_str}', 'uiDesign'),")
    else:
        datas.append(f"('{ui_file_str}', 'uiDesign'),")
    if readme_file.exists():
        datas.append(f"('{readme_file_str}', '.'),")
    if splash_file.exists():
        splash_file_str = str(splash_file).replace('\\', '/')
        datas.append(f"('{splash_file_str}', '.'),")

    # PySide6 binary includes
    pyside_binaries = ""
    if pyside_path:
        # Include PySide6 plugins
        pyside_path_str = str(pyside_path).replace('\\', '/')
        pyside_binaries = f"""
    # PySide6 binaries and plugins
    binaries=[
        ('{pyside_path_str}/plugins/platforms', 'PySide6/plugins/platforms'),
        ('{pyside_path_str}/plugins/styles', 'PySide6/plugins/styles'),
    ],"""

    debug_console = os.environ.get("NIMBLE_BUILD_CONSOLE", "").strip() == "1"

    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Nimble Encounter Builder
# Auto-generated with enhanced PySide6 support

block_cipher = None

a = Analysis(
    ['{main_script_str}'],
    pathex=['{project_root_str}'],
    {pyside_binaries if pyside_binaries else "binaries=[],"}
    datas=[
        {chr(10).join('        ' + d for d in datas)}
    ],
    hiddenimports=[
        # PySide6 modules
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtUiTools',
        'shiboken6',
        # Application modules
        'modules.combatManager',
        'modules.combatants',
        'modules.config',
        'modules.persistence',
        'modules.shared_statblock',
        'modules.condition_descriptions',
        'tabs.heroes_tab',
        'tabs.combat_tab',
        'tabs.bestiary_tab',
        'tabs.config_tab',
        'tabs.hero_dialog',
        'tabs.conditions_dialog',
        'tabs.damage_heal_dialog',
        'tabs.add_edit_monster_dialog',
        'tabs.marker_dialog',
        'tabs.random_encounter_dialog',
        'tabs.bulk_marker_dialog',
        'tabs.vault_viewer_controller',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'tkinter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{app_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console={str(debug_console)},  # Set NIMBLE_BUILD_CONSOLE=1 for debug output
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    {icon_line}
)
"""

    # Write spec file
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)

    print(f"Created spec file: {spec_file}")
    return spec_file, app_name


def build_from_spec(spec_file):
    """Build the executable using PyInstaller."""
    project_root = Path(__file__).resolve().parents[1]
    build_dir = project_root.parent / "build"
    build_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,  # Use the same Python interpreter
        "-m",
        "PyInstaller",
        "--distpath",
        str(build_dir),
        "--clean",
        "--noconfirm",
        str(spec_file)
    ]

    print()
    print("Building executable with PyInstaller...")
    print("Command:", " ".join(cmd))
    print()
    print("This may take several minutes...")
    print()

    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            check=True,
            capture_output=False,  # Show PyInstaller output
            text=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Build failed with error code: {e.returncode}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


def main():
    """Main build process."""
    print("=" * 70)
    print("Nimble Encounter Builder - Fixed Build Script")
    print("=" * 70)
    print()

    # Check dependencies
    deps_ok, pyside_path = check_dependencies()
    if not deps_ok:
        return 1

    # Create spec file
    print("Creating PyInstaller spec file...")
    created = create_spec_file(pyside_path)
    if not created:
        return 1
    spec_file, app_name = created

    print()

    # Build executable
    if build_from_spec(spec_file):
        project_root = Path(__file__).resolve().parents[1]
        exe_path = project_root.parent / "build" / f"{app_name}.exe"

        print()
        print("=" * 70)
        print("BUILD SUCCESSFUL!")
        print("=" * 70)
        print()
        print(f"Executable created: {exe_path}")
        print()
        print("Next steps:")
        print("  1. Test the executable by running it")
        print("  2. Create a distribution folder with:")
        print(f"     - {app_name}.exe")
        print("     - Bestiary folder (if you have one)")
        print("     - Any config files you want to include")
        print()
        print("The executable is standalone and portable!")
        print()
        return 0
    else:
        print()
        print("=" * 70)
        print("BUILD FAILED!")
        print("=" * 70)
        print()
        print("Troubleshooting:")
        print("  1. Make sure PySide6 is installed: pip install PySide6")
        print("  2. Make sure PyInstaller is installed: pip install pyinstaller")
        print("  3. Try running: pip install --upgrade pyinstaller PySide6")
        print("  4. Check that NimbleEncounterBuilder.py runs successfully before building")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())

