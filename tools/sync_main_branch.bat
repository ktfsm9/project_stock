@echo off
setlocal

set "SCRIPT_PATH=%~dp0sync_main_branch.ps1"
if not exist "%SCRIPT_PATH%" (
  echo Error: script not found: "%SCRIPT_PATH%"
  exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "& '%SCRIPT_PATH%' %*"
exit /b %ERRORLEVEL%
