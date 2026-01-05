"""
Install dependencies for Nimble Encounter Builder.

This script installs all required Python packages to run and build
the Nimble Encounter Builder application.

Usage:
    python install_dependencies.py
"""

import subprocess
import sys

def install_package(package_name):
    """Install a package using pip."""
    print(f"Installing {package_name}...")
    try:
        # Use the current interpreter to avoid venv mismatches.
        subprocess.check_call([
            sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            package_name
        ])
        print(f"  [OK] {package_name} installed successfully")
        return True
    except subprocess.CalledProcessError:
        print(f"  [FAILED] Could not install {package_name}")
        return False

def main():
    print("=" * 70)
    print("Nimble Encounter Builder - Dependency Installer")
    print("=" * 70)
    print()
    print("This will install the following packages:")
    print("  - PySide6 (GUI framework)")
    print("  - pyinstaller (for building executables)")
    print()

    input("Press Enter to continue, or Ctrl+C to cancel...")
    print()

    packages = [
        "PySide6",
        "pyinstaller",
    ]

    success_count = 0
    failed = []

    for package in packages:
        if install_package(package):
            success_count += 1
        else:
            failed.append(package)
        print()

    print("=" * 70)
    print("Installation Summary")
    print("=" * 70)
    print()
    print(f"Successfully installed: {success_count}/{len(packages)} packages")

    if failed:
        print()
        print("Failed packages:")
        for pkg in failed:
            print(f"  - {pkg}")
        print()
        print("You may need to install these manually:")
        for pkg in failed:
            print(f"    pip install {pkg}")
        print()
        return 1
    else:
        print()
        print("All dependencies installed successfully!")
        print()
        print("Next steps:")
        print("  1. Test the application: python NimbleEncounterBuilder.py")
        print("  2. Build executable: python _ClickMeToBuild.py")
        print()
        return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print()
        print()
        print("Installation cancelled by user.")
        sys.exit(1)
