"""Tier detection, level assignment and report assembly."""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from . import checks
from .util import SCHEMA, TOOL_VERSION, normalise, sha256_file, sha256_text

EXCLUDE_DIR_NAMES = {"_base", "_standby", "vendored", "vendor", ".git", "node_modules",
                     "legacy", "_archived", "__pycache__", ".venv"}

LEVEL_ORDER = ["L0", "L1", "L2", "L3", "L4", "L5"]
LEVEL_LABEL = {
    "L0": "未达最低结构门槛",
    "L1": "存在",
    "L2": "可交付",
    "L3": "可复现",
    "L4": "被采用",
    "L5": "独立验证",
}

REQUIRED_FOR = {
    "L1": {"M1", "M2"},
    "L2": {"M1", "M2", "M3", "M4", "M8"},
    "L3": {"M1", "M2", "M3", "M4", "M6", "M7", "M8"},
}


def skill_digest(results) -> str:
    payload = [{"id": r.check_id, "status": r.status,
                "sha": r.to_dict()["output_sha256"]} for r in results]
    return sha256_text(json.dumps(payload, sort_keys=True, ensure_ascii=False))


def compute_level(results, tier: str, attestation=None) -> tuple[str, list]:
    """Return (level, reasons).  L1-L3 are tool-issued; L4/L5 need an attestation file."""
    by_id = {r.check_id: r for r in results}
    ok = {cid: (r.status == "pass") for cid, r in by_id.items()}
    reasons = []

    if not (ok.get("M1") and ok.get("M2")):
        return "L0", ["L0: M1 或 M2 未通过，未达最低结构门槛"]

    level = "L1"
    reasons.append("L1: M1+M2 通过")
    need2 = ["M3", "M4", "M8"]
    if tier == "exec":
        need2.append("M5")
    if all(ok.get(c) for c in need2):
        level = "L2"
        reasons.append("L2: " + "+".join(need2) + " 通过")
    else:
        reasons.append("L2 未达: " + ",".join(c for c in need2 if not ok.get(c)))
        return level, reasons

    if ok.get("M6") and ok.get("M7"):
        level = "L3"
        reasons.append("L3: M6 期望输出比对通过 + M7 护栏通过")
    else:
        reasons.append("L3 未达: " + ",".join(c for c in ("M6", "M7") if not ok.get(c)))

    granted = (attestation or {}).get("level") if attestation else None
    if granted in ("L4", "L5") and level == "L3":
        valid, why = validate_attestation(attestation)
        if valid:
            level = granted
            reasons.append(f"{granted}: 人工录入外部证据（{attestation.get('url')}, 采集 {attestation.get('collected_at')}）")
        else:
            reasons.append(f"{granted} 申报无效: {why}")
    return level, reasons


def validate_attestation(att: dict) -> tuple:
    if not att:
        return False, "无 attestation"
    url = str(att.get("url", ""))
    if not re.match(r"^https?://", url):
        return False, "缺 URL 或不是 http(s)"
    collected = str(att.get("collected_at", ""))
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", collected):
        return False, "缺采集日期（YYYY-MM-DD）"
    if att.get("level") not in ("L4", "L5"):
        return False, "level 必须是 L4 或 L5"
    return True, "ok"


def read_attestation(skill_dir: Path):
    for rel in (".uzi/attestation.json", "attestation.json"):
        p = skill_dir / rel
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return {"level": None, "error": f"{rel} 不可解析"}
    return None


def score_of(results) -> dict:
    applicable = [r for r in results if r.applies]
    passed = [r for r in applicable if r.status == "pass"]
    return {
        "passed": len(passed),
        "applicable": len(applicable),
        "score": round(100.0 * len(passed) / len(applicable), 2) if applicable else 0.0,
    }


