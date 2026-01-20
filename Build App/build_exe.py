"""
Build script to package Nimble Encounter Builder into a standalone executable.

Usage:
    python build_exe.py

Requirements:
    pip install pyinstaller

This will create a single .exe file in the 'dist' folder.
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

def build_executable():
    """Build the executable using PyInstaller."""

    print("=" * 60)
    print("Nimble Encounter Builder - Build Script")
    print("=" * 60)
    print()

    # Get the project root directory
    project_root = Path(__file__).resolve().parents[1]

    # Main script to execute
    main_script = project_root / "NimbleEncounterBuilder.py"

    if not main_script.exists():
        print(f"ERROR: Main script not found at {main_script}")
        return 1

    # Icon file (optional - create one if you have it)
    icon_file = project_root / "EncounterBuilderIconImage.png"
    icon_option = f"--icon={icon_file}" if icon_file.exists() else ""

    # UI files that need to be included
    ui_dir = project_root / "uiDesign"
    ui_files = sorted(ui_dir.glob("*.ui")) if ui_dir.exists() else []

    # README.html for the help tab
    readme_file = project_root / "README.html"
    splash_file = project_root / "EncounterBuilderAppImage.png"

    # Build name: Nimble Encounter Builder HHMM-MonDD-YYYY.
    timestamp = datetime.now().strftime("%H%M-%b%d-%Y")
    dist_dir = project_root.parent / "build"
    app_name = f"Nimble Encounter Builder {timestamp}"

    # Build the PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",                           # Create a single executable
        "--windowed",                          # No console window (GUI app)
        f"--name={app_name}",                  # Name of the executable
        f"--distpath={dist_dir}",              # Put outputs in repo-level build folder
        # Add UI files below
        f"--add-data={readme_file};.",        # Include README
        "--hidden-import=PySide6",            # Ensure PySide6 is included
        "--hidden-import=PySide6.QtCore",     # Qt Core module
        "--hidden-import=PySide6.QtGui",      # Qt GUI module
        "--hidden-import=PySide6.QtWidgets",  # Qt Widgets module
        "--hidden-import=PySide6.QtUiTools",  # Qt UI Tools for .ui loading
        "--hidden-import=shiboken6",          # PySide6 dependency
        "--clean",                             # Clean PyInstaller cache
        "--noconfirm",                         # Overwrite without asking
    ]

    # Add UI files
    for ui_file in ui_files:
        cmd.append(f"--add-data={ui_file};uiDesign")
    if splash_file.exists():
        cmd.append(f"--add-data={splash_file};.")

    # Add icon if it exists
    if icon_option:
        cmd.append(icon_option)

    # Add the main script
    cmd.append(str(main_script))

    print("Building executable with PyInstaller...")
    print()
    print("Command:", " ".join(cmd))
    print()

    try:
        # Run PyInstaller
        result = subprocess.run(cmd, cwd=project_root, check=True)

        print()
        print("=" * 60)
        print("BUILD SUCCESSFUL!")
        print("=" * 60)
        print()
        print(f"Executable location: {dist_dir / f'{app_name}.exe'}")
        print()
        print("You can now distribute the .exe file from the 'build' folder.")
        print()

        return 0

    except subprocess.CalledProcessError as e:
        print()
        print("=" * 60)
        print("BUILD FAILED!")
        print("=" * 60)
        print()
        print(f"Error: {e}")
        print()
        print("Make sure PyInstaller is installed:")
        print("    pip install pyinstaller")
        print()
        return 1

    except FileNotFoundError:
        print()
        print("=" * 60)
        print("PyInstaller NOT FOUND!")
        print("=" * 60)
        print()
        print("Please install PyInstaller first:")
        print("    pip install pyinstaller")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(build_executable())

