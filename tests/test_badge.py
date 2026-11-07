from __future__ import annotations

import re

import pytest

from uzi_grade import badge, qr
from uzi_grade.grade import grade_skill

from conftest import EXAMPLES

TEXT_RE = re.compile(r"^UZI-L[1-5] · \d+/\d+ · sha256:[0-9a-f]{7} · \d{4}-\d{2}-\d{2}$")
FORBIDDEN = ["金牌", "认证", "最优", "第一", "权威"]


def test_badge_text_is_fixed_format():
    payload = badge.make_badge(EXAMPLES / "good-exec", "2026-11-07")
    assert TEXT_RE.match(payload["text"]), payload["text"]
    assert payload["text"] == (
        f"UZI-{payload['level']} · {payload['passed']}/{payload['applicable']} · "
        f"sha256:{payload['digest'][:7]} · 2026-11-07")


def test_badge_contains_no_titles():
    payload = badge.make_badge(EXAMPLES / "good-exec", "2026-11-07")
    svg = badge.render_svg(payload)
    for word in FORBIDDEN:
        assert word not in svg
        assert word.lower() not in payload["text"].lower()


def test_badge_embeds_full_digest_for_recomputation():
    payload = badge.make_badge(EXAMPLES / "good-prose", "2026-11-07")
    assert payload["qr_payload"] == "sha256:" + payload["digest"]
    assert qr.encode(payload["qr_payload"])


def test_badge_refuses_l0():
    with pytest.raises(ValueError):
        badge.make_badge(EXAMPLES / "bad-template", "2026-11-07")


def test_badge_refuses_when_report_digest_differs(tmp_path, examples_report):
    import json

    report, _path = examples_report
    fake = json.loads(json.dumps(report))
    for entry in fake["skills"]:
        if entry["name"] == "good-exec":
            entry["digest"] = "0" * 64
    p = tmp_path / "report.json"
    p.write_text(json.dumps(fake), encoding="utf-8")
    with pytest.raises(ValueError):
        badge.make_badge(EXAMPLES / "good-exec", "2026-11-07", p)


def test_badge_matches_the_tool_grade():
    result = grade_skill(EXAMPLES / "good-exec")
    payload = badge.make_badge(EXAMPLES / "good-exec", "2026-11-07")
    assert payload["level"] == result["level"] == "L3"
    assert payload["digest"] == result["digest"]
