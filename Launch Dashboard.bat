@echo off
setlocal
cd /d "%~dp0"

echo [SYSTEM] Waking up Nexora...
echo ------------------------------------------

:: 1. Force close any stuck Python processes
taskkill /F /IM python.exe /T 2>nul
taskkill /F /IM pythonw.exe /T 2>nul

:: 2. Start the server (minimized)
echo [1/2] Powering up the Intelligence Engine...
if exist "venv\Scripts\python.exe" (
    start /min "" "venv\Scripts\python.exe" app.py
) else (
    echo [ERROR] Virtual environment not found. Please run: python -m venv venv
    pause
    exit /b
)

:: 3. Wait 2 seconds for server to bind
echo [2/2] Opening Dashboard Interface...
timeout /t 2 /nobreak >nul

:: 4. Open the specific Dashboard URL
start http://127.0.0.1:8000/

echo ------------------------------------------
echo [ACTIVE] Dashboard is now open in your browser.
echo Port: 8000 | Status: Online
timeout /t 3 >nul
exit
