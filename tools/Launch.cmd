@echo off
if not exist "%~dp0Data" mkdir "%~dp0Data"
cd /d "%~dp0Data"
"%~dp0Current\true-engine-viewport.exe"
