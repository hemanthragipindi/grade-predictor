@echo off
setlocal
cd /d "%~dp0"

echo.
echo  ==============================================
echo     D I R E C T   L A U N C H   ( DEBUG MODE )
echo  ==============================================
echo.

echo [1/3] Clearing processes...
taskkill /F /IM python.exe /T 2>nul
taskkill /F /IM pythonw.exe /T 2>nul

echo [2/3] Activating Virtual Environment...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo [ERROR] Virtual Environment Not Found!
    pause
    exit /b
)

echo [3/3] Launching Nexora Server (PORT 8000)...
echo ------------------------------------------
echo.

:: Run with explicit host and port override if needed (though app.run already has it)
python app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Server died with code %ERRORLEVEL%.
)

echo.
echo ------------------------------------------
echo The window will stay open for debugging.
pause
