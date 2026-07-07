@echo off
rem %~dp0 = this script's folder (bin\beboputer_v7\); project root is two levels up.
cd /d "%~dp0..\.."
echo ============================================================
echo  Step 1: PyInstaller -- bundling app into dist\Beboputer\
echo ============================================================
if exist dist\Beboputer (
    echo Removing old dist\Beboputer ...
    rmdir /s /q dist\Beboputer
)
python -m PyInstaller bin\beboputer_v7\beboputer.spec --noconfirm
if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller failed. See output above.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  Step 2: Inno Setup -- creating BeboputerSetup.exe
echo ============================================================
"C:\Program Files (x86)\Inno Setup 6\iscc.exe" bin\beboputer_v7\beboputer_setup.iss
if errorlevel 1 (
    echo.
    echo ERROR: Inno Setup failed. See output above.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  Done!  Installer is at:
echo  dist\BeboputerSetup.exe
echo ============================================================
pause
