"""Recompute a report's evidence chain and compare every sha256.

The comparison is deliberately redundant: every check's payload hash, the
skill fingerprint (tier, level, score, reasons, attestation), the summary,
the truncation record, the flagship block and the whole-report hash are all
recomputed.  A report that merely *looks* complete -- for example one whose
level was edited by hand, one with a dropped check, or one with an edited
``summary`` -- therefore fails even when the individual check hashes happen
to be intact.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import checks
from .grade import (discover_skills, entry_fingerprint, flagship_status,
                    grade_skill, report_sha256, summarise)
from .util import SCHEMA, TOOL_VERSION, normalise, sha256_text

VERIFY_SCHEMA = "uzi-grade/verify/1"

_COMPARE_KEYS = ("status", "exit_code", "output_sha256", "missing")


def _same_check(old: dict, new: dict) -> bool:
    if any(old.get(k) != new.get(k) for k in _COMPARE_KEYS):
        return False
    return normalise(str(old.get("command", ""))) == normalise(str(new.get("command", "")))


def _compare_checks(old_checks: list, new_checks: list, expected_ids: list) -> tuple:
    old = {c.get("check_id"): c for c in old_checks}
    new = {c.get("check_id"): c for c in new_checks}
    rows, bad = [], []
    for cid in expected_ids:
        if cid not in old:
            rows.append({"check_id": cid, "status": "missing-from-report"})
            bad.append(cid)
        elif cid not in new:
            rows.append({"check_id": cid, "status": "missing-from-recompute"})
            bad.append(cid)
        else:
            same = _same_check(old[cid], new[cid])
            rows.append({
                "check_id": cid,
                "status": "match" if same else "mismatch",
                "old_sha256": old[cid].get("output_sha256"),
                "new_sha256": new[cid].get("output_sha256"),
            })
            if not same:
                bad.append(cid)
    for cid in old:
        if cid not in expected_ids:
            rows.append({"check_id": cid, "status": "unexpected"})
            bad.append(cid)
    return rows, bad


def verify_report(report_path: Path, root_override: Path | None = None) -> dict:
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    root_raw = report.get("root")
    root = Path(root_override).expanduser() if root_override else (
        Path(root_raw) if root_raw else None)
    rows, entries = [], []

    for entry in report.get("skills", []):
        rel = entry.get("rel") or entry.get("name")
        skill_dir = (root / rel) if root is not None else None
        row = {
            "name": entry.get("name"),
            "rel": rel,
            "checks": [],
            "status": "match",
            "recorded_level": entry.get("level"),
            "recorded_tier": entry.get("tier"),
        }
        if skill_dir is None or not (skill_dir / "SKILL.md").is_file():
            row["status"] = "missing"
            rows.append(row)
            continue

        recomputed = grade_skill(skill_dir, rel=rel,
                                 behaviour=("behaviour" in entry))
        entries.append(recomputed)

        row["recomputed_level"] = recomputed.get("level")
        row["recomputed_tier"] = recomputed.get("tier")
        row["recomputed_score"] = recomputed.get("score")
        row["level_match"] = recomputed.get("level") == entry.get("level")
        row["tier_match"] = recomputed.get("tier") == entry.get("tier")
        row["score_match"] = recomputed.get("score") == entry.get("score")

        check_rows, bad_checks = _compare_checks(
            entry.get("checks", []), recomputed.get("checks", []),
            checks.MECHANICAL_IDS)
        row["checks"] = check_rows
        row["check_mismatch"] = bad_checks

        # Only flagship (Top-N) entries carry B1-B3 records.  A non-flagship
        # entry must *not* be asked for them: behaviour was not executed for
        # it, so an empty list is the correct recomputation, not a defect.
        if "behaviour" in entry:
            behaviour_rows, bad_behaviour = _compare_checks(
                entry.get("behaviour", []), recomputed.get("behaviour", []),
                checks.BEHAVIOUR_IDS)
        else:
            behaviour_rows, bad_behaviour = [], []
            if "behaviour" in recomputed:
                bad_behaviour = checks.BEHAVIOUR_IDS
        row["behaviour"] = behaviour_rows
        row["behaviour_mismatch"] = bad_behaviour

        row["entry_match"] = (entry_fingerprint(entry)
                              == entry_fingerprint(recomputed))
        if (not row["entry_match"] or not row["level_match"]
                or not row["tier_match"] or not row["score_match"]
                or bad_checks or bad_behaviour):
            row["status"] = "mismatch"
        rows.append(row)

    summary = summarise(entries)
    summary_match = summary == report.get("summary")

    scanned_match = False
    truncation_match = False
    recomputed_truncation = None
    if root is not None and root.is_dir():
        limit = (report.get("truncation") or {}).get("limit")
        found, recomputed_truncation = discover_skills(root, max_skills=limit)
        scanned_match = len(found) == report.get("scanned")
        truncation_match = recomputed_truncation == report.get("truncation")

    flagship_match = True
    if "flagships" in report:
        flagship_match = (flagship_status(entries, report.get("flagships") or [])
                          == report.get("flagship_status"))

    schema_match = report.get("schema") == SCHEMA
    tool_version_match = report.get("tool_version") == TOOL_VERSION
    # Internal consistency of the display field, independent of where the
    # corpus is re-run: the report must not claim a root it does not record.
    root_display_match = (report.get("root_display")
                          == normalise(str(Path(root_raw))) if root_raw else None)

    # Recompute the report hash from the *recomputed* entries.  The recorded
    # truncation/flagship blocks are included because they are separately
    # compared above; a hand-edited summary cannot survive this comparison.
    recomputed_report = {
        "schema": report.get("schema"),
        "tool_version": report.get("tool_version"),
        "root_display": report.get("root_display"),
        "scanned": report.get("scanned"),
        "truncation": report.get("truncation"),
        "summary": summary,
        "skills": entries,
    }
    if "flagships" in report:
        recomputed_report["flagships"] = report.get("flagships")
        recomputed_report["flagship_status"] = flagship_status(
            entries, report.get("flagships") or [])
    recomputed_hash = report_sha256(recomputed_report)
    # The seal is the hash of the report *as recorded*.  It catches edits to
    # any hashed field even when recomputation would silently restore the
    # truth, so a tampered file is reported twice rather than once.
    seal_hash = report_sha256(report)

    matched = sum(1 for r in rows if r["status"] == "match")
    result = {
        "schema": VERIFY_SCHEMA,
        "report": str(report_path),
        "report_schema": report.get("schema"),
        "skills": len(rows),
        "matched": matched,
        "mismatched": [r["name"] for r in rows if r["status"] == "mismatch"],
        "missing": [r["name"] for r in rows if r["status"] == "missing"],
        "level_mismatch": [r["name"] for r in rows if r.get("level_match") is False],
        "tier_mismatch": [r["name"] for r in rows if r.get("tier_match") is False],
        "score_mismatch": [r["name"] for r in rows if r.get("score_match") is False],
        "entry_mismatch": [r["name"] for r in rows if r.get("entry_match") is False],
        "check_mismatch": [r["name"] for r in rows if r.get("check_mismatch")],
        "behaviour_mismatch": [r["name"] for r in rows if r.get("behaviour_mismatch")],
        "summary_match": summary_match,
        "scanned_match": scanned_match,
        "truncation_match": truncation_match,
        "flagship_match": flagship_match,
        "schema_match": schema_match,
        "tool_version_match": tool_version_match,
        "root_display_match": root_display_match,
        "root_used": str(root) if root is not None else None,
        "recomputed_truncation": recomputed_truncation,
        "report_sha256_recorded": report.get("report_sha256"),
        "report_sha256_recomputed": recomputed_hash,
        "report_sha256_match": recomputed_hash == report.get("report_sha256"),
        "report_seal_sha256": seal_hash,
        "report_seal_match": seal_hash == report.get("report_sha256"),
        "rows": rows,
    }
    result["verify_sha256"] = sha256_text(json.dumps(
        {k: v for k, v in result.items() if k != "verify_sha256"},
        sort_keys=True, ensure_ascii=False))
    return result


def verify_exit_code(result: dict) -> int:
    if result["skills"] == 0:
        return 2
    if result["missing"]:
        return 2
    bad = (result["mismatched"] or result["level_mismatch"]
           or result["tier_mismatch"] or result["score_mismatch"]
           or result["entry_mismatch"] or result["check_mismatch"]
           or result["behaviour_mismatch"])
    if (bad or not result["summary_match"] or not result["scanned_match"]
            or not result["truncation_match"] or not result["flagship_match"]
            or not result["schema_match"] or not result["tool_version_match"]
            or not result["report_sha256_match"]
            or not result["report_seal_match"]
            or result["root_display_match"] is False):
        return 1
    return 0
