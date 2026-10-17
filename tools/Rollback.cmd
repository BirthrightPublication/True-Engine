@echo off
setlocal
set /p "BACKUP=Backup ID from Backups folder: "
py -3 "%~dp0updater.py" --root "%~dp0." --rollback "%BACKUP%"
pause