def behaviour_stubs(skill_dir: Path, rel: str | None = None) -> list:
    """B1-B3 are behavioural and are *not* executed by this static tool.

    Emitting an honest ``unverifiable`` record (with the exact missing
    evidence) is better than silently omitting the criteria: the report then
    cannot be mistaken for a task-correctness proof.
    """
    specs = [
        ("B1", "golden task \u7aef\u5230\u7aef\u6267\u884c\u4e0e\u5224\u5206",
         "\u672a\u6267\u884c B1\uff1a\u7f3a golden task \u6267\u884c\u73af\u5883\u3001\u6a21\u578b\u8c03\u7528\u8bb0\u5f55\u4e0e\u5224\u5206\u7ed3\u679c"),
        ("B2", "\u8d8a\u754c\u8bf7\u6c42\u5b9e\u9645\u62d2\u7b54/\u964d\u7ea7",
         "\u672a\u6267\u884c B2\uff1a\u672c\u8f6e\u672a\u5411\u6a21\u578b\u53d1\u9001 3 \u6761\u8d8a\u754c\u8bf7\u6c42\uff0c\u65e0\u62d2\u7b54\u5f55\u50cf"),
        ("B3", "\u540c\u4efb\u52a1 3 \u6b21\u91c7\u6837\u7a33\u5b9a\u6027",
         "\u672a\u6267\u884c B3\uff1a\u7f3a 3 \u6b21\u91cd\u590d\u91c7\u6837\u7684\u901a\u8fc7\u7387\u8bb0\u5f55"),
    ]
    label = rel or skill_dir.name
    if label.startswith("./"):
        label = label[2:]
    out = []
    for cid, title, missing in specs:
        payload = {"check_id": cid, "status": "unverifiable", "title": title,
                   "missing": missing}
        out.append({
            "check_id": cid,
            "title": title,
            "kind": "behaviour",
            "status": "unverifiable",
            "executed": False,
            # Never put the private corpus path into a public report.  The
            # skill name is enough to locate the fixture again.
            "command": f"uzi behaviour {cid} ./{label}",
            "exit_code": 2,
            "output_sha256": sha256_text(json.dumps(payload, sort_keys=True,
                                                    ensure_ascii=False)),
            "missing": missing,
        })
    return out


def grade_skill(skill_dir: Path, rel: str | None = None, behaviour: bool = False) -> dict:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return {
            "name": skill_dir.name,
            "rel": rel or skill_dir.name,
            "error": "missing SKILL.md",
            "tier": None,
            "level": None,
            "score": None,
            "checks": [],
        }
    tier, results, _doc = checks.run_mechanical(skill_dir, rel=rel)
    att = read_attestation(skill_dir)
    level, reasons = compute_level(results, tier, att)
    sc = score_of(results)
    result = {
        "name": skill_dir.name,
        "rel": rel or skill_dir.name,
        "tier": tier,
        "level": level,
        "level_label": LEVEL_LABEL[level],
        "score": sc["score"],
        "passed": sc["passed"],
        "applicable": sc["applicable"],
        "reasons": reasons,
        "digest": skill_digest(results),
        "attestation": att,
        "checks": [r.to_dict() for r in results],
    }
    if behaviour:
        result["behaviour"] = behaviour_stubs(skill_dir, rel=rel)
    return result


# --------------------------------------------------------------------------- #
# corpus discovery
# --------------------------------------------------------------------------- #
def discover_skills(root: Path, max_skills: int | None = None):
    """Find skill directories (containing SKILL.md), excluding support dirs."""
    found = []
    root = root.resolve()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDE_DIR_NAMES)
        if "SKILL.md" in filenames:
            found.append(Path(dirpath))
    found.sort(key=lambda p: p.as_posix())
    truncated = False
    omitted = []
    if max_skills is not None and len(found) > max_skills:
        omitted = [p.name for p in found[max_skills:]]
        found = found[:max_skills]
        truncated = True
    return found, {"truncated": truncated, "limit": max_skills, "omitted_count": len(omitted),
                   "omitted": omitted}


