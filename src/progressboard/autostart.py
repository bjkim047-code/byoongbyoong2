"""윈도우 로그인 시 자동 실행 등록/해제.

레지스트리(HKEY_CURRENT_USER\\...\\Run)에 값을 넣고 빼는 방식이라 Windows
에서만 동작한다. 다른 OS에서는 아무 것도 하지 않는 안전한 no-op이다.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

APP_REG_NAME = "progressboard"


def is_supported() -> bool:
    return sys.platform == "win32"


def build_command(executable: str, frozen: bool, run_py: Optional[Path] = None) -> str:
    """실제로 레지스트리에 넣을 실행 커맨드를 만든다.

    PyInstaller로 exe를 빌드해 실행 중이면 그 exe 경로 하나면 되고,
    `python run.py`로 개발 중 실행한 경우에는 파이썬 인터프리터 경로와
    run.py 경로를 함께 넣어야 한다.
    """

    if frozen:
        return f'"{executable}"'
    run_py = run_py or Path(__file__).resolve().parents[2] / "run.py"
    return f'"{executable}" "{run_py}"'


def current_command() -> str:
    return build_command(
        executable=sys.executable,
        frozen=bool(getattr(sys, "frozen", False)),
    )


def is_enabled() -> bool:
    if not is_supported():
        return False
    import winreg

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"
        ) as key:
            winreg.QueryValueEx(key, APP_REG_NAME)
        return True
    except FileNotFoundError:
        return False


def set_enabled(enabled: bool) -> None:
    if not is_supported():
        return
    import winreg

    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0,
        winreg.KEY_SET_VALUE,
    ) as key:
        if enabled:
            winreg.SetValueEx(key, APP_REG_NAME, 0, winreg.REG_SZ, current_command())
        else:
            try:
                winreg.DeleteValue(key, APP_REG_NAME)
            except FileNotFoundError:
                pass
