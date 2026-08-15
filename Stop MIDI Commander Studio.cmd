@echo off
setlocal

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Stop MIDI Commander Studio.ps1"
if errorlevel 1 pause

endlocal
