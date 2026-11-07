"""Markdown / frontmatter parsing used by the static checks.

Deliberately dependency-free: SKILL.md files are YAML-fronted Markdown but the
frontmatter surface we need is tiny (scalars + simple lists), so a hand parser
is both sufficient and auditable.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.S)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.M)


@dataclass
class Doc:
    path: Path
    raw: str
    frontmatter: dict = field(default_factory=dict)
    body: str = ""
    headings: list[tuple[int, str]] = field(default_factory=list)


def _parse_scalar(value: str):
    value = value.strip()
    if not value:
        return ""
    if value[0] in "\"'":
        q = value[0]
        end = value.find(q, 1)
        return value[1:end] if end > 0 else value[1:]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        return [_parse_scalar(v) for v in inner.split(",")] if inner else []
    return value


def parse_frontmatter(text: str) -> tuple[dict, str]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    fm: dict = {}
    lines = m.group(1).splitlines()
    key = None
    i = 0
    while i < len(lines):
        line = lines[i]
        i += 1
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if re.match(r"^\s+-\s+", line) and key:
            fm.setdefault(key, [])
            if isinstance(fm[key], str):
                fm[key] = [fm[key]]
            fm[key].append(_parse_scalar(line.split("-", 1)[1]))
            continue
        if ":" in line and not line.startswith(" "):
            key, _, val = line.partition(":")
            key = key.strip()
            style = val.strip()
            if style in (">", "|", ">-", "|-", ">+", "|+"):
                block: list[str] = []
                while i < len(lines) and (not lines[i].strip() or re.match(r"^\s+\S", lines[i])):
                    block.append(lines[i].strip())
                    i += 1
                while block and not block[-1]:
                    block.pop()
                fm[key] = ("\n" if style.startswith("|") else " ").join(block).strip()
            elif style[:1] in ("'", '"') and style.count(style[0]) == 1:
                # A quoted scalar may wrap onto following lines:
                #   description: 'D2L ... 全链路系统。
                #
                #   > 当目标是 ...
                quote = style[0]
                buf = [style[1:]]
                while i < len(lines):
                    nxt = lines[i]
                    i += 1
                    if quote in nxt:
                        buf.append(nxt.split(quote, 1)[0])
                        break
                    buf.append(nxt.strip())
                fm[key] = " ".join(part.strip() for part in buf if part.strip()).strip()
            else:
                fm[key] = _parse_scalar(val)
            continue
        # YAML plain scalars may wrap onto indented continuation lines:
        #   description: Create a PRD ...
        #     Use when writing a PRD ...
        # Append them instead of silently truncating the description at the
        # first line break (a truncated description loses its trigger words).
        if key and line[:1] in (" ", "\t"):
            if re.match(r"^\s*[\w-]+\s*:", line):
                continue  # nested mapping such as metadata.category
            if isinstance(fm.get(key), str):
                merged = f"{fm[key]} {line.strip()}".strip()
                fm[key] = merged
    return fm, text[m.end():]


def load(path: Path) -> Doc:
    raw = path.read_text(encoding="utf-8", errors="replace")
    fm, body = parse_frontmatter(raw)
    heads = [(len(m.group(1)), m.group(2).strip()) for m in HEADING_RE.finditer(body)]
    return Doc(path=path, raw=raw, frontmatter=fm, body=body, headings=heads)


def sections(doc: Doc) -> dict[str, str]:
    """Map heading text -> section body, including nested subsections.

    A section ends at the next heading of the same or a higher level, so
    ``## 使用方式`` keeps its ``### 1. ...`` / ``### 2. ...`` children.
    """
    out: dict[str, str] = {}
    lines = doc.body.splitlines()
    positions = []
    for i, line in enumerate(lines):
        m = HEADING_RE.match(line)
        if m:
            positions.append((i, len(m.group(1)), m.group(2).strip()))
    for idx, (i, level, title) in enumerate(positions):
        end = len(lines)
        for j, lvl, _t in positions[idx + 1:]:
            if lvl <= level:
                end = j
                break
        out.setdefault(title.lower(), "\n".join(lines[i + 1:end]))
    return out


def first_paragraph(doc: Doc) -> str:
    text = HEADING_RE.sub("", doc.body)
    for block in re.split(r"\n\s*\n", text):
        block = block.strip()
        if block and not block.startswith(("|", "```", ">")):
            return block
    return ""


LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
BACKTICK_RE = re.compile(r"`([^`\n]+)`")
# Inside a backtick the path is usually one token of a longer command
# (`python scripts/ok.py --in fixtures/in.txt`), so pull the token out
# instead of treating the whole command as a path.
PATH_TOKEN_RE = re.compile(
    r"(?<![\w/.\-])((?:\./)?(?:references|assets|scripts|fixtures|tests)"
    r"/[\w./\-]+\.[A-Za-z0-9]+)"
)


def referenced_paths(doc: Doc) -> list[str]:
    found = []
    for m in LINK_RE.finditer(doc.body):
        target = m.group(1)
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        found.append(target.split("#")[0])
    for m in BACKTICK_RE.finditer(doc.body):
        for tok in PATH_TOKEN_RE.finditer(m.group(1)):
            found.append(tok.group(1))
    seen, ordered = set(), []
    for p in found:
        p = p.strip().lstrip("./")
        if p and p not in seen:
            seen.add(p)
            ordered.append(p)
    return ordered


NUM_CLAIM_RE = re.compile(
    r"(?<![\w.])(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*"
    r"(%|％|万|亿|倍|人|家|次|小时|分钟|秒|ms|MB|GB|TB|QPS|x\b)"
)
# A number is only an *external* claim when it is about the world, not a
# procedural threshold ("至少 2 个备选方案") or a layout constant ("200px").
CLAIM_CONTEXT_RE = re.compile(
    r"覆盖率?|覆盖|用户|客户|市场|行业|增长|下降|提升|降低|占比|份额|下载|星标|star|"
    r"统计|调研|benchmark|基准|数据|效率|准确率|成功率|营收|收入|利润|规模|转化|"
    r"留存|性能|延迟|耗时|QPS|样本|容量|价格|成本|企业|订单|资产|负债|融资|估值|"
    r"渗透|复购|GMV|MAU|DAU|INP|CLS|LCP|FID|压缩|节省|销售额|投资|收益|回报|ROI|"
    # "对标 X ~85% 等效体验" is an external parity claim even though it is
    # not a market statistic.
    r"等效|体验|对标|持平|领先|优于",
    re.I,
)
# Numbers that belong to the skill's own rubric, method definition, worked
# example or hypothetical are not external facts and must not be graded as
# unsourced claims.  This list exists because the first version of M8 flagged
# "95% CI", "库存库龄红线 70%", "权重 25%" and "如果放大 1000 倍" -- none of
# which are claims about the world.
EXCLUDED_CLAIM_CONTEXT_RE = re.compile(
    r"权重|评分|打分|总分|归一化|维度|分值|满分|档位|阈值|红线|区间|"
    r"上限|下限|最多|至少|不超过|不低于|不高于|报警|警戒|门槛|目标值|基准线|"
    r"置信度|校准|仓位|长期\s*[<>≥≤]|高于同行|低于同行|"
    r"\bCI\b|置信区间|显著性|p\s*[<>=]|z-?test|t-?test|chi-?squared|检验|统计方法|公式|"
    r"如果|假设|假如|倘若|思想实验|情景|反事实|一旦|"
    r"例如|比如|示例|举例|正例|反例|案例|样例",
    re.I,
)
URL_RE = re.compile(r"https?://\S+", re.I)
FILE_ANCHOR_RE = re.compile(
    r"`?(?:references|assets|fixtures|tests|docs)/[\w./\-]+", re.I)
# A named publication is a lead, not a verifiable anchor.  M8 treats it as
# `unverifiable`, never as `pass`, because the reader still cannot open it.
NAMED_SOURCE_RE = re.compile(
    r"(?:来源|source|出处|引用|引自|摘自|参见|详见|参考|据)\s*[:：]?\s*"
    r"[^\n]{0,80}?(?:白皮书|报告|年报|论文|研究|官网|统计|咨询|协会|基金会|"
    r"GitHub|PyPI|npm|arXiv|DOI|Damodaran|World Bank|Gartner|McKinsey|IDC|Statista)",
    re.I,
)
GUARD_RE = re.compile(
    r"禁止|不得|不允许|拒绝|DO NOT|NEVER|MUST NOT|HARD-?GATE|护栏|红线|越界",
    re.I,
)


def numeric_claim_details(doc: Doc) -> list[dict]:
    """Extract external numeric claims and classify how each one is anchored.

    ``anchor_kind`` is one of ``url`` / ``file`` / ``named`` / ``none``.
    Only ``url`` and ``file`` are independently checkable; ``named`` is
    reported but leaves the criterion unverifiable rather than passed.

    The body and the frontmatter description are scanned *separately*.  Joining
    them made the 80-character context window leak from one into the other:
    a description containing "示例" could silence a real claim at the end of
    the body, which is exactly the defect the selftest injects.
    """
    parts = [doc.body]
    desc = doc.frontmatter.get("description")
    if isinstance(desc, list):
        parts.append("\n".join(str(x) for x in desc))
    elif desc:
        parts.append(str(desc))
    claims = []
    for part in parts:
        claims.extend(_claims_in(clean_claim_text(part)))
    for i, claim in enumerate(claims):
        claim["index"] = i
    return claims


def _claims_in(body: str) -> list[dict]:
    """Sentence-scoped claim extraction.

    A fixed character window leaked exclusion words across sentence
    boundaries: "每个模块按 0-5 分打分" (a rubric instruction) silenced a real
    market statistic two lines later.  Claims, rubric exclusions and sources
    are therefore judged on the sentence that contains the number plus the
    sentence that follows it (where a source usually sits).
    """
    out = []
    for line in body.splitlines():
        if not line.strip():
            continue
        sentences = [s for s in re.split(r"(?<=[\u3002\uff01\uff1f!?\uff1b;])\s*", line.strip())
                     if s.strip()]
        for i, sentence in enumerate(sentences):
            if not CLAIM_CONTEXT_RE.search(sentence):
                continue  # procedural/layout number, not an external claim
            if EXCLUDED_CLAIM_CONTEXT_RE.search(sentence):
                continue  # rubric threshold / method definition / example
            window = " ".join(sentences[i:i + 2])
            for m in NUM_CLAIM_RE.finditer(sentence):
                unit = m.group(0)[len(m.group(1)):].strip()
                if unit in ("\u5206\u949f", "\u5c0f\u65f6", "\u79d2") and not re.search(
                        r"\u8017\u65f6|\u5ef6\u8fdf|\u6027\u80fd|\u54cd\u5e94|\u901f\u5ea6|\u5e73\u5747|"
                        r"P9[59]|benchmark", sentence, re.I):
                    continue  # a workflow duration, not a performance claim
                if URL_RE.search(window):
                    kind = "url"
                elif FILE_ANCHOR_RE.search(window):
                    kind = "file"
                elif NAMED_SOURCE_RE.search(window):
                    kind = "named"
                else:
                    kind = "none"
                out.append({
                    "number": m.group(0).strip(),
                    "anchor_kind": kind,
                    "context": " ".join(sentence.split())[:180],
                })
    return out


def numeric_claims_with_anchors(doc: Doc) -> tuple[int, int]:
    """Backwards-compatible count: (external claims, claims with a URL/file)."""
    claims = numeric_claim_details(doc)
    return len(claims), sum(1 for c in claims if c["anchor_kind"] in ("url", "file"))


def clean_claim_text(body: str) -> str:
    """Drop code, HTML, tables and checklists: they carry constants, not claims."""
    text = re.sub(r"```.*?```", "\n", body, flags=re.S)
    text = re.sub(r"`[^`\n]*`", "", text)
    text = re.sub(r"<!--.*?-->", "\n", text, flags=re.S)
    kept = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("|"):
            continue  # markdown table row
        if re.match(r"^[-*]\s*\[[ xX]\]", s):
            continue  # checklist item
        kept.append(line)
    return "\n".join(kept)


def shingles(text: str, n: int = 5) -> set[str]:
    words = re.findall(r"[\w\u4e00-\u9fff]+", text.lower())
    if len(words) < n:
        return {" ".join(words)} if words else set()
    return {" ".join(words[i:i + n]) for i in range(len(words) - n + 1)}


# A deliberately generic scaffold. If a skill's body is largely this text it was
# almost certainly produced by a template injector, not authored.
GENERIC_SKELETON = """
## 概述
本技能用于处理相关任务，提供标准化的流程与输出格式，帮助用户快速完成工作。

## 何时使用
当用户需要处理相关问题时使用本技能。适用于多种常见场景，可根据实际需求调整。

## 步骤
1. 理解用户需求，明确任务目标与边界条件。
2. 收集必要信息，进行结构化分析。
3. 按照标准流程生成输出，确保格式规范。
4. 检查输出质量，确认满足用户需求。

## 输出
按照标准格式输出结果，包含主要结论与关键信息，必要时提供补充说明。

## 失败模式
如果输入信息不足，向用户追问；如果出现错误，说明原因并给出替代方案。

## 验收标准
- 输出完整、格式规范、结论清晰
- 覆盖用户提出的全部要求
- 无遗漏、无错误、无歧义
"""
