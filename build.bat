@echo off
echo Building progressboard.exe ...
echo.

python -m pip install --upgrade pyinstaller
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install pyinstaller.
    echo         Make sure Python is installed and the "python" command works.
    pause
    exit /b 1
)

python -m PyInstaller --onefile --windowed --name progressboard --paths src run.py
if errorlevel 1 (
    echo.
    echo [ERROR] Build failed. See the messages above for details.
    pause
    exit /b 1
)

echo.
echo Done. Check dist\progressboard.exe
pause
