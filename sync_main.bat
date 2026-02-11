@echo off
setlocal

set "ROOT=%~dp0"
set "SCRIPT=%ROOT%sync_main.ps1"

if not exist "%SCRIPT%" (
  echo Error: script not found: "%SCRIPT%"
  exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "& '%SCRIPT%' %*"
exit /b %ERRORLEVEL%
