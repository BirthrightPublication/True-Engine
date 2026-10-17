@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0TrueEngine-Bootstrap.ps1" -Root "%~dp0."
set "RESULT=%ERRORLEVEL%"
pause
exit /b %RESULT%
