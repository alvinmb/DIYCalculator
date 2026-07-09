@echo off
echo Checking .deb for key directories...
set OUT=%~dp0deb_contents.txt
rem Version is read from bin/beboputer_v7/__init__.py at build time, so the
rem .deb filename varies by release -- locate whatever is newest in dist\
rem instead of hardcoding a version number here.
for /f "delims=" %%i in ('wsl wslpath -a "%~dp0..\..\..\dist"') do set WSL_