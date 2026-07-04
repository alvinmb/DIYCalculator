@echo off
echo Checking .deb for key directories...
set OUT=C:\Users\Alvin-Dell\OneDrive\Desktop\Bebop_python\bin\beboputer_v7\RPI_INSTALL\deb_contents.txt
wsl bash -c "dpkg-deb -c '/mnt/c/Users/Alvin-Dell/OneDrive/Desktop/Bebop_python/dist/beboputer_7.0.0_all.deb' | grep -E '(BITMAPS|Config|Data|databook|WorkInProgress)' | head -20" > "%OUT%" 2>&1
echo Done. Results in deb_contents.txt
pause
