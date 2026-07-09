@echo off
rem %~dp0 = this script's folder (bin\beboputer_v7\); project root is two levels up.
cd /d "%~dp0..\.."

echo ============================================================
echo  Step 0: Reading app version from bin\beboputer_v7\__init__.py
echo ============================================================
for /f "delims=" %%v in ('python -c "import sys; sys.path.insert(0, 'bin'); from beboputer_v7 import __version__; print(__version__)"') do set BEBOPUTER_VERSION=%%v
if "%BEBOPUTER_VERSION%"=="" (
    echo.
    echo ERROR: Could not read __version__ from beboputer_v7. Is Python on PATH?
    pause
    exit /b 1
)
echo  Version: %BEBOPUTER_VERSION%

echo.
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
echo =======================