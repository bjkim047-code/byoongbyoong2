"""'기본 시간표 설정' 다이얼로그.

요일 x 교시 표에 어느 교시에 어느 반이 들어오는지 지정한다.
여기서 입력한 시간표는 모든 주차에 공통으로 적용된다.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from ..models import DAYS, DAY_LABELS, Settings


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
        self._settings = settings
        self._vars: dict[tuple[str, int], tk.StringVar] = {}

        ttk.Label(
            self,
            text="교시별로 들어가는 반을 선택하세요. (해당 교시에 수업이 없으면 비워두세요)",
            foreground="gray",
        ).grid(row=0, column=0, columnspan=len(DAYS) + 1, sticky="w", padx=10, pady=(10, 4))

        table = ttk.Frame(self, padding=10)
        table.grid(row=1, column=0, columnspan=len(DAYS) + 1)

        ttk.Label(table, text="").grid(row=0, column=0)
        for col, day in enumerate(DAYS, start=1):
            ttk.Label(table, text=DAY_LABELS[day], font=("", 10, "bold")).grid(
                row=0, column=col, padx=6, pady=4
            )

        class_choices = [""] + list(settings.classes)
        for period in range(1, settings.periods_per_day + 1):
            ttk.Label(table, text=f"{period}교시").grid(row=period, column=0, padx=6, pady=3, sticky="e")
            for col, day in enumerate(DAYS, start=1):
                current = str(timetable.get(day, {}).get(str(period), ""))
                var = tk.StringVar(value=current)
                self._vars[(day, period)] = var
                combo = ttk.Combobox(
                    table, textvariable=var, values=class_choices, width=8, state="readonly"
                )
                combo.grid(row=period, column=col, padx=4, pady=3)

        btns = ttk.Frame(self)
        btns.grid(row=2, column=0, columnspan=len(DAYS) + 1, pady=(4, 10))
        ttk.Button(btns, text="저장", command=self._save).pack(side="left", padx=4)
        ttk.Button(btns, text="취소", command=self.destroy).pack(side="left", padx=4)

        self.bind("<Escape>", lambda _e: self.destroy())

    def _save(self) -> None:
        timetable: dict = {day: {} for day in DAYS}
        for (day, period), var in self._vars.items():
            value = var.get().strip()
            if value:
                timetable[day][str(period)] = value
        self._on_save(timetable)
        self.destroy()
