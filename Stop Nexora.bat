@echo off
setlocal
cd /d "%~dp0"

echo [NEXORA PLATFORM] Stopping System...

:: Kill the pythonw.exe or python.exe process running our app
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM pythonw.exe /T >nul 2>&1

echo [NEXORA PLATFORM] Sessions Terminated.
echo ------------------------------------------
echo Status: Offline
echo ------------------------------------------
timeout /t 2 /nobreak >nul
exit
