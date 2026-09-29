"""주차별 시간표에 반별 예상 진도를 표시하는 메인 창."""

from __future__ import annotations

import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

from .. import autostart, progress, storage
from ..models import DAYS, DAY_LABELS
from ..progress import STATUS_DONE, STATUS_ICONS, STATUS_SHORT, STATUS_SKIPPED
from ..scheduler import Week, build_weeks, current_week_index
from .lessons_dialog import LessonsDialog
from .settings_dialog import SettingsDialog
from .status_dialog import StatusChoiceDialog
from .timetable_dialog import TimetableDialog
from .week_exception_dialog import WeekExceptionDialog

WINDOW_WIDTH = 900
WINDOW_HEIGHT = 560
CELL_ROW_MINSIZE = 60  # 진도 제목이 1줄이든 2줄이든 칸 크기가 흔들리지 않도록 고정

_TODAY_BG = "#eaf6ea"
_DUE_BG = "#fff3d6"
_DUE_BORDER = "#d9932a"
_DONE_FG = "#6b6b6b"
_SKIPPED_FG = "#b23b3b"
_NO_CLASS_BG = "#f3f3f3"


class MainWindow(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.state = storage.load()
        self.weeks: list[Week] = []
        self.selected_week_index = 0

        self.title(f"{self.state.settings.subject_name} 진도표 — progressboard")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(720, 420)

        self._topmost = tk.BooleanVar(value=False)
        self._autostart = tk.BooleanVar(value=autostart.is_enabled())

        self._build_menu()
        self._build_layout()
        self._reload_weeks()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # -- menu -----------------------------------------------------------
    def _build_menu(self) -> None:
        menubar = tk.Menu(self)
        settings_menu = tk.Menu(menubar, tearoff=False)
        settings_menu.add_command(label="기본 설정", command=self.open_settings_dialog)
        settings_menu.add_command(label="기본 시간표 설정", command=self.open_timetable_dialog)
        settings_menu.add_command(label="예외 시간표 설정", command=self.open_week_exception_dialog)
        settings_menu.add_command(label="진도 설정", command=self.open_lessons_dialog)
        menubar.add_cascade(label="시간표 설정", menu=settings_menu)
        self.configure(menu=menubar)

    # -- layout -----------------------------------------------------------
    def _build_layout(self) -> None:
        header = ttk.Frame(self, padding=(10, 8))
        header.pack(fill="x")

        self._subject_label = ttk.Label(header, text="", font=("", 12, "bold"))
        self._subject_label.pack(side="left")

        ttk.Checkbutton(
            header, text="항상 위", variable=self._topmost, command=self._apply_topmost
        ).pack(side="right")

        ttk.Checkbutton(
            header,
            text="윈도우 시작 시 자동 실행",
            variable=self._autostart,
            command=self._apply_autostart,
            state="normal" if autostart.is_supported() else "disabled",
        ).pack(side="right", padx=(0, 10))

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        left = ttk.Frame(body, width=170)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        ttk.Label(left, text="주 / 기간", foreground="gray").pack(anchor="w")
        columns = ("week", "period")
        self._week_tree = ttk.Treeview(
            left, columns=columns, show="headings", selectmode="browse", height=20
        )
        self._week_tree.heading("week", text="주")
        self._week_tree.heading("period", text="기간")
        self._week_tree.column("week", width=36, anchor="center")
        self._week_tree.column("period", width=110, anchor="center")
        self._week_tree.pack(fill="y", expand=True, pady=(2, 0))
        self._week_tree.bind("<<TreeviewSelect>>", self._on_week_selected)

        right = ttk.Frame(body, padding=(12, 0, 0, 0))
        right.pack(side="left", fill="both", expand=True)

        self._grid_frame = ttk.Frame(right)
        self._grid_frame.pack(fill="both", expand=True)

    def _apply_topmost(self) -> None:
        self.attributes("-topmost", self._topmost.get())

    def _apply_autostart(self) -> None:
        try:
            autostart.set_enabled(self._autostart.get())
        except OSError as exc:
            messagebox.showerror("자동 실행 설정 실패", str(exc), parent=self)
            self._autostart.set(not self._autostart.get())

    # -- data ---------------------------------------------------------------
    def _save(self) -> None:
        storage.save(self.state)

    def _reload_weeks(self) -> None:
        settings = self.state.settings
        self.weeks = build_weeks(settings.semester_start, settings.num_weeks)
        self.selected_week_index = current_week_index(self.weeks)
        self._refresh_week_list()
        self._refresh_all()

    def _refresh_week_list(self) -> None:
        self._week_tree.delete(*self._week_tree.get_children())
        for i, week in enumerate(self.weeks):
            self._week_tree.insert("", "end", iid=str(i), values=(week.number, week.label))
        if self.weeks:
            index = max(min(self.selected_week_index, len(self.weeks) - 1), 0)
            self.selected_week_index = index
            self._week_tree.selection_set(str(index))
            self._week_tree.see(str(index))

    def _on_week_selected(self, _event=None) -> None:
        selection = self._week_tree.selection()
        if not selection:
            return
        self.selected_week_index = int(selection[0])
        self._refresh_grid()

    def _refresh_all(self) -> None:
        settings = self.state.settings
        self.title(f"{settings.subject_name} 진도표 — progressboard")
        self._subject_label.configure(text=f"{settings.subject_name} 이번 주 진도표")
        self._refresh_grid()

    # -- timetable grid -------------------------------------------------
    def _refresh_grid(self) -> None:
        for child in self._grid_frame.winfo_children():
            child.destroy()

        if not self.weeks:
            ttk.Label(
                self._grid_frame,
                text="표시할 주차가 없습니다. '시간표 설정 > 기본 설정'에서 시작일과 주차 수를 입력하세요.",
                foreground="gray",
            ).pack(anchor="w", padx=4, pady=10)
            return

        week = self.weeks[self.selected_week_index]
        settings = self.state.settings
        today = date.today()

        for col in range(len(DAYS) + 1):
            self._grid_frame.grid_columnconfigure(col, weight=0 if col == 0 else 1, uniform="day")

        ttk.Label(self._grid_frame, text="").grid(row=0, column=0, padx=4, pady=4)
        for col, day in enumerate(DAYS, start=1):
            day_date = week.day_date(day)
            is_today = day_date == today
            header = tk.Frame(
                self._grid_frame,
                bg=_TODAY_BG if is_today else self.cget("bg"),
                highlightbackground="#bbbbbb",
                highlightthickness=1,
            )
            header.grid(row=0, column=col, sticky="nsew", padx=2, pady=2)
            tk.Label(
                header,
                text=f"{DAY_LABELS[day]} ({day_date.strftime('%m/%d')})",
                bg=header["bg"],
                font=("", 12),
            ).pack(padx=6, pady=7)

        for period in range(1, settings.periods_per_day + 1):
            ttk.Label(self._grid_frame, text=f"{period}교시", foreground="gray").grid(
                row=period, column=0, padx=4, pady=2, sticky="e"
            )
            for col, day in enumerate(DAYS, start=1):
                self._build_cell(day, period, week)

        self._grid_frame.grid_rowconfigure(0, weight=0)
        for row in range(1, settings.periods_per_day + 1):
            self._grid_frame.grid_rowconfigure(
                row, weight=1, uniform="period_row", minsize=CELL_ROW_MINSIZE
            )

    def _build_cell(self, day: str, period: int, week: Week) -> None:
        settings = self.state.settings
        timetable = progress.effective_timetable(self.state, week.number)
        class_name = settings.classes and timetable.get(day, {}).get(str(period))
        slot_date = week.day_date(day)
        today = date.today()

        if not class_name:
            cell = tk.Frame(
                self._grid_frame, bg=_NO_CLASS_BG, highlightbackground="#dddddd", highlightthickness=1
            )
            cell.grid(row=period, column=DAYS.index(day) + 1, sticky="nsew", padx=2, pady=2)
            return

        lesson = progress.expected_lesson(self.state, week.number, day, period, class_name)
        status = progress.slot_status(self.state, slot_date, period, class_name)
        due = status is None and slot_date <= today

        bg = _DUE_BG if due else "white"
        border = _DUE_BORDER if due else "#cccccc"

        cell = tk.Frame(self._grid_frame, bg=bg, highlightbackground=border, highlightthickness=1)
        cell.grid(row=period, column=DAYS.index(day) + 1, sticky="nsew", padx=2, pady=2)

        class_label = tk.Label(
            cell, text=class_name, bg=bg, font=("", 8), fg="#555555", anchor="center", justify="center"
        )
        class_label.pack(fill="x", padx=4, pady=(3, 0))

        if lesson is not None and lesson.title:
            icon = STATUS_ICONS.get(status)
            content_text = f"{icon} {lesson.title}" if icon else lesson.title
            if status in (STATUS_DONE, STATUS_SHORT):
                content_fg = _DONE_FG
            elif status == STATUS_SKIPPED:
                content_fg = _SKIPPED_FG
            else:
                content_fg = "black"
        else:
            content_text = "(배정된 진도 없음)"
            content_fg = "#888888"

        content_label = tk.Label(
            cell,
            text=content_text,
            bg=bg,
            fg=content_fg,
            wraplength=110,
            justify="center",
            anchor="center",
        )
        content_label.pack(padx=4, pady=(0, 3), fill="both", expand=True)

        handler = lambda _e=None, d=slot_date, p=period, c=class_name, wn=week.number: self._on_cell_click(
            d, p, c, wn
        )
        for widget in (cell, class_label, content_label):
            widget.bind("<Button-1>", handler)
            widget.configure(cursor="hand2")

    def _on_cell_click(self, slot_date: date, period: int, class_name: str, week_number: int) -> None:
        day = DAYS[slot_date.weekday()]
        current_status = progress.slot_status(self.state, slot_date, period, class_name)
        lesson = progress.expected_lesson(self.state, week_number, day, period, class_name)
        title = lesson.title if lesson else None

        def on_choose(status) -> None:
            progress.set_slot_status(self.state, slot_date, period, class_name, status)
            self._save()
            self._refresh_grid()

        StatusChoiceDialog(self, class_name, title, current_status, on_choose)

    # -- dialogs ----------------------------------------------------------
    def open_settings_dialog(self) -> None:
        def on_save(settings) -> None:
            self.state.settings = settings
            self._save()
            self._reload_weeks()

        SettingsDialog(self, self.state.settings, on_save)

    def open_timetable_dialog(self) -> None:
        def on_save(timetable: dict) -> None:
            self.state.timetable = timetable
            self._save()
            self._refresh_grid()

        TimetableDialog(self, self.state.settings, self.state.timetable, on_save)

    def open_week_exception_dialog(self) -> None:
        def on_save(week_number: int, timetable) -> None:
            key = str(week_number)
            if timetable is None:
                self.state.week_exceptions.pop(key, None)
            else:
                self.state.week_exceptions[key] = timetable
            self._save()
            self._refresh_grid()

        current_week_number = (
            self.weeks[self.selected_week_index].number
            if self.weeks and 0 <= self.selected_week_index < len(self.weeks)
            else None
        )
        WeekExceptionDialog(
            self,
            self.state.settings,
            self.weeks,
            self.state.timetable,
            self.state.week_exceptions,
            on_save,
            initial_week_number=current_week_number,
        )

    def open_lessons_dialog(self) -> None:
        def on_save(lessons) -> None:
            self.state.lessons = lessons
            self._save()
            self._refresh_grid()

        LessonsDialog(self, self.state.settings, self.state.lessons, on_save)

    def _on_close(self) -> None:
        self._save()
        self.destroy()
