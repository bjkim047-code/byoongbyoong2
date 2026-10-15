"""수업 진행 상태(완료 / 시간 부족 / 진행 못함)를 고르는 작은 팝업.

'시간 부족'을 고르면 보충할 내용을 적어둘 수 있는 선택적 메모 입력
화면으로 바뀐다. 이 메모는 그 반의 바로 다음 수업 칸에 표시된다.
"""

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
        current_note: Optional[str],
        on_choose: Callable[[Optional[str], Optional[str]], None],
    ):
        super().__init__(parent)
        self.title("수업 진행 상태")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._on_choose = on_choose
        self._current_note = current_note or ""
        self._note_text: Optional[tk.Text] = None

        ttk.Label(
            self, text=self._header_text(class_name, lesson_title), wraplength=260, justify="left"
        ).pack(padx=16, pady=(16, 10))

        self._choice_frame = ttk.Frame(self)
        self._choice_frame.pack(padx=16)
        ttk.Button(
            self._choice_frame,
            text=STATUS_LABELS[STATUS_DONE],
            command=lambda: self._choose(STATUS_DONE, None),
        ).pack(side="left", padx=4)
        ttk.Button(
            self._choice_frame, text=STATUS_LABELS[STATUS_SHORT], command=self._show_note_input
        ).pack(side="left", padx=4)
        ttk.Button(
            self._choice_frame,
            text=STATUS_LABELS[STATUS_SKIPPED],
            command=lambda: self._choose(STATUS_SKIPPED, None),
        ).pack(side="left", padx=4)

        self._bottom_frame = ttk.Frame(self)
        self._bottom_frame.pack(padx=16, pady=(10, 16))
        if current_status is not None:
            ttk.Button(
                self._bottom_frame, text="상태 해제", command=lambda: self._choose(None, None)
            ).pack(side="left", padx=4)
        ttk.Button(self._bottom_frame, text="취소", command=self.destroy).pack(side="left", padx=4)

        self._note_frame = ttk.Frame(self)

        self.bind("<Escape>", lambda _e: self.destroy())

    @staticmethod
    def _header_text(class_name: str, lesson_title: Optional[str]) -> str:
        text = f"{class_name} 반"
        if lesson_title:
            text += f" · {lesson_title}"
        return text

    def _show_note_input(self) -> None:
        self._choice_frame.pack_forget()
        self._bottom_frame.pack_forget()

        ttk.Label(
            self._note_frame,
            text="보충할 내용이 있으면 적어두세요. (선택 사항 — 다음 수업 칸에 표시됩니다)",
            foreground="gray",
            wraplength=260,
            justify="left",
        ).pack(anchor="w", pady=(0, 6))

        self._note_text = tk.Text(self._note_frame, width=32, height=4, wrap="word")
        self._note_text.pack()
        if self._current_note:
            self._note_text.insert("1.0", self._current_note)
        self._note_text.focus_set()

        btns = ttk.Frame(self._note_frame)
        btns.pack(pady=(8, 0))
        ttk.Button(btns, text="저장", command=self._save_note).pack(side="left", padx=4)
        ttk.Button(btns, text="취소", command=self.destroy).pack(side="left", padx=4)

        self._note_frame.pack(padx=16, pady=(0, 16))

    def _save_note(self) -> None:
        note = self._note_text.get("1.0", "end").strip() if self._note_text else ""
        self._choose(STATUS_SHORT, note or None)

    def _choose(self, status: Optional[str], note: Optional[str]) -> None:
        self._on_choose(status, note)
        self.destroy()
