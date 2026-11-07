from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
EXAMPLES = REPO / "examples"
sys.path.insert(0, str(REPO / "src"))


@pytest.fixture(scope="session")
def examples_report(tmp_path_factory):
    """Grade the synthetic corpus once; most tests read this report."""
    from uzi_grade.grade import build_report, write_report

    out = tmp_path_factory.mktemp("examples-report")
    report = build_report(EXAMPLES)
    report_path, _md = write_report(report, out)
    return report, report_path


@pytest.fixture()
def copy_skill(tmp_path):
    def _copy(name: str = "good-exec") -> Path:
        dst = tmp_path / name
        shutil.copytree(EXAMPLES / name, dst)
        return dst
    return _copy


def load(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))
