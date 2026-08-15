@echo off
setlocal

cd /d "%~dp0"

echo Starting AI Sentence Builder Booth Demo...
python app.py

echo.
echo Demo has finished. You can close this window.
pause

endlocal
