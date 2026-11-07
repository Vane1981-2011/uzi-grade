from __future__ import annotations

import pytest

from uzi_grade import qr
from uzi_grade.calibrate import distribution, percentile
from uzi_grade.checks import CheckResult, extract_triggers
from uzi_grade.grade import compute_level, validate_attestation
from uzi_grade.parse import parse_frontmatter


def test_percentile_uses_linear_interpolation():
    assert percentile([10, 20, 30, 40], 0.5) == 25.0
    assert percentile([10, 20, 30, 40], 0.75) == 32.5
    assert percentile([], 0.5) is None
    assert distribution([])["n"] == 0


def test_unverifiable_requires_missing_text():
    with pytest.raises(ValueError):
        CheckResult("M6", "unverifiable", "no evidence")
    ok = CheckResult("M6", "unverifiable", "no evidence", missing="tests/expected.json")
    assert ok.to_dict()["missing"] == "tests/expected.json"
    assert ok.to_dict()["exit_code"] == 2


def test_prose_skill_cannot_reach_l3():
    results = [CheckResult(cid, "pass") for cid in
               ("M1", "M2", "M3", "M4", "M7", "M8")]
    results.append(CheckResult("M5", "skip"))
    results.append(CheckResult("M6", "skip"))
    level, reasons = compute_level(results, "prose")
    assert level == "L2"
    assert any("L3 未达" in r for r in reasons)


def test_attestation_needs_url_and_date():
    ok, _ = validate_attestation({"level": "L4", "url": "https://example.com/case",
                                  "collected_at": "2026-11-07"})
    assert ok
    assert not validate_attestation({"level": "L4", "url": "example.com"})[0]
    assert not validate_attestation({"level": "L4", "url": "https://example.com"})[0]
    assert not validate_attestation({"level": "L3", "url": "https://example.com",
                                     "collected_at": "2026-11-07"})[0]


def test_l4_requires_a_valid_attestation():
    results = [CheckResult(cid, "pass") for cid in
               ("M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8")]
    level, _ = compute_level(results, "exec")
    assert level == "L3"
    level, reasons = compute_level(results, "exec", {"level": "L4"})
    assert level == "L3"
    assert any("申报无效" in r for r in reasons)
    level, _ = compute_level(results, "exec", {"level": "L4", "url": "https://x.test/a",
                                               "collected_at": "2026-11-07"})
    assert level == "L4"


def test_multiline_trigger_block_is_extracted():
    fm, _ = parse_frontmatter(
        "---\n"
        "name: demo\n"
        "description: |\n"
        "  分析财报并给出结论。\n"
        "  MUST trigger when user:\n"
        "  - 请求决策分析：该怎么选、要不要做\n"
        "  - 需要财报拆解\n"
        "---\n"
        "body\n")
    triggers = extract_triggers(fm["description"])
    assert "请求决策分析" in triggers
    assert "怎么写" not in triggers


def test_qr_encodes_digest_payload():
    mod = qr.encode("sha256:" + "0" * 64)
    assert len(mod) > 10
    assert all(len(row) == len(mod) for row in mod)
