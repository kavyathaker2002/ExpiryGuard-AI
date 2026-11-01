@echo off
title ExpiryGuard AI - Online Cloud Server
echo ========================================================
echo       Starting ExpiryGuard AI Online Cloud Server
echo ========================================================
echo.

cd /d "%~dp0"

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PY_CMD=python
) else (
    set PY_CMD=py
)

if exist "C:\Program Files (x86)\cloudflared\cloudflared.exe" (
    echo 1. Starting Cloudflare Global Tunnel (Mobile Data / Any Wi-Fi)...
    start "Cloudflare Tunnel" /min "C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel --url https://localhost:5000 --no-tls-verify
)

echo 2. Starting Flask Server with SSL...
%PY_CMD% run.py --ssl

pause
