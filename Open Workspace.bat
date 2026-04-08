@echo off
setlocal
cd /d "%~dp0"

echo [WORKSPACE] Initializing Development Environment...
echo ------------------------------------------

:: Open Windows Explorer to the root folder
echo [1/3] Opening Project Root...
start explorer .

:: Open key backend and frontend files in the default editor
echo [2/3] Accessing Core Engine & Interface...
start "" "app.py"
start "" "templates\dashboard.html"
start "" "templates\layout.html"
start "" "static\style.css"

:: Open important logic units
echo [3/3] Opening Intelligence Units...
start "" "intelligence.py"
start "" "models.py"

echo ------------------------------------------
echo [STATUS] Project files are now open for editing.
echo This window will close automatically.
timeout /t 3 >nul
exit
