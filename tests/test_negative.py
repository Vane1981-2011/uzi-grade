"""Negative acceptance: removing a guardrail must actually cost a level."""
from __future__ import annotations

import re

from uzi_grade.grade import grade_skill


def _drop_section(text: str, keyword: str) -> str:
    lines = text.splitlines()
    out, skip, level = [], False, 0
    for line in lines:
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m and keyword in m.group(2):
            skip, level = True, len(m.group(1))
            continue
        if skip and m and len(m.group(1)) <= level:
            skip = False
        if not skip:
            out.append(line)
    return "\n".join(out)


def test_removing_hard_gate_drops_level(copy_skill):
    skill = copy_skill("good-exec")
    before = grade_skill(skill)
    assert before["level"] == "L3"

    md = skill / "SKILL.md"
    md.write_text(_drop_section(md.read_text(encoding="utf-8"), "HARD-GATE"),
                  encoding="utf-8")

    after = grade_skill(skill)
    m7 = next(c for c in after["checks"] if c["check_id"] == "M7")
    assert m7["status"] == "fail"
    assert after["level"] == "L2"
    assert after["level"] != before["level"]


def test_removing_source_drops_m8(copy_skill):
    skill = copy_skill("good-exec")
    md = skill / "SKILL.md"
    text = md.read_text(encoding="utf-8")
    # keep an external numeric claim, delete only its anchor
    text = text.replace("样例语料共 3 个词，来源：https://example.com/sample（采集于 2026-11-01）。",
                        "全量语料覆盖率 92%。")
    md.write_text(text, encoding="utf-8")
    after = grade_skill(skill)
    assert next(c for c in after["checks"] if c["check_id"] == "M8")["status"] == "fail"
