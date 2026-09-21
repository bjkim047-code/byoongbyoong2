"""더블클릭 또는 `python run.py`로 바로 실행할 수 있는 진입점."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from progressboard.app import run  # noqa: E402

if __name__ == "__main__":
    run()
