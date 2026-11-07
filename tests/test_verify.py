from __future__ import annotations

import copy
import json

import pytest

from uzi_grade.verify import verify_exit_code, verify_report


def _write(tmp_path, report) -> "object":
    p = tmp_path / "report.json"
    p.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
    return p


def test_clean_report_verifies_twice_identically(examples_report):
    _report, path = examples_report
    a = verify_report(path)
    b = verify_report(path)
    assert a["matched"] == a["skills"] == 4
    assert a["mismatched"] == []
    assert a["behaviour_mismatch"] == []
    assert a["report_sha256_match"] is True
    assert a["report_seal_match"] is True
    assert verify_exit_code(a) == 0
    assert a["verify_sha256"] == b["verify_sha256"]


def test_non_flagship_entries_need_no_behaviour_records(examples_report):
    report, path = examples_report
    assert all("behaviour" not in e for e in report["skills"])
    assert verify_report(path)["behaviour_mismatch"] == []


@pytest.mark.parametrize("mutate", [
    lambda r: r["skills"][0].__setitem__("level", "L3"),
    lambda r: r["summary"].__setitem__("score_mean", 99.0),
    lambda r: r["skills"][0]["checks"].pop(0),
    lambda r: r["skills"][1].__setitem__("reasons", ["hand written"]),
    lambda r: r["skills"][0]["checks"][0].__setitem__("output_sha256", "0" * 64),
    lambda r: r["skills"][0]["checks"][0].__setitem__("command", "uzi check M1 ./elsewhere"),
    lambda r: r.__setitem__("root_display", "<HOME>/fake"),
    lambda r: r["truncation"].__setitem__("limit", 99),
], ids=["level", "summary", "drop-check", "reason", "check-sha",
        "command", "root-display", "truncation"])
def test_tampering_fails_verification(tmp_path, examples_report, mutate):
    report, _path = examples_report
    bad = copy.deepcopy(report)
    mutate(bad)
    result = verify_report(_write(tmp_path, bad))
    assert verify_exit_code(result) == 1


def test_moved_corpus_verifies_with_root_override(tmp_path, examples_report):
    import shutil

    from conftest import REPO

    _report, path = examples_report
    moved = tmp_path / "moved"
    shutil.copytree(REPO / "examples", moved)
    result = verify_report(path, root_override=moved)
    assert result["matched"] == 4
    assert result["report_sha256_match"] is True
    assert verify_exit_code(result) == 0


def test_missing_corpus_cannot_be_judged(tmp_path, examples_report):
    report, _path = examples_report
    bad = copy.deepcopy(report)
    bad["root"] = str(tmp_path / "does-not-exist")
    result = verify_report(_write(tmp_path, bad))
    assert result["missing"]
    assert verify_exit_code(result) == 2
