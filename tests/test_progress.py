import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from progressboard.models import AppState, Lesson
from progressboard.progress import (
    current_lesson,
    current_lesson_index,
    is_completed_slot,
    is_finished,
    mark_completed,
    unmark_completed,
)


def make_state() -> AppState:
    state = AppState()
    state.lessons = [Lesson(title=f"{i}차시") for i in range(1, 4)]  # 3개 차시
    return state


def test_new_class_starts_at_first_lesson():
    state = make_state()
    assert current_lesson_index(state, "2-1") == 0
    assert current_lesson(state, "2-1").title == "1차시"
    assert not is_finished(state, "2-1")


def test_mark_completed_advances_progress_and_records_slot():
    state = make_state()
    d = date(2026, 9, 21)
    assert mark_completed(state, d, 1, "2-1") is True
    assert current_lesson_index(state, "2-1") == 1
    assert is_completed_slot(state, d, 1, "2-1")


def test_mark_completed_is_idempotent_for_same_slot():
    state = make_state()
    d = date(2026, 9, 21)
    mark_completed(state, d, 1, "2-1")
    assert mark_completed(state, d, 1, "2-1") is False
    assert current_lesson_index(state, "2-1") == 1  # 두 번 넘어가지 않음


def test_other_classes_are_independent():
    state = make_state()
    mark_completed(state, date(2026, 9, 21), 1, "2-1")
    assert current_lesson_index(state, "2-2") == 0


def test_unmark_completed_reverts_progress():
    state = make_state()
    d = date(2026, 9, 21)
    mark_completed(state, d, 1, "2-1")
    assert unmark_completed(state, d, 1, "2-1") is True
    assert current_lesson_index(state, "2-1") == 0
    assert not is_completed_slot(state, d, 1, "2-1")


def test_unmark_completed_does_nothing_if_not_completed():
    state = make_state()
    assert unmark_completed(state, date(2026, 9, 21), 1, "2-1") is False


def test_is_finished_once_all_lessons_completed():
    state = make_state()
    for i, d in enumerate([date(2026, 9, 21), date(2026, 9, 24), date(2026, 9, 28)]):
        mark_completed(state, d, i + 1, "2-1")
    assert is_finished(state, "2-1")
    assert current_lesson(state, "2-1") is None
