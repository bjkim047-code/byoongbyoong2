import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from progressboard import autostart


def test_build_command_for_frozen_exe_is_just_the_executable():
    command = autostart.build_command(executable=r"C:\apps\progressboard.exe", frozen=True)
    assert command == r'"C:\apps\progressboard.exe"'


def test_build_command_for_script_includes_interpreter_and_run_py():
    run_py = Path(r"C:\code\progressboard\run.py")
    command = autostart.build_command(
        executable=r"C:\Python\pythonw.exe", frozen=False, run_py=run_py
    )
    assert command == r'"C:\Python\pythonw.exe" "C:\code\progressboard\run.py"'


def test_is_supported_reflects_platform(monkeypatch):
    monkeypatch.setattr(autostart.sys, "platform", "win32")
    assert autostart.is_supported() is True
    monkeypatch.setattr(autostart.sys, "platform", "linux")
    assert autostart.is_supported() is False


def test_unsupported_platform_calls_are_safe_no_ops(monkeypatch):
    monkeypatch.setattr(autostart.sys, "platform", "linux")
    assert autostart.is_enabled() is False
    autostart.set_enabled(True)  # 예외 없이 그냥 아무 일도 하지 않아야 한다.
