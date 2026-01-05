"""
Advanced build script to package Nimble Encounter Builder into a standalone executable.

This script creates a PyInstaller spec file for more control over the build process,
then builds the executable.

Usage:
    python build_exe_advanced.py

Requirements:
    pip install pyinstaller
"""

import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SPEC_TEMPLATE = """
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{main_script}'],
    pathex=['{project_root}'],
    binaries=[],
    datas=[
{datas}
    ],
    hiddenimports=[
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtUiTools',
        'shiboken6',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
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
    console=False,  # Set to True if you want to see console output for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    {icon_line}
)
"""

def create_spec_file():
    """Create a PyInstaller spec file."""
    project_root = Path(__file__).resolve().parents[1]
    yymmdd = datetime.now().strftime("%y%m%d")
    dist_dir = project_root.parent / "build"
    pattern = re.compile(rf"^Nimble Encounter Builder v{yymmdd}(\d{{2}})\.exe$")
    max_build = 0
    if dist_dir.exists():
        # Scan existing builds to increment the daily counter.
        for path in dist_dir.iterdir():
            if not path.is_file():
                continue
            match = pattern.match(path.name)
            if match:
                try:
                    max_build = max(max_build, int(match.group(1)))
                except ValueError:
                    continue
    app_name = f"Nimble Encounter Builder v{yymmdd}{max_build + 1:02d}"
    main_script = project_root / "NimbleEncounterBuilder.py"
    ui_dir = project_root / "uiDesign"
    ui_file = ui_dir / "nimbleHandy.ui"
    readme_file = project_root / "README.html"
    splash_file = project_root / "EncounterBuilderAppImage.png"
    icon_file = project_root / "EncounterBuilderIconImage.png"
    spec_file = Path(__file__).resolve().parent / "NimbleEncounterBuilder.spec"

    # Check required files exist
    if not main_script.exists():
        print(f"ERROR: Main script not found at {main_script}")
        return None

    if not ui_dir.exists() and not ui_file.exists():
        print(f"ERROR: UI directory not found at {ui_dir}")
        return None

    if not readme_file.exists():
        print(f"WARNING: README.html not found at {readme_file}")

    # Icon line (optional)
    icon_line = f"icon='{icon_file}'," if icon_file.exists() else ""

    # Create spec content
    ui_files = sorted(ui_dir.glob("*.ui")) if ui_dir.exists() else []
    if ui_files:
        datas_lines = [
            f"        ('{str(path).replace('\\\\', '/')}', 'uiDesign'),"
            for path in ui_files
        ]
    else:
        datas_lines = [f"        ('{str(ui_file).replace('\\\\', '/')}', 'uiDesign'),"]
    if readme_file.exists():
        datas_lines.append(f"        ('{str(readme_file).replace('\\\\', '/')}', '.'),")
    if splash_file.exists():
        datas_lines.append(f"        ('{str(splash_file).replace('\\\\', '/')}', '.'),")

    spec_content = SPEC_TEMPLATE.format(
        main_script=str(main_script).replace('\\', '/'),
        project_root=str(project_root).replace('\\', '/'),
        datas="\n".join(datas_lines),
        app_name=app_name,
        icon_line=icon_line
    )

    # Write spec file
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)

    print(f"Created spec file: {spec_file}")
    return spec_file, app_name


def build_from_spec(spec_file):
    """Build the executable from a spec file."""
    project_root = Path(__file__).resolve().parents[1]
    build_dir = project_root.parent / "build"
    build_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "python",
        "-m",
        "PyInstaller",
        "--distpath",
        str(build_dir),
        "--clean",
        "--noconfirm",
        str(spec_file)
    ]

    print()
    print("Building executable...")
    print("Command:", " ".join(cmd))
    print()

    try:
        subprocess.run(cmd, cwd=project_root, check=True)
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        print("ERROR: PyInstaller not found. Install it with: pip install pyinstaller")
        return False


def main():
    print("=" * 60)
    print("Nimble Encounter Builder - Advanced Build Script")
    print("=" * 60)
    print()

    # Create spec file
    created = create_spec_file()
    if not created:
        return 1
    spec_file, app_name = created

    print()

    # Build from spec
    if build_from_spec(spec_file):
        project_root = Path(__file__).resolve().parents[1]
        exe_path = project_root.parent / "build" / f"{app_name}.exe"

        print()
        print("=" * 60)
        print("BUILD SUCCESSFUL!")
        print("=" * 60)
        print()
        print(f"Executable: {exe_path}")
        print()
        print("Distribution notes:")
        print("  - The .exe file is standalone and portable")
        print("  - Users will need the Bestiary folder in the same directory")
        print("  - Users will need a config file (or it will create defaults)")
        print()
        return 0
    else:
        print()
        print("=" * 60)
        print("BUILD FAILED!")
        print("=" * 60)
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())

