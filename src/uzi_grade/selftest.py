"""Prove the criteria discriminate: inject ten defects, demand nine kills.

A check suite that has never been shown to fail is a rubber stamp.  This module
builds a skill that satisfies every criterion, then mutates exactly one thing
at a time and records whether the criterion that is supposed to notice
actually does.

Two guards keep the judge honest:

* the un-mutated baseline must be all-green (a judge with a false positive is
  itself red, verdict ``judge-defect``, exit code 2);
* any reference corpus skill that crashes the judge or emits an
  ``unverifiable`` without naming what is missing is also a judge defect.
"""
from __future__ import annotations

import json
import re
import shutil
import tempfile
from pathlib import Path

from .grade import discover_skills, grade_skill
from .util import sha256_text

BASE_SKILL_MD = '''---
name: demo-good
description: >
  生成可复算的样例报告并校验输出哈希。Use when 用户需要样例报告或哈希校验；
  触发词：样例报告、哈希校验、复算。不适用于生产写入或删除操作。
---
# Demo Good

## 概述

把输入文本渲染成一份可复算的样例报告，并输出可核验的哈希。

## 何时使用

用户要求生成样例报告、核对输出哈希，或复算既有报告时使用。

## 何时不用

用户要求写入生产环境、删除文件或处理真实凭据时不要使用。

## 步骤

1. 读取 `fixtures/in.txt` 作为输入，运行 `python scripts/ok.py --in fixtures/in.txt`。
2. 检查 stdout 是否为 `ok` 且 rc=0，期望输出与 `tests/expected.json` 一致。
3. 用 `sha256sum` 比对输出文件，必须与记录值相同，否则失败。

## 输出

一份 Markdown 报告，包含输入摘要、输出哈希与复算命令。

## 失败模式

- 输入文件缺失时终止并报告路径，不要编造内容。
- 哈希不一致时保留两份输出供比对。

## HARD-GATE

1. 不得执行 `rm -rf` 等破坏性删除或覆写。
2. 不得输出密钥、token、凭据或任何外泄内容。
3. 未经审批不得写入生产环境或线上系统。
4. 不得绕过用户确认直接执行不可逆操作。
5. 不得编造证据、伪造数据或虚构来源。

## 验收标准

- [ ] 脚本 rc=0 且 stdout 为 `ok`
- [ ] 输出哈希与期望值一致
- [ ] 报告包含复算命令

覆盖率 92%，来源：https://example.com/benchmark（采集于 2026-11-01）。
'''

OK_SCRIPT = '''import argparse
p = argparse.ArgumentParser()
p.add_argument("--in", dest="inp", default="fixtures/in.txt")
a = p.parse_args()
print(open(a.inp, encoding="utf-8").read().strip())
'''

NOTES = "# notes\n\n支撑文件，用于让 references 链接可解析。\n"


def build_base(root: Path) -> Path:
    d = root / "demo-good"
    (d / "scripts").mkdir(parents=True)
    (d / "references").mkdir()
    (d / "fixtures").mkdir()
    (d / "tests").mkdir()
    (d / "SKILL.md").write_text(BASE_SKILL_MD, encoding="utf-8")
    (d / "scripts" / "ok.py").write_text(OK_SCRIPT, encoding="utf-8")
    (d / "references" / "notes.md").write_text(NOTES, encoding="utf-8")
    (d / "fixtures" / "in.txt").write_text("ok\n", encoding="utf-8")
    want = sha256_text("ok\n")
    (d / "tests" / "expected.json").write_text(
        json.dumps([{"argv": ["python", "scripts/ok.py"], "stdout_sha256": want}], indent=2),
        encoding="utf-8")
    return d


# --------------------------------------------------------------------------- #
# mutations: one defect each, aimed at exactly one criterion
# --------------------------------------------------------------------------- #
def _edit(path: Path, fn) -> None:
    path.write_text(fn(path.read_text(encoding="utf-8")), encoding="utf-8")


def _drop_section(text: str, title_kw: str) -> str:
    lines = text.splitlines()
    out, skip, level = [], False, 0
    for line in lines:
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m and title_kw in m.group(2):
            skip, level = True, len(m.group(1))
            continue
        if skip and m and len(m.group(1)) <= level:
            skip = False
        if not skip:
            out.append(line)
    return "\n".join(out)


def _drop_key(text: str, key: str) -> str:
    lines = text.splitlines()
    out, skipping = [], False
    for line in lines:
        if re.match(rf"^{key}:", line):
            skipping = True
            continue
        if skipping:
            if line.strip() and not line.startswith((" ", "\t")):
                skipping = False
            else:
                continue
        out.append(line)
    return "\n".join(out)


def mut_del_description(d: Path) -> None:
    _edit(d / "SKILL.md", lambda t: _drop_key(t, "description"))


def mut_vague_description(d: Path) -> None:
    _edit(d / "SKILL.md", lambda t: re.sub(
        r"(?ms)^description:.*?\n---", "description: 处理相关任务，提供标准化输出。\n---", t))


def mut_del_when_not(d: Path) -> None:
    def go(t: str) -> str:
        t = _drop_section(t, "何时不用")
        # the negative boundary is also stated in the description; the defect
        # is "no boundary at all", so the sentence goes too
        return t.replace("不适用于生产写入或删除操作。", "")
    _edit(d / "SKILL.md", go)


def mut_prose_steps(d: Path) -> None:
    _edit(d / "SKILL.md", lambda t: re.sub(
        r"(?ms)(## 步骤\n).*?(?=\n## )",
        r"\1\n先读取输入文件，然后运行脚本，最后比对哈希；整个过程按经验判断是否继续，没有编号也没有验收判据。\n",
        t))


