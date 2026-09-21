"""앱 실행 진입점."""

from __future__ import annotations

from .ui.main_window import MainWindow


def run() -> None:
    window = MainWindow()
    window.mainloop()
