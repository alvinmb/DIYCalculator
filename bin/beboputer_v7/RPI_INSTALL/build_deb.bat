@echo off
echo ============================================================
echo  Building Beboputer Raspberry Pi .deb package via WSL
echo ============================================================
rem %~dp0 = this script's folder on Windows; convert to a WSL path so this
rem works regardless of where the repo is checked out.
for /f "delims=" %%i in ('wsl wslpath -a "%~dp0build_deb.sh"') do set WSL_SCRIPT=%%i
wsl bash "%WSL_SCRIPT%"
if errorlevel 1 (
    echo.
    echo ERROR: Build failed. See output above.
    echo If WSL is not installed, open PowerShell as Admin and run:
    echo   wsl --install
    pause
    exit /b 1
)
echo.
echo Done! Copy the .deb from dist\ (beboputer_^<version^>_all.deb) to your Raspberry Pi.
pause