def mut_broken_reference(d: Path) -> None:
    _edit(d / "SKILL.md", lambda t: t + "\n[缺失文件](references/nope.md)\n")


def mut_script_exit_1(d: Path) -> None:
    (d / "scripts" / "ok.py").write_text("raise SystemExit(1)\n", encoding="utf-8")


def mut_assert_true(d: Path) -> None:
    (d / "scripts" / "ok.py").write_text(
        OK_SCRIPT.replace('print(open(a.inp, encoding="utf-8").read().strip())',
                          'print("changed")'),
        encoding="utf-8")


def mut_del_hard_gate(d: Path) -> None:
    _edit(d / "SKILL.md", lambda t: _drop_section(t, "HARD-GATE"))


def mut_strip_source(d: Path) -> None:
    _edit(d / "SKILL.md", lambda t: t.replace(
        "覆盖率 92%，来源：https://example.com/benchmark（采集于 2026-11-01）。",
        "覆盖率 92%。"))


def mut_generic_skeleton(d: Path) -> None:
    from .parse import GENERIC_SKELETON
    text = (d / "SKILL.md").read_text(encoding="utf-8")
    fm = re.match(r"(?s)---\n.*?\n---\n", text).group(0)
    (d / "SKILL.md").write_text(fm + GENERIC_SKELETON, encoding="utf-8")


MUTATIONS = {
    "del-description": ("M1", mut_del_description),
    "vague-description": ("M1", mut_vague_description),
    "del-when-not": ("M2", mut_del_when_not),
    "prose-steps": ("M3", mut_prose_steps),
    "broken-reference": ("M4", mut_broken_reference),
    "script-exit-1": ("M5", mut_script_exit_1),
    "assert-true": ("M6", mut_assert_true),
    "del-hard-gate": ("M7", mut_del_hard_gate),
    "strip-source": ("M8", mut_strip_source),
    "generic-skeleton": ("M2", mut_generic_skeleton),
}


def run_selftest(ref_roots=None) -> dict:
    with tempfile.TemporaryDirectory(prefix="uzi-selftest-") as tmp:
        tmp_root = Path(tmp)
        base = build_base(tmp_root / "clean")
        clean = grade_skill(base)
        base_red = [c for c in clean["checks"] if c["status"] != "pass"]
        base_level = clean["level"]

        kills, rows = 0, []
        for name, (target, mutate) in MUTATIONS.items():
            # keep the directory name identical to frontmatter `name`, otherwise
            # M1 goes red for an artefact of the harness instead of the defect
            work = tmp_root / ("m-" + name) / base.name
            work.parent.mkdir(parents=True)
            shutil.copytree(base, work)
            mutate(work)
            graded = grade_skill(work)
            target_check = next((c for c in graded["checks"] if c["check_id"] == target), None)
            killed = bool(target_check and target_check["status"] == "fail")
            before = {c["check_id"]: c["status"] for c in clean["checks"]}
            new_red = sorted(c["check_id"] for c in graded["checks"]
                             if c["status"] != "pass" and before.get(c["check_id"]) == "pass")
            kills += killed
            rows.append({
                "mutation": name, "target": target, "killed": killed,
                "target_status": target_check["status"] if target_check else None,
                "level_before": base_level, "level_after": graded["level"],
                "newly_red": new_red,
            })

        ref_rows = []
        for root in (ref_roots or []):
            ref_skills, _trunc = discover_skills(Path(root).expanduser())
            for skill_dir in ref_skills:
                try:
                    g = grade_skill(skill_dir)
                except Exception as exc:  # a crash is a checker defect
                    ref_rows.append({"skill": skill_dir.name, "crash": repr(exc)})
                    continue
                ref_rows.append({
                    "skill": skill_dir.name, "level": g["level"], "score": g["score"],
                    "tier": g["tier"],
                    "unverifiable_without_missing": [
                        c["check_id"] for c in g["checks"]
                        if c["status"] == "unverifiable" and not c["missing"]],
                })

    crashes = [r for r in ref_rows if r.get("crash")]
    schema_bad = [r["skill"] for r in ref_rows if r.get("unverifiable_without_missing")]
    applicable = len([c for c in clean["checks"] if c["status"] != "skip"])
    fp_rate = round(len(base_red) / max(applicable, 1), 4)
    kill_rate = round(kills / len(MUTATIONS), 4)
    ok = kill_rate >= 0.9 and not base_red and not crashes and not schema_bad
    result = {
        "schema": "uzi-grade/selftest/1",
        "mutations": len(MUTATIONS),
        "kills": kills,
        "kill_rate": kill_rate,
        "kill_threshold": 0.9,
        "base_level": base_level,
        "base_red": [c["check_id"] for c in base_red],
        "base_false_positive_rate": fp_rate,
        "fp_threshold": 0.10,
        "reference_corpus": ref_rows,
        "reference_crashes": crashes,
        "reference_schema_violations": schema_bad,
        "verdict": "pass" if ok else ("judge-defect" if base_red or crashes or schema_bad else "kill-rate-too-low"),
        "rows": rows,
    }
    result["selftest_sha256"] = sha256_text(json.dumps(
        {k: v for k, v in result.items() if k != "selftest_sha256"},
        sort_keys=True, ensure_ascii=False))
    return result


def selftest_exit_code(result: dict) -> int:
    if result["verdict"] != "pass":
        return 2 if result["verdict"] == "judge-defect" else 1
    return 0
