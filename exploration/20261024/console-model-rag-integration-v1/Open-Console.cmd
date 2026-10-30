@echo off
set "RTL_INTEGRATION_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\pythonw.exe"
if not exist "%RTL_INTEGRATION_PYTHON%" exit /b 2
start "" "%RTL_INTEGRATION_PYTHON%" -B "%~dp0console.py"
