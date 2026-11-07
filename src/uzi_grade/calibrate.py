"""Build an external scale from third-party skills.

The rating only means something if it is anchored to work we did not write.
``calibrate`` runs the same eleven criteria over reference corpora and records
the score distribution per tier, so a claim like "above the P75 of the
reference corpus" becomes a number anyone can recompute.

Percentile method: linear interpolation between closest ranks (the same
definition as numpy's default ``linear`` / R's type 7).  For n sorted values
x[0..n-1] and p in [0,1], rank = p*(n-1); the result is interpolated between
floor(rank) and ceil(rank).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from .grade import discover_skills, grade_skill
from .util import SCHEMA, TOOL_VERSION, normalise, sha256_text

CALIBRATION_SCHEMA = "uzi-grade/calibration/1"


def percentile(values, p: float):
    """Linear-interpolation percentile (R type 7).  Returns None for no data."""
    vals = sorted(v for v in values if v is not None)
    if not vals:
        return None
    if len(vals) == 1:
        return float(vals[0])
    rank = p * (len(vals) - 1)
    lo, hi = math.floor(rank), math.ceil(rank)
    if lo == hi:
        return float(vals[lo])
    frac = rank - lo
    return round(vals[lo] * (1 - frac) + vals[hi] * frac, 2)


def distribution(values) -> dict:
    vals = sorted(v for v in values if v is not None)
    return {
        "n": len(vals),
        "min": vals[0] if vals else None,
        "p25": percentile(vals, 0.25),
        "p50": percentile(vals, 0.50),
        "p75": percentile(vals, 0.75),
        "max": vals[-1] if vals else None,
        "mean": round(sum(vals) / len(vals), 2) if vals else None,
    }


def calibrate(roots, labels=None) -> dict:
    roots = [Path(r).expanduser() for r in roots]
    labels = labels or [r.name for r in roots]
    rows, per_root = [], []
    for root, label in zip(roots, labels):
        if not root.is_dir():
            per_root.append({"root": normalise(str(root)), "label": label,
                             "exists": False, "scanned": 0})
            continue
        skills, _trunc = discover_skills(root)
        per_root.append({"root": normalise(str(root)), "label": label,
                         "exists": True, "scanned": len(skills)})
        for skill_dir in skills:
            try:
                g = grade_skill(skill_dir)
            except Exception as exc:  # never let one bad skill abort calibration
                rows.append({"skill": skill_dir.name, "source": label,
                             "error": repr(exc), "tier": None, "score": None,
                             "level": None})
                continue
            rows.append({
                "skill": skill_dir.name,
                "slug": skill_dir.name,
                "source": label,
                "tier": g["tier"],
                "level": g["level"],
                "score": g["score"],
                "passed": g["passed"],
                "applicable": g["applicable"],
                "digest": g["digest"],
                "evidence": {
                    "command": f"uzi grade {skill_dir.name}",
                    "exit_code": 0 if g["score"] == 100.0 else 1,
                    "output_sha256": g["digest"],
                },
                "failed_checks": [c["check_id"] for c in g["checks"]
                                  if c["status"] in ("fail", "unverifiable")],
                "unverifiable": {c["check_id"]: c["missing"] for c in g["checks"]
                                 if c["status"] == "unverifiable"},
            })

    tiers = {}
    for tier in ("exec", "prose"):
        group = [r for r in rows if r.get("tier") == tier and not r.get("error")]
        tiers[tier] = {
            "skills": len(group),
            "score": distribution([r["score"] for r in group]),
            "levels": {lv: sum(1 for r in group if r["level"] == lv)
                       for lv in ("L0", "L1", "L2", "L3", "L4", "L5")},
        }
    all_scores = [r["score"] for r in rows if not r.get("error")]
    result = {
        "schema": CALIBRATION_SCHEMA,
        "tool_schema": SCHEMA,
        "tool_version": TOOL_VERSION,
        "percentile_method": "linear interpolation between closest ranks (R type 7)",
        "roots": per_root,
        "scanned": len([r for r in rows if not r.get("error")]),
        "errors": [r for r in rows if r.get("error")],
        "tiers": tiers,
        "overall": distribution(all_scores),
        "skills": rows,
    }
    result["calibration_sha256"] = sha256_text(json.dumps(
        {k: v for k, v in result.items() if k != "calibration_sha256"},
        sort_keys=True, ensure_ascii=False))
    return result


def calibration_exit_code(result: dict) -> int:
    if result["scanned"] == 0:
        return 2
    if result["errors"]:
        return 1
    return 0


def render_markdown(result: dict) -> str:
    lines = [
        "# UZI calibration",
        "",
        f"- schema: `{result['schema']}` / tool `{result['tool_version']}`",
        f"- percentile method: {result['percentile_method']}",
        f"- scanned: **{result['scanned']}** reference skills",
        "",
        "## 这份刻度是什么，不是什么",
        "",
        "**是什么**：用同一套 M1–M8 判据、同一份统计口径，对**不是本工具作者写的**技能目录"
        "跑出的分数分布。它把「达到优质水准」翻译成一个可复算的数字（P50 / P75），"
        "任何人都可以按 README 的命令重新生成。",
        "",
        "**不是什么**：",
        "",
        "- 不是行业排名，也不是对外部技能质量的评价。38 个参照几乎全部落在 L0，"
        "主要因为 M2（六段结构 + 去模板化）与 M7（HARD-GATE + 5 类越界规则）"
        "是**本工具的交付契约**，普通第三方技能并未按此契约编写；这是契约差异，"
        "不是「它们很差」。分布因此偏高偏硬，只适合做**同口径**阈值。",
        "- 不是任务正确性证明。M7 是静态护栏覆盖检查（文本里是否写明了拒绝规则），"
        "不是模型真实拒答；B1–B3 行为评测本轮未执行。",
        "- 不是可以按需下调的分数线。分位值由数据算出；达不到就写「未达标」，"
        "不修改判据、不放宽阈值去凑结果。",
        "- exec 与 prose 分档统计：prose 无 scripts/tests，M5/M6 记为 skip 并从分母剔除，"
        "所以两个档位的分数不可直接互比。prose 档在 L3（可复现）上缺少可执行证据，"
        "结构上最高只能到 L2。",
        "",
        "| 来源 | 路径 | 存在 | 扫描数 |",
        "|:--|:--|:--|--:|",
    ]
    for r in result["roots"]:
        lines.append(f"| {r['label']} | `{r['root']}` | {r['exists']} | {r['scanned']} |")
    lines += ["", "| 档 | n | min | P25 | P50 | P75 | max | mean |",
              "|:--|--:|--:|--:|--:|--:|--:|--:|"]
    for tier, t in result["tiers"].items():
        s = t["score"]
        lines.append(f"| {tier} | {s['n']} | {s['min']} | {s['p25']} | {s['p50']} | "
                     f"{s['p75']} | {s['max']} | {s['mean']} |")
    s = result["overall"]
    lines.append(f"| 全部 | {s['n']} | {s['min']} | {s['p25']} | {s['p50']} | "
                 f"{s['p75']} | {s['max']} | {s['mean']} |")
    lines += ["", "| 档 | L0 | L1 | L2 | L3 | L4 | L5 |", "|:--|--:|--:|--:|--:|--:|--:|"]
    for tier, t in result["tiers"].items():
        lv = t["levels"]
        lines.append(f"| {tier} | {lv['L0']} | {lv['L1']} | {lv['L2']} | {lv['L3']} | "
                     f"{lv['L4']} | {lv['L5']} |")
    lines += ["", f"calibration sha256: `{result['calibration_sha256']}`", ""]
    return "\n".join(lines)
