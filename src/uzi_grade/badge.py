"""Sign a badge only for a grade the tool itself computed.

The badge carries a fixed text line ``UZI-Lx · n/n · sha256:xxxxxxx · date`` and
a QR code that holds the full ``sha256:<digest>`` so anyone can re-run
``uzi verify`` and compare.  No template, no title, no self-awarded label.
"""
from __future__ import annotations

import json
from pathlib import Path
from xml.sax.saxutils import escape

from . import qr
from .grade import grade_skill

FORBIDDEN_WORDS = ["金牌", "认证", "最优", "第一", "权威", "gold", "certified", "best-in-class"]

WIDTH, HEIGHT = 760, 220


def badge_payload(result: dict, date: str) -> dict:
    level = result.get("level") or ""
    if level in ("", "L0", None):
        raise ValueError("评级未达 L1（L0 或无等级），不能签发徽章")
    passed = result.get("passed", 0)
    applicable = result.get("applicable", 0)
    digest = result.get("digest", "")
    text = f"UZI-{level} · {passed}/{applicable} · sha256:{digest[:7]} · {date}"
    return {
        "level": level,
        "passed": passed,
        "applicable": applicable,
        "digest": digest,
        "date": date,
        "text": text,
        "qr_payload": f"sha256:{digest}",
    }


def render_svg(payload: dict) -> str:
    mod = qr.encode(payload["qr_payload"])
    n = len(mod)
    module = 3.2
    qr_size = n * module
    qr_x = WIDTH - qr_size - 30
    qr_y = (HEIGHT - qr_size) / 2
    path = qr.to_svg_path(mod, qr_x, qr_y, module)
    for word in FORBIDDEN_WORDS:
        if word in payload["text"]:
            raise ValueError(f"badge text contains forbidden word {word!r}")
    line1 = f"UZI-{payload['level']}"
    line2 = f"{payload['passed']}/{payload['applicable']} checks passed"
    line3 = f"sha256:{payload['digest'][:7]}"
    line4 = payload["date"]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="{escape(payload['text'])}">
  <title>{escape(payload['text'])}</title>
  <rect width="{WIDTH}" height="{HEIGHT}" rx="18" fill="#0b1020"/>
  <rect x="1.5" y="1.5" width="{WIDTH - 3}" height="{HEIGHT - 3}" rx="17" fill="none" stroke="#2b3557" stroke-width="3"/>
  <text x="34" y="78" font-family="ui-monospace,SFMono-Regular,Menlo,monospace" font-size="52" font-weight="700" fill="#7ee787">{escape(line1)}</text>
  <text x="34" y="118" font-family="ui-monospace,SFMono-Regular,Menlo,monospace" font-size="22" fill="#c9d1d9">{escape(line2)}</text>
  <text x="34" y="154" font-family="ui-monospace,SFMono-Regular,Menlo,monospace" font-size="22" fill="#8b949e">{escape(line3)}</text>
  <text x="34" y="188" font-family="ui-monospace,SFMono-Regular,Menlo,monospace" font-size="18" fill="#6e7681">{escape(line4)}</text>
  <rect x="{qr_x - 8:.1f}" y="{qr_y - 8:.1f}" width="{qr_size + 16:.1f}" height="{qr_size + 16:.1f}" fill="#ffffff" rx="6"/>
  <path d="{path}" fill="#0b1020"/>
</svg>
"""


def make_badge(skill_dir: Path, date: str, report: Path | None = None) -> dict:
    result = grade_skill(skill_dir)
    if result.get("error"):
        raise ValueError(f"{skill_dir}: {result['error']}")
    if report is not None:
        rep = json.loads(Path(report).read_text(encoding="utf-8"))
        recorded = next((e for e in rep.get("skills", [])
                         if e.get("name") == result["name"]), None)
        if recorded is None:
            raise ValueError(f"{result['name']} 不在报告 {report} 中")
        if recorded.get("digest") != result.get("digest"):
            raise ValueError("报告中的 digest 与当前目录复算不一致，拒绝签发")
    return badge_payload(result, date)
