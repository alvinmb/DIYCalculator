@echo off
echo ============================================================
echo  Building Beboputer Raspberry Pi .deb package via WSL
echo ============================================================
wsl bash /mnt/c/Users/Alvin-Dell/OneDrive/Desktop/Bebop_python/bin/beboputer_v7/RPI_INSTALL/build_deb.sh
if errorlevel 1 (
    echo.
    echo ERROR: Build failed. See output above.
    echo If WSL is not installed, open PowerShell as Admin and run:
    echo   wsl --install
    pause
    exit /b 1
)
echo.
echo Done! Copy dist/beboputer_7.0.0_all.deb to your Raspberry Pi.
pause
