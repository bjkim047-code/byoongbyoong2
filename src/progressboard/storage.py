"""로컬 JSON 파일에 설정/시간표/진도 상태를 저장하고 불러온다."""

from __future__ import annotations

import json
import os
from pathlib import Path

from .models import AppState

APP_DIR = Path(os.environ.get("PROGRESSBOARD_HOME", Path.home() / ".progressboard"))
DATA_FILE = APP_DIR / "data.json"


def _ensure_dir() -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)


def load() -> AppState:
    _ensure_dir()
    if not DATA_FILE.exists():
        return AppState()
    try:
        raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return AppState()
    return AppState.from_dict(raw)


def save(state: AppState) -> None:
    _ensure_dir()
    tmp_file = DATA_FILE.with_suffix(".json.tmp")
    tmp_file.write_text(json.dumps(state.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_file.replace(DATA_FILE)
