#!/usr/bin/env python3
"""Regrade an existing skill corpus against UZI v2 and publish the downgrades.

Input is a private corpus; output is redacted: every entry exposes the skill
name, slug, tier, level, score, the failing check IDs and the evidence digest,
never the skill body or an absolute path.

Usage:
  regrade.py --map pairs.json --corpus DIR [--corpus DIR ...] \
             --old uzi-score-report.json --calibration calibration.json \
             --out regrade

``pairs.json`` is a JSON list of ``[display_name, slug]``.  When a slug is not
found it may be listed in ``--alias`` (JSON object slug -> target slug) so the
alias inherits the target's grade instead of silently disappearing.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from uzi_grade.grade import LEVEL_ORDER, grade_skill  # noqa: E402
from uzi_grade.util import sha256_text  # noqa: E402


def find_skill(slug: str, corpora: list[Path]):
    for i, root in enumerate(corpora):
        cand = root / slug
        if (cand / "SKILL.md").is_file():
            return cand, i
    return None, None


def level_at_least(level: str | None, floor: str) -> bool:
    if not level or level not in LEVEL_ORDER:
        return False
    return LEVEL_ORDER.index(level) >= LEVEL_ORDER.index(floor)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--map", required=True)
    ap.add_argument("--corpus", action="append", required=True)
    ap.add_argument("--old", required=True)
    ap.add_argument("--calibration", required=True)
    ap.add_argument("--alias", default=None, help="JSON object slug -> target slug")
    ap.add_argument("--out", default="regrade")
    args = ap.parse_args()

    pairs = json.loads(Path(args.map).read_text(encoding="utf-8"))
    corpora = [Path(c).expanduser().resolve() for c in args.corpus]
    aliases = json.loads(Path(args.alias).read_text(encoding="utf-8")) if args.alias else {}
    old = json.loads(Path(args.old).read_text(encoding="utf-8"))
    old_scores = old.get("scores", {})
    calib = json.loads(Path(args.calibration).read_text(encoding="utf-8"))
    # prose skips M5/M6 and is scored on a smaller denominator, so its score
    # distribution must not be compared against the exec distribution.
    tier_thresholds = {}
    for tier in ("exec", "prose"):
        dist = calib.get("tiers", {}).get(tier, {}).get("score", {})
        tier_thresholds[tier] = {"p50": dist.get("p50"), "p75": dist.get("p75"),
                                 "n": dist.get("n", 0)}

    # Flagship = the 20 highest-scoring skills under the *old* scale that are
    # actually inside the 91-item map.  Ranking the whole old report would leak
    # skills outside the corpus and under-count the group (13/20 in an earlier
    # run), so restrict the candidate set first.
    pair_slugs = {slug for _, slug in pairs}
    ranked = sorted(
        ((slug, v) for slug, v in old_scores.items() if slug in pair_slugs),
        key=lambda kv: (-(kv[1].get("after") or 0), kv[0]),
    )
    top20 = [slug for slug, _ in ranked[:20]]
    top_set = set(top20)

    entries, missing = [], []
    for display, slug in pairs:
        path, corpus_idx = find_skill(slug, corpora)
        alias_of = None
        if path is None and slug in aliases:
            alias_of = aliases[slug]
            path, corpus_idx = find_skill(alias_of, corpora)
        before = old_scores.get(slug) or (old_scores.get(alias_of) if alias_of else None)
        if path is None:
            missing.append({"name": display, "slug": slug})
            continue
        g = grade_skill(path, behaviour=(slug in top_set))
        failed = [c["check_id"] for c in g["checks"] if c["status"] in ("fail", "unverifiable")]
        unverifiable = {c["check_id"]: c["missing"] for c in g["checks"]
                        if c["status"] == "unverifiable"}
        reason = []
        if before and "GOLD" in str(before.get("status", "")):
            reason.append(f"旧体系标 GOLD（{before.get('after')}/11.5），"
                          f"UZI v2 由工具签出 {g['level']}")
        if failed:
            reason.append("未通过/无证据: " + ",".join(failed))
        if g["tier"] == "prose" and not level_at_least(g["level"], "L3"):
            reason.append("prose 档无 scripts/tests，M5/M6 不适用，最高可达 L2（可复现需可执行证据）")
        entries.append({
            "name": display,
            "slug": slug,
            "path_display": f"<skill-corpus-{corpus_idx + 1}>/{path.name}",
            "alias_of": alias_of,
            "tier": g["tier"],
            "level": g["level"],
            "score": g["score"],
            "passed": g["passed"],
            "applicable": g["applicable"],
            "before": ({"score": before.get("after"), "status": before.get("status")}
                       if before else {"score": None, "status": "旧报告未收录"}),
            "checks": {c["check_id"]: c["status"] for c in g["checks"]},
            "failed_checks": failed,
            "unverifiable": unverifiable,
            "downgrade_reason": "; ".join(reason) or "无降级",
            "digest": g["digest"],
            "behaviour": g.get("behaviour", []),
            "evidence": {"command": f"uzi grade <skill-corpus>/{slug}",
                         "exit_code": 0 if not failed else 1,
                         "output_sha256": g["digest"]},
        })

    by_slug = {e["slug"]: e for e in entries}
    top20_rows = [by_slug[s] for s in top20 if s in by_slug]
    others = [e for e in entries if e["slug"] not in set(top20)]

    def floor_for(e, group):
        return tier_thresholds.get(e.get("tier") or "", {}).get(
            "p75" if group == "top20" else "p50")

    def meets(e, floor_score):
        return (floor_score is not None and level_at_least(e["level"], "L2")
                and e["score"] is not None and e["score"] >= floor_score)

    top_unmet = [e for e in top20_rows if not meets(e, floor_for(e, "top20"))]
    other_unmet = [e for e in others if not meets(e, floor_for(e, "others"))]

    levels = {lv: sum(1 for e in entries if e["level"] == lv) for lv in LEVEL_ORDER}
    summary = {
        "requested": len(pairs),
        "graded": len(entries),
        "missing": missing,
        "levels": levels,
        "gold_before": sum(1 for e in entries if "GOLD" in str(e["before"]["status"])),
        "levels_before_gold": sum(1 for e in entries if e["level"] in ("L1", "L2")),
        "thresholds": {"by_tier": tier_thresholds,
                       "source": "calibration.json tiers.<exec|prose>.score"},
        "behaviour": {"executed": 0, "records": sum(len(e.get("behaviour", []))
                                                    for e in entries),
                      "note": "B1-B3 行为评测本轮未执行，Top20 仅记录 unverifiable 及缺失项"},
        "top20": {"count": len(top20_rows),
                  "met": len(top20_rows) - len(top_unmet),
                  "unmet": [e["slug"] for e in top_unmet]},
        "others": {"count": len(others), "met": len(others) - len(other_unmet),
                   "unmet": [e["slug"] for e in other_unmet]},
    }
    report = {"schema": "uzi-grade/regrade/1", "summary": summary, "skills": entries}
    report["regrade_sha256"] = sha256_text(json.dumps(
        {k: v for k, v in report.items() if k != "regrade_sha256"},
        sort_keys=True, ensure_ascii=False))

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "regrade.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                                      encoding="utf-8")
    (out / "regrade.md").write_text(render(report, top20_rows), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"wrote {out/'regrade.json'}")
    print(f"wrote {out/'regrade.md'}")
    return 0 if len(entries) == len(pairs) else 1


def render(report: dict, top20_rows) -> str:
    s = report["summary"]
    th = s["thresholds"]["by_tier"]
    th_line = "; ".join(
        f"{tier}: P50={v.get('p50')} P75={v.get('p75')} (n={v.get('n')})"
        for tier, v in th.items())
    lines = [
        "# UZI v2 全库重评（91 项自有技能）",
        "",
        "> 结论先行：旧体系的「金牌」是文本模板注入 + 正则打分的结果，不是工具实力证明。",
        "> 本表所有等级由 `uzi grade` 工具签发；L4/L5 需人工录入带 URL 与采集日期的外部证据。",
        "",
        f"- 请求重评: **{s['requested']}** / 已评级: **{s['graded']}** / 缺失: {len(s['missing'])}",
        f"- 旧标 GOLD: **{s['gold_before']}** → 新体系 L1/L2: **{s['levels_before_gold']}**",
        f"- 等级分布: " + ", ".join(f"{k}={v}" for k, v in s["levels"].items()),
        f"- 达标线（按 exec/prose 分档，来自 calibration.json）: {th_line}",
        f"- Top20 达标: {s['top20']['met']}/{s['top20']['count']}；其余达标: "
        f"{s['others']['met']}/{s['others']['count']}",
        f"- 行为评测 B1-B3: 未执行（Top20 记录 {s['behaviour']['records']} 条 "
        f"unverifiable + 缺失说明）",
        f"- regrade sha256: `{report['regrade_sha256']}`",
        "",
    ]
    if s["missing"]:
        lines += ["## 未找到的技能", ""]
        lines += [f"- {m['name']} (`{m['slug']}`)" for m in s["missing"]]
        lines.append("")
    lines += [
        "## Top 20 旗舰（按旧体系分数取前 20）",
        "",
        "| 技能 | 档 | 旧分 | 新等级 | 分数 | 未过项 | 结论 |",
        "|:--|:--|--:|:--|--:|:--|:--|",
    ]
    tset = {e["slug"] for e in top20_rows}
    for e in sorted(top20_rows, key=lambda x: x["slug"]):
        ok = e["slug"] not in s["top20"]["unmet"]
        lines.append(f"| {e['name']} | {e['tier']} | {e['before']['score']} | {e['level']} | "
                     f"{e['score']} | {','.join(e['failed_checks']) or '-'} | "
                     f"{'达标' if ok else '未达标'} |")
    lines += ["", "## 未达标清单（不修饰）", ""]
    unmet = [e for e in report["skills"] if e["slug"] in
             set(s["top20"]["unmet"]) | set(s["others"]["unmet"])]
    if unmet:
        lines += ["| 技能 | 组 | 等级 | 分数 | 门槛 | 缺口 |", "|:--|:--|:--|--:|--:|:--|"]
        for e in sorted(unmet, key=lambda x: x["slug"]):
            group = "Top20" if e["slug"] in tset else "其余"
            floor = th.get(e.get("tier") or "", {}).get("p75" if group == "Top20" else "p50")
            gap = []
            if not level_at_least(e["level"], "L2"):
                gap.append(f"等级 {e['level']} < L2")
            if floor is None:
                gap.append("参照档无 P 分位数据")
            elif (e["score"] or 0) < floor:
                gap.append(f"分数 {e['score']} < {floor}")
            lines.append(f"| {e['name']} | {group} | {e['level']} | {e['score']} | {floor} | "
                         f"{'; '.join(gap)} |")
    else:
        lines.append("无。")
    lines += ["", "## 全部 91 项", "",
              "| 技能 | 档 | 新等级 | 分数 | 通过/适用 | 证据 sha256（前 12） |",
              "|:--|:--|:--|--:|:--|:--|"]
    for e in sorted(report["skills"], key=lambda x: x["slug"]):
        lines.append(f"| {e['name']} | {e['tier']} | {e['level']} | {e['score']} | "
                     f"{e['passed']}/{e['applicable']} | `{e['digest'][:12]}` |")
    lines += [
        "",
        "## 对外表述替换表",
        "",
        "| 旧表述 | 问题 | 替换为 |",
        "|:--|:--|:--|",
        "| 「UZI 金牌技能 86/88」 | 金牌来自模板注入与正则打分，不测任务正确性 | 「UZI v2 评级：L1–L3 由工具签发，逐项附命令/退出码/sha256」 |",
        "| 「金牌认证」 | 认证暗示第三方授权，实际无外部审核 | 「工具签发评级（L2 可交付）」 |",
        "| 「最优 / 第一 / 权威」 | 无同口径横向比较 | 「在 38 个外部参照技能中位于 P50/P75 分位」 |",
        "| 「技能很强」 | 无证据 | 「M1–M8 机械项 x/y 通过，M6 期望输出比对一致」 |",
        "| 「达到优质水准」 | 未定义 | 「≥ 参照语料 P75 且 ≥ L2，未达标项公开列出」 |",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
