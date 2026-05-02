@echo off
echo Nexora Maintenance: Cleaning up old file structure...

:: Remove redundant root files if they still exist
if exist "app.py" (
    echo [CLEANUP] Removing legacy root files...
    del "app.py" "models.py" "database.py" "intelligence.py" "config.py" "migrate_db.py" "check_db.py" "fix_db.py" "update_mth165.py" "update_phy110.py" "sync_transcript.py" "debug_score.py" "exam_practice_helper.py" "notifications.py" "migrate_sem1.py" 2>nul
)

:: Remove redundant root folders
if exist "templates" rmdir /s /q "templates"
if exist "static" rmdir /s /q "static"
if exist "routes" rmdir /s /q "routes"
if exist "logic" rmdir /s /q "logic"
if exist "instance" rmdir /s /q "instance"

echo [SUCCESS] Project structure is now clean.

:: Activate virtual environment
if not exist "venv" (
    echo [ERROR] Virtual environment not found. Please create it first.
    pause
    exit
)

call venv\Scripts\activate.bat

echo [INFO] Synchronizing libraries with requirements.txt...
pip install -r requirements.txt

echo Starting Nexora Grade Predictor...

:: Start backend
cd backend
python app.py

pause
