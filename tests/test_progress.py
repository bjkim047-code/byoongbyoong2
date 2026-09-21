import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from progressboard.models import AppState, Lesson
from progressboard.progress import (
    STATUS_DONE,
    STATUS_SHORT,
    STATUS_SKIPPED,
    class_weekly_slots,
    effective_timetable,
    expected_lesson,
    expected_lesson_index,
    set_slot_status,
    slot_status,
)

BASE_TIMETABLE = {
    "mon": {"1": "2-1", "3": "2-2"},
    "tue": {"1": "2-1"},
    "wed": {},
    "thu": {},
    "fri": {},
}


def make_state(total_lessons: int = 20, semester_start: str = "2026-09-21") -> AppState:
    state = AppState()
    state.settings.semester_start = semester_start  # 2026-09-21은 월요일
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


def test_slot_status_toggles_with_set():
    state = make_state()
    d = date(2026, 9, 21)  # 1주차 월요일
    assert slot_status(state, d, 1, "2-1") is None
    set_slot_status(state, d, 1, "2-1", STATUS_DONE)
    assert slot_status(state, d, 1, "2-1") == STATUS_DONE
    set_slot_status(state, d, 1, "2-1", None)
    assert slot_status(state, d, 1, "2-1") is None


def test_done_and_short_do_not_affect_expected_lesson_numbering():
    state = make_state()
    d = date(2026, 9, 21)  # 1주차 월요일, 2-1
    set_slot_status(state, d, 1, "2-1", STATUS_DONE)
    assert expected_lesson_index(state, 1, "mon", 1, "2-1") == 0
    assert expected_lesson_index(state, 1, "tue", 1, "2-1") == 1

    set_slot_status(state, d, 1, "2-1", STATUS_SHORT)
    assert expected_lesson_index(state, 1, "mon", 1, "2-1") == 0
    assert expected_lesson_index(state, 1, "tue", 1, "2-1") == 1


def test_skipped_shifts_later_slots_back_for_that_class_only():
    state = make_state()
    mon_week1 = date(2026, 9, 21)  # 2-1 1주차 월요일 (0번째)
    set_slot_status(state, mon_week1, 1, "2-1", STATUS_SKIPPED)

    # 못 나간 슬롯 자신은 원래 예정됐던 번호를 그대로 보여준다.
    assert expected_lesson_index(state, 1, "mon", 1, "2-1") == 0
    # 그 다음 슬롯(화요일)부터는 하나씩 밀린다: 원래 1이었을 것이 0으로.
    assert expected_lesson_index(state, 1, "tue", 1, "2-1") == 0
    # 그 다음 주 월요일도 계속 하나 밀린 상태(원래 2 -> 1).
    assert expected_lesson_index(state, 2, "mon", 1, "2-1") == 1

    # 다른 반(2-2)은 전혀 영향받지 않는다.
    assert expected_lesson_index(state, 1, "mon", 3, "2-2") == 0


def test_skipped_uses_correct_lesson_content_after_shift():
    state = make_state()
    mon_week1 = date(2026, 9, 21)
    set_slot_status(state, mon_week1, 1, "2-1", STATUS_SKIPPED)
    assert expected_lesson(state, 1, "tue", 1, "2-1").title == "1차시"


def test_multiple_skips_accumulate_the_shift():
    state = make_state()
    set_slot_status(state, date(2026, 9, 21), 1, "2-1", STATUS_SKIPPED)  # 1주차 월
    set_slot_status(state, date(2026, 9, 22), 1, "2-1", STATUS_SKIPPED)  # 1주차 화
    # 2주차 월요일은 원래 2였을 것이 두 번 밀려 0.
    assert expected_lesson_index(state, 2, "mon", 1, "2-1") == 0
