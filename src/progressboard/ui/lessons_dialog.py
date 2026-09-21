"""'진도 설정' 다이얼로그.

1차시부터 마지막 차시까지 각 차시의 제목/내용을 입력한다.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from ..models import Lesson, Settings


class LessonsDialog(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Misc,
        settings: Settings,
        lessons: list[Lesson],
        on_save: Callable[[list[Lesson]], None],
    ):
        super().__init__(parent)
        self.title("진도 설정")
        self.geometry("520x420")
        self.minsize(480, 360)
        self.transient(parent)
        self.grab_set()

        self._on_save = on_save
        self._lessons = self._reconcile(lessons, settings.total_lessons)
        self._current_index: int | None = None

        body = ttk.Frame(self, padding=10)
        body.pack(fill="both", expand=True)

        left = ttk.Frame(body)
        left.pack(side="left", fill="y")

        ttk.Label(left, text=f"{settings.subject_name} 차시 목록").pack(anchor="w")
        list_frame = ttk.Frame(left)
        list_frame.pack(fill="y", expand=True, pady=(4, 0))
        self._listbox = tk.Listbox(list_frame, width=22, height=18, exportselection=False)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self._listbox.yview)
        self._listbox.configure(yscrollcommand=scrollbar.set)
        self._listbox.pack(side="left", fill="y")
        scrollbar.pack(side="left", fill="y")
        self._listbox.bind("<<ListboxSelect>>", self._on_select)

        right = ttk.Frame(body, padding=(12, 0, 0, 0))
        right.pack(side="left", fill="both", expand=True)

        ttk.Label(right, text="차시 제목").pack(anchor="w")
        self._title_var = tk.StringVar()
        ttk.Entry(right, textvariable=self._title_var).pack(fill="x", pady=(2, 10))

        ttk.Label(right, text="수업 내용").pack(anchor="w")
        self._content_text = tk.Text(right, height=14, wrap="word")
        self._content_text.pack(fill="both", expand=True, pady=(2, 0))

        btns = ttk.Frame(self)
        btns.pack(side="bottom", pady=(0, 10))
        ttk.Button(btns, text="저장", command=self._save).pack(side="left", padx=4)
        ttk.Button(btns, text="취소", command=self.destroy).pack(side="left", padx=4)

        self._refresh_list()
        if self._lessons:
            self._listbox.selection_set(0)
            self._load_index(0)

        self.bind("<Escape>", lambda _e: self.destroy())

    @staticmethod
    def _reconcile(lessons: list[Lesson], total: int) -> list[Lesson]:
        lessons = [Lesson(l.title, l.content) for l in lessons]
        if len(lessons) < total:
            lessons.extend(Lesson() for _ in range(total - len(lessons)))
        elif len(lessons) > total:
            lessons = lessons[:total]
        return lessons

    def _refresh_list(self) -> None:
        self._listbox.delete(0, "end")
        for i, lesson in enumerate(self._lessons, start=1):
            label = f"{i}차시 " + (lesson.title if lesson.title else "(제목 없음)")
            self._listbox.insert("end", label)

    def _store_current(self) -> None:
        if self._current_index is None:
            return
        self._lessons[self._current_index] = Lesson(
            title=self._title_var.get().strip(),
            content=self._content_text.get("1.0", "end").strip(),
        )

    def _load_index(self, index: int) -> None:
        self._current_index = index
        lesson = self._lessons[index]
        self._title_var.set(lesson.title)
        self._content_text.delete("1.0", "end")
        self._content_text.insert("1.0", lesson.content)

    def _on_select(self, _event=None) -> None:
        selection = self._listbox.curselection()
        if not selection:
            return
        self._store_current()
        self._load_index(selection[0])
        self._refresh_list()
        self._listbox.selection_set(selection[0])

    def _save(self) -> None:
        self._store_current()
        self._on_save(self._lessons)
        self.destroy()
