@echo off
powershell.exe -NoProfile -STA -ExecutionPolicy Bypass -File "%~dp0Apply-Patch.ps1"
echo.
pause
