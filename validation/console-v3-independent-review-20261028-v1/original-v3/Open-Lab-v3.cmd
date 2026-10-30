@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Open-Lab-v3.ps1"
if errorlevel 1 pause
