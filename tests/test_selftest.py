from __future__ import annotations

import pytest

from uzi_grade.selftest import MUTATIONS, run_selftest, selftest_exit_code


@pytest.fixture(scope="module")
def result():
    return run_selftest()


def test_ten_mutations_are_declared(result):
    assert len(MUTATIONS) == 10
    assert result["mutations"] == 10


def test_kill_rate_meets_threshold(result):
    assert result["kills"] >= 9
    assert result["kill_rate"] >= 0.9
    assert selftest_exit_code(result) == 0


def test_every_mutation_kills_its_target(result):
    killed = {r["mutation"]: r["killed"] for r in result["rows"]}
    assert set(killed) == set(MUTATIONS)
    # a mutation may only escape if it is still *detected* somewhere; a
    # completely undetected defect would be a blind spot, so require that too
    undetected = [r["mutation"] for r in result["rows"]
                  if not r["killed"] and not r["newly_red"]]
    assert undetected == []


def test_unmutated_baseline_is_all_green(result):
    assert result["base_red"] == []
    assert result["base_level"] == "L3"
    assert result["base_false_positive_rate"] == 0.0
    assert result["verdict"] == "pass"


def test_reference_corpus_has_no_judge_crash(result):
    assert result["reference_crashes"] == []
    assert result["reference_schema_violations"] == []
