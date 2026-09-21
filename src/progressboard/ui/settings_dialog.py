"""'기본 설정' 다이얼로그.

과목명, 반 목록, 주당 시수, 총 차시 수, 학기(주차) 시작일과 표시할 주 수를 입력받는다.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from ..models import Settings
from ..scheduler import parse_date


class SettingsDialog(tk.Toplevel):
    def __init__(self, parent: tk.Misc, settings: Settings, on_save: Callable[[Settings], None]):
        super().__init__(parent)
        self.title("기본 설정")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._on_save = on_save

        self._subject = tk.StringVar(value=settings.subject_name)
        self._classes = tk.StringVar(value=", ".join(settings.classes))
        self._periods_per_week = tk.StringVar(value=str(settings.periods_per_week))
        self._periods_per_day = tk.StringVar(value=str(settings.periods_per_day))
        self._total_lessons = tk.StringVar(value=str(settings.total_lessons))
        self._semester_start = tk.StringVar(value=settings.semester_start)
        self._num_weeks = tk.StringVar(value=str(settings.num_weeks))

        pad = {"padx": 10, "pady": 6}
        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)

        row = 0
        ttk.Label(body, text="과목명").grid(row=row, column=0, sticky="w", **pad)
        ttk.Entry(body, textvariable=self._subject, width=30).grid(row=row, column=1, **pad)

        row += 1
        ttk.Label(body, text="담당 반 목록").grid(row=row, column=0, sticky="w", **pad)
        ttk.Entry(body, textvariable=self._classes, width=30).grid(row=row, column=1, **pad)
        ttk.Label(body, text="(쉼표로 구분, 예: 2-1, 2-2, ...)", foreground="gray").grid(
            row=row + 1, column=1, sticky="w", padx=10
        )

        row += 2
        ttk.Label(body, text="반별 주당 시수").grid(row=row, column=0, sticky="w", **pad)
        ttk.Entry(body, textvariable=self._periods_per_week, width=8).grid(
            row=row, column=1, sticky="w", **pad
        )

        row += 1
        ttk.Label(body, text="하루 최대 교시").grid(row=row, column=0, sticky="w", **pad)
        ttk.Entry(body, textvariable=self._periods_per_day, width=8).grid(
            row=row, column=1, sticky="w", **pad
        )

        row += 1
        ttk.Label(body, text="총 차시 수(진도표 칸 수)").grid(row=row, column=0, sticky="w", **pad)
        ttk.Entry(body, textvariable=self._total_lessons, width=8).grid(
            row=row, column=1, sticky="w", **pad
        )
        ttk.Label(
            body, text="(예: 남은 8주 x 주당 2시수 = 16)", foreground="gray"
        ).grid(row=row + 1, column=1, sticky="w", padx=10)

        row += 2
        ttk.Label(body, text="1주차 시작일(월요일)").grid(row=row, column=0, sticky="w", **pad)
        ttk.Entry(body, textvariable=self._semester_start, width=14).grid(
            row=row, column=1, sticky="w", **pad
        )
        ttk.Label(body, text="YYYY-MM-DD", foreground="gray").grid(
            row=row + 1, column=1, sticky="w", padx=10
        )

        row += 2
        ttk.Label(body, text="표시할 주차 수").grid(row=row, column=0, sticky="w", **pad)
        ttk.Entry(body, textvariable=self._num_weeks, width=8).grid(
            row=row, column=1, sticky="w", **pad
        )

        row += 1
        btns = ttk.Frame(body)
        btns.grid(row=row, column=0, columnspan=2, pady=(12, 10))
        ttk.Button(btns, text="저장", command=self._save).pack(side="left", padx=4)
        ttk.Button(btns, text="취소", command=self.destroy).pack(side="left", padx=4)

        self.bind("<Escape>", lambda _e: self.destroy())

    def _save(self) -> None:
        classes = [c.strip() for c in self._classes.get().split(",") if c.strip()]
        if not classes:
            messagebox.showerror("입력 오류", "담당 반을 한 개 이상 입력하세요.", parent=self)
            return

        try:
            periods_per_week = int(self._periods_per_week.get())
            periods_per_day = int(self._periods_per_day.get())
            total_lessons = int(self._total_lessons.get())
            num_weeks = int(self._num_weeks.get())
        except ValueError:
            messagebox.showerror("입력 오류", "시수/교시/차시/주차 수는 숫자로 입력하세요.", parent=self)
            return

        if self._semester_start.get().strip() and parse_date(self._semester_start.get()) is None:
            messagebox.showerror(
                "입력 오류", "시작일은 YYYY-MM-DD 형식으로 입력하세요. (예: 2026-09-21)", parent=self
            )
            return

        settings = Settings(
            subject_name=self._subject.get().strip() or "과목",
            classes=classes,
            periods_per_week=max(periods_per_week, 1),
            periods_per_day=max(periods_per_day, 1),
            total_lessons=max(total_lessons, 0),
            semester_start=self._semester_start.get().strip(),
            num_weeks=max(num_weeks, 1),
        )
        self._on_save(settings)
        self.destroy()
