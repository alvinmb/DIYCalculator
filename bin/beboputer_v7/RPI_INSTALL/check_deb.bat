@echo off
echo Checking .deb for key directories...
set OUT=%~dp0deb_contents.txt
for /f "delims=" %%i in ('wsl wslpath -a "%~dp0..\..\..\dist\beboputer_7.0.0_all.deb"') do set WSL_DEB=%%i
wsl bash -c "dpkg-deb -c '%WSL_DEB%' | grep -E '(BITMAPS|Config|Data|databook|WorkInProgress|tutorial)' | head -20" > "%OUT%" 2>&1
echo Done. Results in deb_contents.t