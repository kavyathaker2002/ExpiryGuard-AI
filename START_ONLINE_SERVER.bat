@echo off
title ExpiryGuard AI - Online Cloud Server
echo ========================================================
echo       Starting ExpiryGuard AI Online Cloud Server
echo ========================================================
echo.

cd /d "%~dp0"

echo 1. Starting Cloudflare Global Tunnel (Mobile Data / Any Wi-Fi)...
start "Cloudflare Tunnel" /min "C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel --url https://localhost:5000 --no-tls-verify

echo 2. Starting Flask Server with SSL...
"C:\Users\intel\anaconda3\python.exe" run.py --ssl

pause
