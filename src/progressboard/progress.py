"""반별 진도 조회/완료 처리 로직."""

from __future__ import annotations

from datetime import date

from .models import AppState, Lesson


def slot_key(slot_date: date, period: int, class_name: str) -> str:
    return f"{slot_date.isoformat()}|{period}|{class_name}"


def current_lesson_index(state: AppState, class_name: str) -> int:
    """이 반이 다음에 나갈 차시 번호(0-based). 아직 기록이 없으면 0(첫 차시)."""

    return int(state.progress.get(class_name, 0))


def current_lesson(state: AppState, class_name: str) -> Lesson | None:
    index = current_lesson_index(state, class_name)
    if 0 <= index < len(state.lessons):
        return state.lessons[index]
    return None


def is_finished(state: AppState, class_name: str) -> bool:
    return current_lesson_index(state, class_name) >= len(state.lessons)


def is_completed_slot(state: AppState, slot_date: date, period: int, class_name: str) -> bool:
    return slot_key(slot_date, period, class_name) in state.completed


def mark_completed(state: AppState, slot_date: date, period: int, class_name: str) -> bool:
    """해당 수업을 완료 처리하고 그 반의 진도를 한 차시 넘긴다.

    이미 완료 처리된 (날짜, 교시, 반) 조합이면 아무 것도 하지 않고 False를 반환한다.
    """

    key = slot_key(slot_date, period, class_name)
    if key in state.completed:
        return False
    state.completed.append(key)
    state.progress[class_name] = current_lesson_index(state, class_name) + 1
    return True


def unmark_completed(state: AppState, slot_date: date, period: int, class_name: str) -> bool:
    """완료 처리를 취소하고 그 반의 진도를 한 차시 되돌린다."""

    key = slot_key(slot_date, period, class_name)
    if key not in state.completed:
        return False
    state.completed.remove(key)
    state.progress[class_name] = max(current_lesson_index(state, class_name) - 1, 0)
    return True
