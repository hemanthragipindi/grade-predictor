@echo off
setlocal
cd /d "%~dp0"

echo [1/4] Clearing high-priority ports...
taskkill /F /IM python.exe /T 2>nul
taskkill /F /IM pythonw.exe /T 2>nul

echo [2/4] Initializing Database ^& Brain...
if exist "venv\Scripts\python.exe" (
    start /min "" "venv\Scripts\python.exe" app.py
) else (
    echo Error: Virtual environment (venv) not found.
    pause
    exit /b
)

echo [3/4] Warming up the intelligence engine...
FOR /L %%i IN (1,1,10) DO (
    <nul set /p "=. "
    timeout /t 1 /nobreak >nul
)
echo Done.

echo [4/4] Projecting Interface Synthesis...
set APP_URL=http://127.0.0.1:8000/

:: Launch browser
if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (
    start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --app=%APP_URL%
) else (
    start %APP_URL%
)

echo.
echo [SYSTEM ACTIVE] Nexora is running on Port 8000.
echo This window will close automatically.
timeout /t 5 >nul
exit
