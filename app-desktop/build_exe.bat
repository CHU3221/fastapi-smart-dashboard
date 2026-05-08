@echo off
echo Installing required libraries
pip install fastapi uvicorn httpx pydantic icalendar recurring-ical_events pyinstaller

echo.
echo Building Standalone EXE file
python -m PyInstaller --onefile --add-data "static;static" main.py

echo.
echo ======================================================
echo Build Complete. Check the 'dist' folder for main.exe.
echo ======================================================
pause