import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from progressboard.models import AppState, Lesson
from progressboard.progress import (
    class_weekly_slots,
    effective_timetable,
    expected_lesson,
    expected_lesson_index,
    is_completed_slot,
    mark_completed,
    unmark_completed,
)

BASE_TIMETABLE = {
    "mon": {"1": "2-1", "3": "2-2"},
    "tue": {"1": "2-1"},
    "wed": {},
    "thu": {},
    "fri": {},
}


def make_state(total_lessons: int = 20) -> AppState:
    state = AppState()
    state.timetable = BASE_TIMETABLE
    state.lessons = [Lesson(title=f"{i}차시") for i in range(1, total_lessons + 1)]
    return state


def test_class_weekly_slots_orders_by_weekday_then_period():
    slots = class_weekly_slots(BASE_TIMETABLE, "2-1")
    assert slots == [("mon", 1), ("tue", 1)]


def test_class_weekly_slots_empty_when_class_not_scheduled():
    assert class_weekly_slots(BASE_TIMETABLE, "2-9") == []


def test_expected_lesson_index_first_week_matches_weekly_order():
    state = make_state()
    assert expected_lesson_index(state, 1, "mon", 1, "2-1") == 0
    assert expected_lesson_index(state, 1, "tue", 1, "2-1") == 1


def test_expected_lesson_index_advances_by_weekly_count_each_week():
    state = make_state()
    # 주당 2차시이므로 3주차는 5,6차시(0-based 4,5)여야 한다.
    assert expected_lesson_index(state, 3, "mon", 1, "2-1") == 4
    assert expected_lesson_index(state, 3, "tue", 1, "2-1") == 5


def test_expected_lesson_index_none_for_unassigned_slot():
    state = make_state()
    assert expected_lesson_index(state, 1, "wed", 1, "2-1") is None


def test_expected_lesson_returns_none_past_total_lessons():
    state = make_state(total_lessons=1)
    assert expected_lesson(state, 1, "mon", 1, "2-1").title == "1차시"
    assert expected_lesson(state, 1, "tue", 1, "2-1") is None  # 두 번째 차시는 목록 밖


def test_effective_timetable_uses_exception_only_for_that_week():
    state = make_state()
    state.week_exceptions["2"] = {"mon": {"1": "2-1"}, "tue": {}, "wed": {}, "thu": {}, "fri": {}}
    assert effective_timetable(state, 1) == BASE_TIMETABLE
    assert effective_timetable(state, 2) == state.week_exceptions["2"]
    assert effective_timetable(state, 3) == BASE_TIMETABLE


def test_exception_week_with_fewer_occurrences_shifts_later_weeks_back():
    state = make_state()
    # 2주차에 2-1반 화요일 수업이 휴강(예외 시간표에서 제거)됐다고 가정.
    state.week_exceptions["2"] = {"mon": {"1": "2-1"}, "tue": {}, "wed": {}, "thu": {}, "fri": {}}

    # 1주차: 0,1 / 2주차(휴강으로 1번만): 2 / 3주차부터는 하나씩 밀려서 3,4
    assert expected_lesson_index(state, 1, "mon", 1, "2-1") == 0
    assert expected_lesson_index(state, 1, "tue", 1, "2-1") == 1
    assert expected_lesson_index(state, 2, "mon", 1, "2-1") == 2
    assert expected_lesson_index(state, 3, "mon", 1, "2-1") == 3
    assert expected_lesson_index(state, 3, "tue", 1, "2-1") == 4


def test_is_completed_slot_toggles_with_mark_and_unmark():
    state = make_state()
    d = date(2026, 9, 21)
    assert not is_completed_slot(state, d, 1, "2-1")
    assert mark_completed(state, d, 1, "2-1") is True
    assert is_completed_slot(state, d, 1, "2-1")
    assert unmark_completed(state, d, 1, "2-1") is True
    assert not is_completed_slot(state, d, 1, "2-1")


def test_mark_completed_is_idempotent_for_same_slot():
    state = make_state()
    d = date(2026, 9, 21)
    assert mark_completed(state, d, 1, "2-1") is True
    assert mark_completed(state, d, 1, "2-1") is False
    assert state.completed.count(f"{d.isoformat()}|1|2-1") == 1


def test_unmark_completed_does_nothing_if_not_completed():
    assert unmark_completed(make_state(), date(2026, 9, 21), 1, "2-1") is False


def test_completion_does_not_change_expected_lesson_for_other_slots():
    state = make_state()
    d = date(2026, 9, 21)
    mark_completed(state, d, 1, "2-1")
    # 완료 처리해도 시간표 기반 예상 차시 번호 자체는 바뀌지 않는다.
    assert expected_lesson_index(state, 1, "mon", 1, "2-1") == 0
    assert expected_lesson_index(state, 1, "tue", 1, "2-1") == 1
