"""Command line interface: ``uzi <subcommand>``.

Exit codes are three-state everywhere, because "could not judge" must never be
confused with "judged and passed":

    0  all green
    1  judged, with findings
    2  cannot judge (empty corpus, missing path, truncated scan, judge defect)
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from . import __version__, badge, calibrate as calib, checks, grade, selftest, verify
from .util import SCHEMA


def _emit(obj, as_json: bool) -> None:
    if as_json:
        print(json.dumps(obj, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(obj, ensure_ascii=False, indent=2))


def single_exit_code(result: dict) -> int:
    if result.get("error"):
        return 2
    statuses = {c["status"] for c in result.get("checks", [])}
    if statuses & {"fail", "unverifiable"}:
        return 1
    return 0


def cmd_grade(args) -> int:
    if args.all:
        root = Path(args.all).expanduser()
        if not root.is_dir():
            print(f"uzi: path not found: {root}", file=sys.stderr)
            return 2
        report = grade.build_report(root, max_skills=args.max)
        out = Path(args.out).expanduser() if args.out else Path("uzi-report")
        if args.json:
            _emit(report, True)
        else:
            rj, rm = grade.write_report(report, out)
            print(f"wrote {rj}")
            print(f"wrote {rm}")
            rc = grade.exit_code_for(report)
            print(f"scanned={report['scanned']} levels={report['summary']['levels']} rc={rc}")
        return grade.exit_code_for(report)

    target = Path(args.target).expanduser() if args.target else None
    if target is None or not target.is_dir():
        print(f"uzi: path not found: {target}", file=sys.stderr)
        return 2
    if not (target / "SKILL.md").is_file():
        print(f"uzi: {target} has no SKILL.md", file=sys.stderr)
        return 2
    result = grade.grade_skill(target)
    if args.report:
        rp = Path(args.report).expanduser()
        rp.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if not args.json:
            print(f"wrote {rp}")
    if args.json:
        _emit(result, True)
    else:
        print(f"{result['name']}: {result['level']} ({result['level_label']}) "
              f"{result['passed']}/{result['applicable']} tier={result['tier']}")
        for c in result["checks"]:
            print(f"  {c['check_id']} {c['status']:<12} {c['detail']}")
        for r in result["reasons"]:
            print(f"  - {r}")
        print(f"  digest: {result['digest']}")
    return single_exit_code(result)


def cmd_badge(args) -> int:
    skill_dir = Path(args.target).expanduser()
    if not (skill_dir / "SKILL.md").is_file():
        print(f"uzi: {skill_dir} has no SKILL.md", file=sys.stderr)
        return 2
    try:
        payload = badge.make_badge(skill_dir, args.date,
                                   Path(args.report).expanduser() if args.report else None)
        svg = badge.render_svg(payload)
    except ValueError as exc:
        print(f"uzi badge: refused: {exc}", file=sys.stderr)
        return 2
    out = Path(args.out).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg, encoding="utf-8")
    if args.json:
        _emit(payload, True)
    else:
        print(f"wrote {out}")
        print(payload["text"])
        print(f"qr payload: {payload['qr_payload']}")
    return 0


def cmd_verify(args) -> int:
    path = Path(args.report).expanduser()
    if not path.is_file():
        print(f"uzi: report not found: {path}", file=sys.stderr)
        return 2
    root = Path(args.root).expanduser() if args.root else None
    result = verify.verify_report(path, root_override=root)
    _emit(result, True)
    rc = verify.verify_exit_code(result)
    print(f"verify: matched={result['matched']}/{result['skills']} "
          f"sha_match={result['report_sha256_match']} "
          f"seal_match={result['report_seal_match']} rc={rc}", file=sys.stderr)
    return rc


def cmd_check(args) -> int:
    """Re-run exactly one criterion -- the operation a report row cites."""
    skill_dir = Path(args.target).expanduser()
    if not (skill_dir / "SKILL.md").is_file():
        print(f"uzi: {skill_dir} has no SKILL.md", file=sys.stderr)
        return 2
    try:
        result = checks.run_one(skill_dir, args.check_id, rel=args.rel)
    except ValueError as exc:
        print(f"uzi check: {exc}", file=sys.stderr)
        return 2
    _emit(result.to_dict(), True)
    return {"pass": 0, "skip": 0, "fail": 1, "unverifiable": 2}[result.status]


def cmd_behaviour(args) -> int:
    """B1-B3 are not executed in this release; say so with rc 2, never fake it."""
    skill_dir = Path(args.target).expanduser()
    if not (skill_dir / "SKILL.md").is_file():
        print(f"uzi: {skill_dir} has no SKILL.md", file=sys.stderr)
        return 2
    stub = next((b for b in grade.behaviour_stubs(skill_dir, rel=args.rel)
                 if b["check_id"] == args.check_id), None)
    if stub is None:
        print(f"uzi behaviour: unknown check {args.check_id!r} "
              f"(expected B1, B2, B3)", file=sys.stderr)
        return 2
    _emit(stub, True)
    print(f"uzi behaviour: {args.check_id} NOT EXECUTED -- {stub['missing']}",
          file=sys.stderr)
    return 2


def cmd_selftest(args) -> int:
    result = selftest.run_selftest([Path(r) for r in (args.ref or [])])
    _emit(result, True)
    rc = selftest.selftest_exit_code(result)
    print(f"selftest: kill={result['kills']}/{result['mutations']} "
          f"base_red={result['base_red']} verdict={result['verdict']} rc={rc}", file=sys.stderr)
    return rc


def cmd_calibrate(args) -> int:
    if not args.ref:
        print("uzi calibrate: at least one --ref is required", file=sys.stderr)
        return 2
    for r in args.ref:
        if not Path(r).expanduser().is_dir():
            print(f"uzi: reference path not found: {r}", file=sys.stderr)
            return 2
    result = calib.calibrate(args.ref)
    out = Path(args.out).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md = out.with_suffix(".md")
    md.write_text(calib.render_markdown(result), encoding="utf-8")
    if args.json:
        _emit(result, True)
    else:
        print(f"wrote {out}")
        print(f"wrote {md}")
        s = result["overall"]
        print(f"scanned={result['scanned']} P50={s['p50']} P75={s['p75']}")
    return calib.calibration_exit_code(result)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="uzi", description="UZI v2 recomputable skill rating")
    p.add_argument("--version", action="version", version=f"uzi-grade {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    g = sub.add_parser("grade", help="grade one skill directory or a whole corpus")
    g.add_argument("target", nargs="?", help="skill directory")
    g.add_argument("--all", metavar="ROOT", help="grade every SKILL.md under ROOT")
    g.add_argument("--out", metavar="DIR", help="output directory for --all reports")
    g.add_argument("--max", type=int, default=None, help="stop after N skills (truncation -> rc 2)")
    g.add_argument("--report", metavar="PATH", help="write the single-skill result JSON here")
    g.add_argument("--json", action="store_true", help="print JSON")
    g.set_defaults(func=cmd_grade)

    b = sub.add_parser("badge", help="sign an SVG badge for a tool-computed grade")
    b.add_argument("target", help="skill directory")
    b.add_argument("--out", default="badge.svg")
    b.add_argument("--date", default=date.today().isoformat())
    b.add_argument("--report", help="refuse to sign unless the digest matches this report")
    b.add_argument("--json", action="store_true")
    b.set_defaults(func=cmd_badge)

    v = sub.add_parser("verify", help="recompute a report's evidence chain")
    v.add_argument("report")
    v.add_argument("--root", metavar="DIR",
                   help="locate the corpus here instead of the recorded root")
    v.add_argument("--json", action="store_true")
    v.set_defaults(func=cmd_verify)

    k = sub.add_parser("check", help="re-run one mechanical criterion (M1-M8)")
    k.add_argument("check_id", choices=checks.MECHANICAL_IDS)
    k.add_argument("target", help="skill directory")
    k.add_argument("--rel", help="relative label used in the recorded command")
    k.add_argument("--json", action="store_true")
    k.set_defaults(func=cmd_check)

    bh = sub.add_parser("behaviour", help="B1-B3 stub: records what is missing")
    bh.add_argument("check_id", choices=checks.BEHAVIOUR_IDS)
    bh.add_argument("target", help="skill directory")
    bh.add_argument("--rel", help="relative label used in the recorded command")
    bh.add_argument("--json", action="store_true")
    bh.set_defaults(func=cmd_behaviour)

    s = sub.add_parser("selftest", help="prove the criteria discriminate")
    s.add_argument("--ref", action="append", help="reference corpus root (repeatable)")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_selftest)

    c = sub.add_parser("calibrate", help="build an external scale from reference skills")
    c.add_argument("--ref", action="append", required=True)
    c.add_argument("--out", default="calibration.json")
    c.add_argument("--json", action="store_true")
    c.set_defaults(func=cmd_calibrate)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