def _check_fingerprint(check: dict) -> dict:
    """The part of a check record that a verifier must reproduce exactly."""
    return {
        "check_id": check.get("check_id"),
        "status": check.get("status"),
        "exit_code": check.get("exit_code"),
        "command": normalise(str(check.get("command", ""))),
        "output_sha256": check.get("output_sha256"),
        "missing": check.get("missing"),
    }


def _behaviour_fingerprint(check: dict) -> dict:
    return {
        "check_id": check.get("check_id"),
        "status": check.get("status"),
        "exit_code": check.get("exit_code"),
        "command": normalise(str(check.get("command", ""))),
        "output_sha256": check.get("output_sha256"),
        "missing": check.get("missing"),
    }


def entry_fingerprint(entry: dict) -> dict:
    """Canonical, path-normalised evidence for one skill.

    ``report_sha256`` is computed over these fingerprints.  Hashing only
    ``name/level/digest`` (the first version of this tool) let a hand-edited
    ``summary``, a dropped check, or a changed reason line survive audit.
    """
    return {
        "name": entry.get("name"),
        "rel": entry.get("rel"),
        "tier": entry.get("tier"),
        "level": entry.get("level"),
        "score": entry.get("score"),
        "passed": entry.get("passed"),
        "applicable": entry.get("applicable"),
        "digest": entry.get("digest"),
        "reasons": entry.get("reasons", []),
        "attestation": entry.get("attestation"),
        "error": entry.get("error"),
        "checks": [_check_fingerprint(c) for c in entry.get("checks", [])],
        "behaviour": [_behaviour_fingerprint(c) for c in entry.get("behaviour", [])],
    }


def report_fingerprint(report: dict) -> dict:
    """Everything in a report that is recomputable from the corpus.

    ``generated_at`` and the absolute ``root`` are deliberately excluded so a
    report remains hash-stable when moved to another machine.  ``root_display``
    is display metadata only (it changes when the same corpus is cloned to a
    different path, without any evidence changing); ``verify`` checks its
    internal consistency separately.  The summary and truncation record *are*
    included: they are claims about the evidence and must be reproducible.
    """
    return {
        "schema": report.get("schema"),
        "tool_version": report.get("tool_version"),
        "scanned": report.get("scanned"),
        "truncation": report.get("truncation"),
        "summary": report.get("summary"),
        "flagships": report.get("flagships"),
        "flagship_status": report.get("flagship_status"),
        "skills": [entry_fingerprint(e) for e in report.get("skills", [])],
    }


def report_sha256(report: dict) -> str:
    return sha256_text(json.dumps(report_fingerprint(report),
                                  sort_keys=True, ensure_ascii=False))


def build_report(root: Path, max_skills: int | None = None, top: list | None = None) -> dict:
    t0 = datetime.now(timezone.utc).replace(microsecond=0)
    root = Path(root).resolve()
    skills, trunc = discover_skills(root, max_skills)
    top_names = set(top or [])
    entries = [grade_skill(p, p.relative_to(root).as_posix(), behaviour=p.name in top_names)
               for p in skills]
    report = {
        "schema": SCHEMA,
        "tool_version": TOOL_VERSION,
        "generated_at": t0.isoformat().replace("+00:00", "Z"),
        "root": str(Path(root).resolve()),
        "root_display": normalise(str(Path(root).resolve())),
        "scanned": len(entries),
        "truncation": trunc,
        "summary": summarise(entries),
        "skills": entries,
        "report_sha256": "",
    }
    if top:
        report["flagships"] = top
        report["flagship_status"] = flagship_status(entries, top)
    report["report_sha256"] = report_sha256(report)
    return report


