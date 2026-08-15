@echo off
setlocal

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Launch MIDI Commander Studio.ps1"
if errorlevel 1 (
  echo.
  echo MIDI Commander Studio could not be started. Review the message above.
  pause
)

endlocal
