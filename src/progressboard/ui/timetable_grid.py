"""요일 x 교시 시간표를 입력받는 그리드 위젯.

'기본 시간표 설정'과 '예외 시간표 설정'에서 공통으로 쓴다.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ..models import DAYS, DAY_LABELS, Settings


class TimetableGrid(ttk.Frame):
    def __init__(self, parent: tk.Misc, settings: Settings, initial: dict | None = None):
        super().__init__(parent)
        self._settings = settings
        self._vars: dict[tuple[str, int], tk.StringVar] = {}
        self._render(initial or {})

    def _render(self, timetable: dict) -> None:
        class_choices = [""] + list(self._settings.classes)

        ttk.Label(self, text="").grid(row=0, column=0)
        for col, day in enumerate(DAYS, start=1):
            ttk.Label(self, text=DAY_LABELS[day], font=("", 10, "bold")).grid(
                row=0, column=col, padx=6, pady=4
            )

        for period in range(1, self._settings.periods_per_day + 1):
            ttk.Label(self, text=f"{period}교시").grid(
                row=period, column=0, padx=6, pady=3, sticky="e"
            )
            for col, day in enumerate(DAYS, start=1):
                current = str(timetable.get(day, {}).get(str(period), ""))
                var = tk.StringVar(value=current)
                self._vars[(day, period)] = var
                combo = ttk.Combobox(
                    self, textvariable=var, values=class_choices, width=8, state="readonly"
                )
                combo.grid(row=period, column=col, padx=4, pady=3)

        clear_row = self._settings.periods_per_day + 1
        ttk.Label(self, text="요일 지우기", foreground="gray").grid(
            row=clear_row, column=0, padx=6, pady=(8, 4), sticky="e"
        )
        for col, day in enumerate(DAYS, start=1):
            ttk.Button(
                self, text="지우기", width=6, command=lambda d=day: self._clear_day(d)
            ).grid(row=clear_row, column=col, padx=4, pady=(8, 4))

    def _clear_day(self, day: str) -> None:
        for (var_day, _period), var in self._vars.items():
            if var_day == day:
                var.set("")

    def reload(self, timetable: dict) -> None:
        for child in self.winfo_children():
            child.destroy()
        self._vars = {}
        self._render(timetable)

    def get_timetable(self) -> dict:
        timetable: dict = {day: {} for day in DAYS}
        for (day, period), var in self._vars.items():
            value = var.get().strip()
            if value:
                timetable[day][str(period)] = value
        return timetable
