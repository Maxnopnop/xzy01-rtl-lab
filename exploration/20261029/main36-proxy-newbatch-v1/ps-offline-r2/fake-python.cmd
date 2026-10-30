@echo off
if defined OPENROUTER_API_KEY (echo %~3 KEY_PRESENT>> "%TRACE_FILE%") else (echo %~3 KEY_ABSENT>> "%TRACE_FILE%")
exit /b 0
