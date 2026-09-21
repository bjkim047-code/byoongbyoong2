"""데이터 모델: 기본 설정(Settings)과 진도 항목(Lesson)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Optional

DAYS = ["mon", "tue", "wed", "thu", "fri"]
DAY_LABELS = {"mon": "월", "tue": "화", "wed": "수", "thu": "목", "fri": "금"}


def default_classes() -> list[str]:
    return [f"2-{i}" for i in range(1, 11)]


@dataclass
class Settings:
    """수업 기본 설정. 시간표/진도표를 구성하는 기준값들."""

    subject_name: str = "과목"
    classes: list[str] = field(default_factory=default_classes)
    periods_per_week: int = 2  # 한 반에 일주일에 몇 번 들어가는지
    periods_per_day: int = 7  # 하루 최대 교시 수 (표시용)
    total_lessons: int = 16  # 이번 학기 진도표 칸 개수(총 차시 수)
    semester_start: str = ""  # 1주차 월요일 날짜, "YYYY-MM-DD"
    num_weeks: int = 8  # 남은(표시할) 주차 수

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: Optional[dict]) -> "Settings":
        base = Settings().to_dict()
        base.update(data or {})
        return Settings(**{k: base[k] for k in base if k in Settings.__dataclass_fields__})


@dataclass
class Lesson:
    """한 차시의 진도 제목/내용."""

    title: str = ""
    content: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: Optional[dict]) -> "Lesson":
        base = Lesson().to_dict()
        base.update(data or {})
        return Lesson(**{k: base[k] for k in base if k in Lesson.__dataclass_fields__})


@dataclass
class AppState:
    """앱 전체 저장 상태: 설정, 기본 시간표, 진도 목록, 반별 진행 상황."""

    settings: Settings = field(default_factory=Settings)
    timetable: dict = field(default_factory=dict)  # day -> {period(str): class_name}
    lessons: list[Lesson] = field(default_factory=list)
    progress: dict = field(default_factory=dict)  # class_name -> 다음에 나갈 차시 번호(0-based)
    completed: list = field(default_factory=list)  # "날짜|교시|반" 형태로 완료 처리된 수업 기록

    def to_dict(self) -> dict:
        return {
            "settings": self.settings.to_dict(),
            "timetable": self.timetable,
            "lessons": [lesson.to_dict() for lesson in self.lessons],
            "progress": self.progress,
            "completed": list(self.completed),
        }

    @staticmethod
    def from_dict(data: Optional[dict]) -> "AppState":
        data = data or {}
        return AppState(
            settings=Settings.from_dict(data.get("settings")),
            timetable=data.get("timetable") or {},
            lessons=[Lesson.from_dict(item) for item in data.get("lessons", [])],
            progress=dict(data.get("progress") or {}),
            completed=list(data.get("completed") or []),
        )
