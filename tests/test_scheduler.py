import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from progressboard.scheduler import build_weeks, current_week_index, monday_of, parse_date


def test_parse_date_valid_and_invalid():
    assert parse_date("2026-09-21") == date(2026, 9, 21)
    assert parse_date("") is None
    assert parse_date("not-a-date") is None


def test_monday_of_returns_monday_of_same_week():
    wednesday = date(2026, 9, 23)
    assert monday_of(wednesday) == date(2026, 9, 21)
    assert monday_of(date(2026, 9, 21)) == date(2026, 9, 21)


def test_build_weeks_generates_consecutive_mon_to_fri_weeks():
    weeks = build_weeks("2026-09-21", 3)
    assert [w.number for w in weeks] == [1, 2, 3]
    assert weeks[0].start == date(2026, 9, 21)
    assert weeks[0].end == date(2026, 9, 25)
    assert weeks[1].start == date(2026, 9, 28)
    assert weeks[2].start == date(2026, 10, 5)


def test_build_weeks_snaps_non_monday_start_to_monday():
    weeks = build_weeks("2026-09-23", 1)  # 수요일
    assert weeks[0].start == date(2026, 9, 21)


def test_week_day_date_maps_weekday_to_correct_date():
    weeks = build_weeks("2026-09-21", 1)
    week = weeks[0]
    assert week.day_date("mon") == date(2026, 9, 21)
    assert week.day_date("fri") == date(2026, 9, 25)


def test_current_week_index_finds_week_containing_today():
    today = date.today()
    start = monday_of(today - timedelta(weeks=1))
    weeks = build_weeks(start.isoformat(), 3)
    index = current_week_index(weeks, today)
    assert weeks[index].start <= today <= weeks[index].end


def test_current_week_index_before_semester_returns_first_week():
    future_start = date.today() + timedelta(weeks=2)
    weeks = build_weeks(monday_of(future_start).isoformat(), 3)
    assert current_week_index(weeks, date.today()) == 0


def test_current_week_index_after_semester_returns_last_week():
    past_start = date.today() - timedelta(weeks=10)
    weeks = build_weeks(monday_of(past_start).isoformat(), 3)
    assert current_week_index(weeks, date.today()) == len(weeks) - 1


def test_current_week_index_empty_weeks_returns_negative_one():
    assert current_week_index([], date.today()) == -1
