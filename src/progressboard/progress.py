"""시간표 상 슬롯이 몇 차시에 해당하는지 계산하고, 진행 상태를 기록한다.

각 반의 "예상 차시"는 원칙적으로 주차와 기본(또는 예외) 시간표만으로
계산된다. 즉 1주차에 2번 들어가는 반이면 1주차는 1~2차시, 2주차는
3~4차시, ... 처럼 정해진 위치에 정해진 차시가 표시된다. 휴강 등으로
예외 시간표에서 특정 주의 수업 횟수가 줄어들면, 그 다음 주차부터는
차시 번호가 그만큼 뒤로 밀린다.

수업마다 세 가지 상태를 표시할 수 있다.
- done(완료) / short(시간 부족): 기록만 남을 뿐 이후 차시 번호에는
  영향을 주지 않는다.
- skipped(진행 못함): 그 수업은 실제로 진행되지 않은 것으로 치고,
  그 반의 그 다음 수업부터 차시 번호가 하나씩 뒤로 밀린다(밀린 수업
  자신은 원래 예정됐던 번호를 그대로 보여준다).
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from .models import DAYS, AppState, Lesson
from .scheduler import week_number_for_date

STATUS_DONE = "done"
STATUS_SHORT = "short"
STATUS_SKIPPED = "skipped"

STATUS_LABELS = {STATUS_DONE: "완료", STATUS_SHORT: "시간 부족", STATUS_SKIPPED: "진행 못함"}
STATUS_ICONS = {STATUS_DONE: "✓", STATUS_SHORT: "△", STATUS_SKIPPED: "✕"}


def slot_key(slot_date: date, period: int, class_name: str) -> str:
    return f"{slot_date.isoformat()}|{period}|{class_name}"


def _parse_slot_key(key: str) -> Optional[tuple[date, int, str]]:
    try:
        date_str, period_str, class_name = key.split("|", 2)
        return date.fromisoformat(date_str), int(period_str), class_name
    except (ValueError, TypeError):
        return None


def effective_timetable(state: AppState, week_number: int) -> dict:
    """해당 주차에 실제로 적용되는 시간표. 예외가 등록돼 있으면 그걸 쓴다."""

    return state.week_exceptions.get(str(week_number)) or state.timetable


def class_weekly_slots(timetable: dict, class_name: str) -> list[tuple[str, int]]:
    """그 시간표에서 이 반이 들어가는 (요일, 교시) 목록을, 주중 순서대로."""

    slots = []
    for day in DAYS:
        for period_str, name in (timetable.get(day) or {}).items():
            if name == class_name:
                slots.append((day, int(period_str)))
    slots.sort(key=lambda dp: (DAYS.index(dp[0]), dp[1]))
    return slots


def _raw_position(
    state: AppState, week_number: int, day: str, period: int, class_name: str
) -> Optional[int]:
    """진행 못함 처리 이전, 시간표만으로 계산한 순번(0-based)."""

    cumulative = 0
    for earlier_week in range(1, week_number):
        earlier_timetable = effective_timetable(state, earlier_week)
        cumulative += len(class_weekly_slots(earlier_timetable, class_name))

    current_slots = class_weekly_slots(effective_timetable(state, week_number), class_name)
    try:
        rank = current_slots.index((day, period))
    except ValueError:
        return None
    return cumulative + rank


def _skip_count_before(state: AppState, class_name: str, position: int) -> int:
    """이 반의 순번이 position보다 앞선 '진행 못함' 처리 건수."""

    count = 0
    for key, status in state.slot_status.items():
        if status != STATUS_SKIPPED:
            continue
        parsed = _parse_slot_key(key)
        if parsed is None:
            continue
        slot_date, period, key_class = parsed
        if key_class != class_name:
            continue
        day_index = slot_date.weekday()
        if day_index >= len(DAYS):
            continue
        week_number = week_number_for_date(state.settings.semester_start, slot_date)
        skipped_position = _raw_position(state, week_number, DAYS[day_index], period, class_name)
        if skipped_position is not None and skipped_position < position:
            count += 1
    return count


def expected_lesson_index(
    state: AppState, week_number: int, day: str, period: int, class_name: str
) -> Optional[int]:
    """이 (주차, 요일, 교시) 슬롯에 예상되는 차시 번호(0-based)."""

    position = _raw_position(state, week_number, day, period, class_name)
    if position is None:
        return None
    return position - _skip_count_before(state, class_name, position)


def expected_lesson(
    state: AppState, week_number: int, day: str, period: int, class_name: str
) -> Optional[Lesson]:
    index = expected_lesson_index(state, week_number, day, period, class_name)
    if index is None or index >= len(state.lessons):
        return None
    return state.lessons[index]


def slot_status(state: AppState, slot_date: date, period: int, class_name: str) -> Optional[str]:
    return state.slot_status.get(slot_key(slot_date, period, class_name))


def set_slot_status(
    state: AppState, slot_date: date, period: int, class_name: str, status: Optional[str]
) -> None:
    """이 수업의 진행 상태를 설정한다. status가 None이면 상태를 지운다(미정으로 되돌림)."""

    key = slot_key(slot_date, period, class_name)
    if status is None:
        state.slot_status.pop(key, None)
    else:
        state.slot_status[key] = status
