@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0app\Start-TrueEngine.ps1" -Root "%~dp0."
set "RESULT=%ERRORLEVEL%"
pause
exit /b %RESULT%
