@echo off
REM Build script for Nimble Encounter Builder

echo ============================================================
echo Nimble Encounter Builder - Build to EXE
echo ============================================================
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller is not installed. Installing now...
    pip install pyinstaller
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to install PyInstaller
        echo Please install manually: pip install pyinstaller
        pause
        exit /b 1
    )
)

echo.
echo PyInstaller is ready!
echo.
echo Building executable...
echo.

REM Run the build script
python _ClickMeToBuild.py

if errorlevel 1 (
    echo.
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Build complete! Check the 'dist' folder for your .exe
echo ============================================================
echo.
pause
