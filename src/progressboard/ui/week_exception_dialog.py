"""'예외 시간표 설정' 다이얼로그.

특정 주차에만 적용되는 시간표를 따로 등록한다. 시험 기간, 휴업일 등으로
그 주만 시간표가 달라질 때 사용한다. 예외가 없는 주차는 계속 기본
시간표를 따른다.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional

from ..models import Settings
from ..scheduler import Week
from .timetable_grid import TimetableGrid


class WeekExceptionDialog(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Misc,
        settings: Settings,
        weeks: list[Week],
        base_timetable: dict,
        week_exceptions: dict,
        on_save: Callable[[int, Optional[dict]], None],
    ):
        super().__init__(parent)
        self.title("예외 시간표 설정")
        self.geometry("640x460")
        self.minsize(600, 420)
        self.transient(parent)
        self.grab_set()

        self._settings = settings
        self._weeks = weeks
        self._base_timetable = base_timetable
        self._week_exceptions = dict(week_exceptions)
        self._on_save = on_save
        self._grid: TimetableGrid | None = None
        self._selected_week: Week | None = None

        ttk.Label(
            self,
            text="예외를 등록할 주차를 선택한 뒤 그 주만의 시간표를 입력하고 저장하세요.",
            foreground="gray",
            wraplength=600,
        ).pack(anchor="w", padx=10, pady=(10, 4))

        body = ttk.Frame(self, padding=(10, 0, 10, 10))
        body.pack(fill="both", expand=True)

        left = ttk.Frame(body, width=170)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        ttk.Label(left, text="주 / 기간 (● = 예외 등록됨)", foreground="gray").pack(anchor="w")
        columns = ("week", "period", "exc")
        self._tree = ttk.Treeview(
            left, columns=columns, show="headings", selectmode="browse", height=16
        )
        self._tree.heading("week", text="주")
        self._tree.heading("period", text="기간")
        self._tree.heading("exc", text="예외")
        self._tree.column("week", width=32, anchor="center")
        self._tree.column("period", width=100, anchor="center")
        self._tree.column("exc", width=24, anchor="center")
        self._tree.pack(fill="y", expand=True, pady=(2, 0))
        self._tree.bind("<<TreeviewSelect>>", self._on_week_selected)

        right = ttk.Frame(body, padding=(12, 0, 0, 0))
        right.pack(side="left", fill="both", expand=True)

        self._grid_container = ttk.Frame(right)
        self._grid_container.pack(fill="both", expand=True)
        self._placeholder = ttk.Label(
            self._grid_container, text="왼쪽에서 주차를 선택하세요.", foreground="gray"
        )
        self._placeholder.pack(anchor="w", pady=20)

        btns = ttk.Frame(right)
        btns.pack(anchor="w", pady=(8, 0))
        ttk.Button(btns, text="이 주 예외로 저장", command=self._save_current).pack(
            side="left", padx=(0, 4)
        )
        ttk.Button(btns, text="예외 해제(기본 시간표 사용)", command=self._clear_current).pack(
            side="left", padx=4
        )
        ttk.Button(self, text="닫기", command=self.destroy).pack(pady=(0, 10))

        self._refresh_week_list()
        self.bind("<Escape>", lambda _e: self.destroy())

    # -- week list --------------------------------------------------------
    def _refresh_week_list(self) -> None:
        selected = self._tree.selection()
        selected_iid = selected[0] if selected else None
        self._tree.delete(*self._tree.get_children())
        for week in self._weeks:
            has_exception = str(week.number) in self._week_exceptions
            self._tree.insert(
                "", "end", iid=str(week.number), values=(week.number, week.label, "●" if has_exception else "")
            )
        if selected_iid and self._tree.exists(selected_iid):
            self._tree.selection_set(selected_iid)

    def _on_week_selected(self, _event=None) -> None:
        selection = self._tree.selection()
        if not selection:
            return
        week_number = int(selection[0])
        self._selected_week = next(w for w in self._weeks if w.number == week_number)
        self._show_grid_for_selected_week()

    def _show_grid_for_selected_week(self) -> None:
        for child in self._grid_container.winfo_children():
            child.destroy()
        if self._selected_week is None:
            return
        initial = self._week_exceptions.get(str(self._selected_week.number), self._base_timetable)
        self._grid = TimetableGrid(self._grid_container, self._settings, initial)
        self._grid.pack(anchor="w")

    # -- save/clear ---------------------------------------------------------
    def _save_current(self) -> None:
        if self._selected_week is None or self._grid is None:
            messagebox.showinfo("안내", "먼저 왼쪽에서 주차를 선택하세요.", parent=self)
            return
        timetable = self._grid.get_timetable()
        self._week_exceptions[str(self._selected_week.number)] = timetable
        self._on_save(self._selected_week.number, timetable)
        self._refresh_week_list()

    def _clear_current(self) -> None:
        if self._selected_week is None:
            messagebox.showinfo("안내", "먼저 왼쪽에서 주차를 선택하세요.", parent=self)
            return
        self._week_exceptions.pop(str(self._selected_week.number), None)
        self._on_save(self._selected_week.number, None)
        self._refresh_week_list()
        self._show_grid_for_selected_week()
