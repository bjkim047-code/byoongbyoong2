"""'기본 시간표 설정' 다이얼로그.

요일 x 교시 표에 어느 교시에 어느 반이 들어오는지 지정한다.
여기서 입력한 시간표는 예외 시간표가 없는 모든 주차에 공통으로 적용된다.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from ..models import Settings
from .timetable_grid import TimetableGrid


class TimetableDialog(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Misc,
        settings: Settings,
        timetable: dict,
        on_save: Callable[[dict], None],
    ):
        super().__init__(parent)
        self.title("기본 시간표 설정")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._on_save = on_save

        ttk.Label(
            self,
            text="교시별로 들어가는 반을 선택하세요. (해당 교시에 수업이 없으면 비워두세요)",
            foreground="gray",
        ).pack(anchor="w", padx=10, pady=(10, 4))

        self._grid = TimetableGrid(self, settings, timetable)
        self._grid.pack(padx=10, pady=(0, 4))

        btns = ttk.Frame(self)
        btns.pack(pady=(4, 10))
        ttk.Button(btns, text="저장", command=self._save).pack(side="left", padx=4)
        ttk.Button(btns, text="취소", command=self.destroy).pack(side="left", padx=4)

        self.bind("<Escape>", lambda _e: self.destroy())

    def _save(self) -> None:
        self._on_save(self._grid.get_timetable())
        self.destroy()
