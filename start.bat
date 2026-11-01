@echo off
title ExpiryGuard AI - Gupta Chaat & Stores
color 0A
cd /d "%~dp0"

echo ===============================================================
echo   Starting ExpiryGuard AI Server...
echo ===============================================================
echo.

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PY_CMD=python
    goto RUN
)
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PY_CMD=py
    goto RUN
)

color 0C
echo [ERROR] Python is not installed or not in PATH!
echo Download from https://www.python.org/downloads/ and check "Add Python to PATH".
pause
exit /b 1

:RUN
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:5000"
%PY_CMD% run.py
pause
