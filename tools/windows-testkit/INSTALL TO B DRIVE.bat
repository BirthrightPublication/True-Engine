@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-To-B-Drive.ps1"
set "RESULT=%ERRORLEVEL%"
pause
exit /b %RESULT%