def summarise(entries) -> dict:
    levels = {k: 0 for k in LEVEL_ORDER}
    tiers = {"exec": 0, "prose": 0, "unknown": 0}
    statuses = {"pass": 0, "fail": 0, "unverifiable": 0, "skip": 0}
    for e in entries:
        if e.get("level"):
            levels[e["level"]] += 1
        tiers[e.get("tier") or "unknown"] += 1
        for c in e.get("checks", []):
            statuses[c["status"]] = statuses.get(c["status"], 0) + 1
    scores = [e["score"] for e in entries if e.get("score") is not None]
    behaviour_unverifiable = sum(
        1 for e in entries for b in e.get("behaviour", [])
        if b.get("status") == "unverifiable")
    return {
        "levels": levels,
        "tiers": tiers,
        "check_statuses": statuses,
        "score_mean": round(sum(scores) / len(scores), 2) if scores else None,
        "behaviour_unverifiable": behaviour_unverifiable,
        "behaviour_executed": 0,
        "errors": [e["name"] for e in entries if e.get("error")],
    }


def flagship_status(entries, top) -> dict:
    by_name = {e["name"]: e for e in entries}
    return {
        "requested": len(top),
        "found": sum(1 for n in top if n in by_name),
        "missing": [n for n in top if n not in by_name],
    }


def exit_code_for(report: dict) -> int:
    if report.get("truncation", {}).get("truncated"):
        return 2
    if report.get("scanned", 0) == 0:
        return 2
    statuses = report.get("summary", {}).get("check_statuses", {})
    if statuses.get("fail"):
        return 1
    if statuses.get("unverifiable"):
        return 1
    return 0


# --------------------------------------------------------------------------- #
# markdown rendering
# --------------------------------------------------------------------------- #
def render_markdown(report: dict, title: str = "UZI grade report") -> str:
    s = report["summary"]
    lines = [
        f"# {title}",
        "",
        f"- schema: `{report['schema']}` / tool `{report['tool_version']}`",
        f"- root: `{report.get('root_display', report.get('root'))}`",
        f"- scanned: **{report['scanned']}** skills",
        f"- levels: " + ", ".join(f"{k}={v}" for k, v in s["levels"].items()),
        f"- tiers: " + ", ".join(f"{k}={v}" for k, v in s["tiers"].items()),
        f"- check statuses: " + ", ".join(f"{k}={v}" for k, v in s["check_statuses"].items()),
        f"- behavioural B1-B3: executed={s.get('behaviour_executed', 0)}, "
        f"unverifiable records={s.get('behaviour_unverifiable', 0)} "
        f"(\u672c\u8f6e\u672a\u6267\u884c\u884c\u4e3a\u8bc4\u6d4b\uff0c\u4e0d\u80fd\u5f53\u4f5c\u4efb\u52a1\u6b63\u786e\u6027\u8bc1\u660e)",
        f"- report sha256: `{report['report_sha256']}`",
        "",
    ]
    if report.get("truncation", {}).get("truncated"):
        t = report["truncation"]
        lines += [f"> **SCAN TRUNCATED**: limit={t['limit']}, omitted={t['omitted_count']} "
                  f"(此处不完整，退出码 2)", ""]
    lines += ["| 技能 | 档 | 等级 | 分数 | 未通过项 |", "|:--|:--|:--|--:|:--|"]
    for e in report["skills"]:
        bad = ",".join(c["check_id"] for c in e.get("checks", [])
                       if c["status"] in ("fail", "unverifiable")) or "-"
        lines.append(f"| {e['name']} | {e.get('tier') or '-'} | {e.get('level') or '-'} | "
                     f"{e.get('score') if e.get('score') is not None else '-'} | {bad} |")
    return "\n".join(lines) + "\n"


def write_report(report: dict, out_dir: Path) -> tuple:
    out_dir.mkdir(parents=True, exist_ok=True)
    rj = out_dir / "report.json"
    rm = out_dir / "report.md"
    rj.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rm.write_text(render_markdown(report), encoding="utf-8")
    return rj, rm
