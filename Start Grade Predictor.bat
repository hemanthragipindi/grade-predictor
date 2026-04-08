@echo off
echo Starting Grade Predictor...
echo Please wait a moment while the server starts up.

:: Activate the virtual environment
call venv\Scripts\activate.bat

:: Open the default web browser to the local app address
start http://127.0.0.1:5000/

:: Start the python application
python app.py

pause
