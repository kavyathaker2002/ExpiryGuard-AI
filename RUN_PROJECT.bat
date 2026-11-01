@echo off
title ExpiryGuard AI - Startup Wizard
color 0A
cd /d "%~dp0"

echo ======================================================================
echo           🛡️  EXPIRYGUARD AI — ONE-CLICK RUNNER  🛡️
echo ======================================================================
echo.

:: 1. Detect Python
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PY_CMD=python
    goto PYTHON_FOUND
)

where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PY_CMD=py
    goto PYTHON_FOUND
)

color 0C
echo [ERROR] Python is not installed or not added to your system PATH!
echo.
echo To fix this:
echo  1. Download Python from: https://www.python.org/downloads/
echo  2. IMPORTANT: When installing, CHECK the box: "Add python.exe to PATH"
echo  3. Restart your laptop and double-click this file again.
echo.
echo ======================================================================
pause
exit /b 1

:PYTHON_FOUND
echo [OK] Found Python interpreter: %PY_CMD%
%PY_CMD% --version
echo.

:: 2. Check if required dependencies are installed
echo Checking required libraries...
%PY_CMD% -c "import flask, sklearn, pandas, PIL, qrcode" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Installing required libraries (this only happens on the first run)...
    echo.
    %PY_CMD% -m pip install --upgrade pip
    %PY_CMD% -m pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        color 0C
        echo.
        echo [ERROR] Failed to install libraries. Please check your internet connection.
        echo.
        pause
        exit /b 1
    )
)

echo [OK] All libraries are installed!
echo.
echo ======================================================================
echo   Starting ExpiryGuard AI Server...
echo   Open in browser: http://localhost:5000
echo   Default Login:
echo      Username: admin
echo      Password: admin 123
echo ======================================================================
echo.

:: Launch browser in 2 seconds in background
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:5000"

:: Start Flask app
%PY_CMD% run.py

if %ERRORLEVEL% NEQ 0 (
    color 0C
    echo.
    echo [ERROR] The server stopped unexpectedly.
    echo.
)
pause
