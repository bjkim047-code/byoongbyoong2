"""수업 진행 상태(완료 / 시간 부족 / 진행 못함)를 고르는 작은 팝업."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from ..progress import STATUS_DONE, STATUS_LABELS, STATUS_SHORT, STATUS_SKIPPED


class StatusChoiceDialog(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Misc,
        class_name: str,
        lesson_title: Optional[str],
        current_status: Optional[str],
        on_choose: Callable[[Optional[str]], None],
    ):
        super().__init__(parent)
        self.title("수업 진행 상태")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._on_choose = on_choose

        text = f"{class_name} 반"
        if lesson_title:
            text += f" · {lesson_title}"
        ttk.Label(self, text=text, wraplength=260, justify="left").pack(padx=16, pady=(16, 10))

        choices = ttk.Frame(self)
        choices.pack(padx=16)
        for status in (STATUS_DONE, STATUS_SHORT, STATUS_SKIPPED):
            ttk.Button(
                choices, text=STATUS_LABELS[status], command=lambda s=status: self._choose(s)
            ).pack(side="left", padx=4)

        bottom = ttk.Frame(self)
        bottom.pack(padx=16, pady=(10, 16))
        if current_status is not None:
            ttk.Button(bottom, text="상태 해제", command=lambda: self._choose(None)).pack(
                side="left", padx=4
            )
        ttk.Button(bottom, text="취소", command=self.destroy).pack(side="left", padx=4)

        self.bind("<Escape>", lambda _e: self.destroy())

    def _choose(self, status: Optional[str]) -> None:
        self._on_choose(status)
        self.destroy()
