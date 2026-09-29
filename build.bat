@echo off
echo progressboard.exe 빌드를 시작합니다...
echo.

python -m pip install --upgrade pyinstaller
if errorlevel 1 (
    echo.
    echo [오류] pyinstaller 설치에 실패했습니다. 파이썬이 설치돼 있는지,
    echo        "python" 명령이 동작하는지 확인해주세요.
    pause
    exit /b 1
)

python -m PyInstaller --onefile --windowed --name progressboard run.py
if errorlevel 1 (
    echo.
    echo [오류] 빌드 중 문제가 발생했습니다. 위 메시지를 확인해주세요.
    pause
    exit /b 1
)

echo.
echo 빌드가 끝났습니다. dist\progressboard.exe 파일을 확인하세요.
pause
