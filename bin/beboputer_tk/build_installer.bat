@echo off
rem build_installer.bat -- Windows installer build for the tkinter port.
rem Mirrors bin\beboputer_v7\build_installer.bat exactly; see that
rem file if you're comparing the two side by side.
rem
rem Must be run ON WINDOWS -- PyInstaller does not cross-compile, so a
rem Windows .exe cannot be produced from this Linux/macOS dev sandbox
rem (see beboputer_tk.spec's own header for the full explanation).
rem
rem %~dp0 = this script's folder (bin\beboputer_tk\); project root is two levels up.
cd /d "%~dp0..\.."

echo ============================================================
echo  Step 0: Reading app version from bin\beboputer_v7\__init__.py
echo ============================================================
rem beboputer_tk re-exports the exact same __version__ constant (see
rem bin\beboputer_tk\__init__.py) -- reading it from beboputer_v7
rem directly here keeps this script identical to the Qt build's, and
rem there's only ever one version number for the whole app either way.
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
python -m PyInstaller bin\beboputer_tk\beboputer_tk.spec --noconfirm
if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller failed. See output above.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  Step 2: Inno Setup -- creating BeboputerTkSetup.exe
echo ============================================================
"C:\Program Files (x86)\Inno Setup 6\iscc.exe" bin\beboputer_tk\beboputer_tk_setup.iss
if errorlevel 1 (
    echo.
    echo ERROR: Inno Setup failed. See output above.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  Done!  Installer is at:
echo  dist\BeboputerTkSetup.exe
echo ============================================================
pause
