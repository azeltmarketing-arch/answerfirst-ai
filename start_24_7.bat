@echo off
setlocal enabledelayedexpansion

:: AnswerFirst AI - 24/7 Server Launcher
:: Starts CRM, Dashboard, Portal, Unified, and Cloudflare Tunnels

echo [*] Starting AnswerFirst AI servers...

:: Start CRM
start "CRM Server" /MIN cmd /c "cd /d C:\Users\azelt\answerfirst-ai\crm && python app.py"

:: Start Dashboard
start "Dashboard" /MIN cmd /c "cd /d C:\Users\azelt\answerfirst-ai\dashboard && python -m http.server 8080"

:: Start Portal
start "Portal Server" /MIN cmd /c "cd /d C:\Users\azelt\answerfirst-ai\portal && python app.py"

:: Start Unified
start "Unified Server" /MIN cmd /c "cd /d C:\Users\azelt\answerfirst-ai\unified && python app.py"

:: Wait for servers to initialize
timeout /t 5 /nobreak >nul

:: Start Cloudflare Tunnels for public access
start "Tunnel CRM" /MIN cmd /c "cloudflared tunnel --url http://127.0.0.1:5050"
start "Tunnel Dashboard" /MIN cmd /c "cloudflared tunnel --url http://127.0.0.1:8080"
start "Tunnel Unified" /MIN cmd /c "cloudflared tunnel --url http://127.0.0.1:5070"

echo [+] All servers started
echo [*] Manager Hub: http://localhost:8080
echo [*] CRM API: http://127.0.0.1:5050
echo [*] Portal: http://127.0.0.1:5060
echo [*] Unified: http://127.0.0.1:5070
echo.
echo [*] Public tunnels are starting... Check the minimized windows for URLs.
pause
