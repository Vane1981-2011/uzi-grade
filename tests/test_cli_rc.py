from __future__ import annotations

import json

from uzi_grade.cli import main

from conftest import EXAMPLES


def test_missing_path_is_not_judged(capsys):
    assert main(["grade", "/nope/definitely-missing"]) == 2


def test_empty_corpus_is_not_judged(tmp_path, capsys):
    assert main(["grade", "--all", str(tmp_path), "--out", str(tmp_path / "out")]) == 2


def test_truncated_scan_is_not_judged(tmp_path, capsys):
    rc = main(["grade", "--all", str(EXAMPLES), "--max", "1",
               "--out", str(tmp_path / "out")])
    assert rc == 2
    report = json.loads((tmp_path / "out" / "report.json").read_text(encoding="utf-8"))
    trunc = report["truncation"]
    assert trunc["truncated"] is True
    assert trunc["omitted_count"] == 3
    assert trunc["omitted"] == ["bad-template", "good-exec", "good-prose"]


def test_single_good_skill_exits_zero(capsys):
    assert main(["grade", str(EXAMPLES / "good-exec")]) == 0


def test_single_bad_skill_exits_one(capsys):
    assert main(["grade", str(EXAMPLES / "bad-broken-ref")]) == 1


def test_check_subcommand_replays_one_row(capsys):
    assert main(["check", "M1", str(EXAMPLES / "good-exec")]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["check_id"] == "M1" and out["status"] == "pass"
    assert out["command"] == "uzi check M1 ./good-exec"


def test_behaviour_stub_says_not_executed(capsys):
    assert main(["behaviour", "B1", str(EXAMPLES / "good-exec")]) == 2
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "unverifiable"
    assert out["missing"]
