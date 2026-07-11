@echo off
echo Checking .deb for key directories...
set OUT=%~dp0deb_contents.txt
rem Version is read from bin/beboputer_v7/__init__.py at build time, so the
rem .deb filename varies by release -- locate whatever is newest in dist\
rem instead of hardcoding a version number here.
for /f "delims=" %%i in ('wsl wslpath -a "%~dp0..\..\..\dist"') do set WSL_DIST=%%i
wsl bash -c "DEB=$(ls -t '%WSL_DIST%'/beboputer_*_all.deb 2>/dev/null | head -1); if [ -z \"$DEB\" ]; then echo 'No beboputer_*_all.deb found in dist/. Run build_deb.sh first.'; exit 1; fi; echo \"Inspecting: $DEB\"; dpkg-deb -c \"$DEB\" | grep -E '(BITMAPS|Config|Data|databook|WorkInProgress|tutorial)' | head -20" > "%OUT%" 2>&1
echo Done. Results in deb_contents.txt
pause
