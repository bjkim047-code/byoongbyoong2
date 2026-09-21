"""시간표 상 슬롯이 몇 차시에 해당하는지 계산하고, 완료 여부를 기록한다.

각 반의 "예상 차시"는 실제 진행 여부와 무관하게, 주차와 기본(또는 예외)
시간표만으로 계산된다. 즉 1주차에 2번 들어가는 반이면 1주차는 1~2차시,
2주차는 3~4차시, ... 처럼 항상 정해진 위치에 정해진 차시가 표시된다.
휴강 등으로 예외 시간표에서 특정 주의 수업 횟수가 줄어들면, 그 다음
주차부터는 차시 번호가 그만큼 뒤로 밀린다(직전 주들의 실제 수업 횟수를
누적해서 계산하기 때문).

수업 완료 체크(완료 표시)는 이 차시 계산과는 별개로, 단순히 "이 (날짜,
교시, 반) 수업을 실제로 진행했다"는 기록일 뿐이다.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from .models import DAYS, AppState, Lesson


def slot_key(slot_date: date, period: int, class_name: str) -> str:
    return f"{slot_date.isoformat()}|{period}|{class_name}"


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


def expected_lesson_index(
    state: AppState, week_number: int, day: str, period: int, class_name: str
) -> Optional[int]:
    """이 (주차, 요일, 교시) 슬롯에 예상되는 차시 번호(0-based)."""

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


def expected_lesson(
    state: AppState, week_number: int, day: str, period: int, class_name: str
) -> Optional[Lesson]:
    index = expected_lesson_index(state, week_number, day, period, class_name)
    if index is None or index >= len(state.lessons):
        return None
    return state.lessons[index]


def is_completed_slot(state: AppState, slot_date: date, period: int, class_name: str) -> bool:
    return slot_key(slot_date, period, class_name) in state.completed


def mark_completed(state: AppState, slot_date: date, period: int, class_name: str) -> bool:
    """해당 수업을 완료 처리한다. 이미 완료 처리돼 있으면 아무 것도 하지 않는다."""

    key = slot_key(slot_date, period, class_name)
    if key in state.completed:
        return False
    state.completed.append(key)
    return True


def unmark_completed(state: AppState, slot_date: date, period: int, class_name: str) -> bool:
    """완료 표시를 취소한다."""

    key = slot_key(slot_date, period, class_name)
    if key not in state.completed:
        return False
    state.completed.remove(key)
    return True
