@echo off
setlocal
set /p "PACKAGE=Full path to release ZIP: "
set /p "HASH=Trusted release SHA-256: "
py -3 "%~dp0updater.py" --root "%~dp0." --package "%PACKAGE%" --sha256 "%HASH%"
pause
