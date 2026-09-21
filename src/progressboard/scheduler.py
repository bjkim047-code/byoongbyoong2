"""학기 시작일을 기준으로 주차/날짜를 계산한다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from .models import DAYS

DATE_FMT = "%Y-%m-%d"


@dataclass
class Week:
    number: int  # 1부터 시작하는 주차 번호
    start: date  # 월요일
    end: date  # 금요일

    @property
    def label(self) -> str:
        return f"{self.start.strftime('%m-%d')} ~ {self.end.strftime('%m-%d')}"

    def day_date(self, day: str) -> date:
        return self.start + timedelta(days=DAYS.index(day))


def parse_date(text: str) -> Optional[date]:
    text = (text or "").strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def monday_of(day: date) -> date:
    return day - timedelta(days=day.weekday())


def build_weeks(semester_start: str, num_weeks: int) -> list[Week]:
    start = parse_date(semester_start) or monday_of(date.today())
    start = monday_of(start)
    num_weeks = max(int(num_weeks or 0), 0)
    weeks = []
    for i in range(num_weeks):
        week_start = start + timedelta(weeks=i)
        weeks.append(Week(number=i + 1, start=week_start, end=week_start + timedelta(days=4)))
    return weeks


def week_number_for_date(semester_start: str, target: date) -> int:
    """1주차 시작일 기준으로, 이 날짜가 몇 주차에 해당하는지(1부터)."""

    start = monday_of(parse_date(semester_start) or target)
    delta_days = (target - start).days
    return delta_days // 7 + 1


def current_week_index(weeks: list[Week], today: Optional[date] = None) -> int:
    """오늘이 포함된 주차의 인덱스. 없으면 가장 가까운 미래 주, 그마저 없으면 마지막 주."""

    if not weeks:
        return -1
    today = today or date.today()
    for i, week in enumerate(weeks):
        if week.start <= today <= week.end:
            return i
    for i, week in enumerate(weeks):
        if today < week.start:
            return i
    return len(weeks) - 1
