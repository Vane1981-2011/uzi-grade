# 验收记录（Acceptance）

本文件逐条记录 UZI v2 的完成判据、实际执行的命令、退出码与输出哈希。
每条结论都区分三档：

- **已证实**：有命令 + 退出码 + sha256，任何人都能复跑；
- **待验证**：工具本轮没有执行或只有静态证据；
- **最终判断**：基于已证实证据的结论，不超出证据范围。

环境：

- 仓库根目录 `uzi-grade/`（本文所有命令都在仓库根目录执行）
- 开发环境：临时 venv（`pip install -e .` + pytest）
- 干净环境：新建 venv，仅 `pip install -e .`，无 pytest
- 日期 2026-11-07

所有哈希均为 sha256；`verify_sha256` 是 `uzi verify` 对「重跑证据链后得到的
结果集合」计算的哈希，与报告文件的字节哈希（`report_sha256`）是两层不同的校验。

---

## 1. 判别力自证：`uzi selftest`

```bash
uzi selftest --ref ~/.claude/plugins/marketplaces/claude-plugins-official \
             --ref ~/.codex/skills/.system
```

| 项 | 值 |
|:--|:--|
| 退出码 | `0` |
| 注入变异 | 10 |
| 命中（kill） | **10 / 10**（阈值 9/10） |
| kill_rate | `1.0` |
| 未变异基线 | `base_level=L3`，`base_red=[]`，误报率 `0.0` |
| 38 个外部参照 | `reference_corpus=38`，崩溃 `0`，`unverifiable` 缺说明 `0` |
| verdict | `pass` |
| 输出文件哈希 | `df55107d28ff866217b22f7cde3f0ba77ce4e8dc51cef5fa70fe227d6383b5ff`（`/tmp/selftest-ref.json`） |
| 结果内 `selftest_sha256` | `76597397a67e56942246fe016ab1f0dae742094e3b7f770aeffcfe517402b36c` |

逐条变异与被迫变红的判据：

| 变异 | 目标判据 | 是否命中 | 新变红项 |
|:--|:--|:--|:--|
| 删 description | M1 | 是 | M1 |
| description 空泛化 | M1 | 是 | M1 |
| 删「何时不用」 | M2 | 是 | M2 |
| 步骤散文化 | M3 | 是 | M3 |
| 引用不存在文件 | M4 | 是 | M4 |
| 脚本强制 exit 1 | M5 | 是 | M5, M6 |
| 断言改 `assert True` | M6 | 是 | M6 |
| 删 HARD-GATE | M7 | 是 | M7 |
| 数字去来源 | M8 | 是 | M8 |
| 整段换成通用骨架 | M2 | 是 | M2, M3, M7 |

**已证实**：判据对 10 类缺陷有判别力，未变异基线不误报。
**待验证**：这里的「基线」是合成技能；38 个外部参照只校验了「不崩溃、不出
无说明的 unverifiable」，不校验它们的等级是否合理——那取决于契约差异，见第 5 节。

## 2. 报告可复算：`uzi verify` 两次一致

```bash
uzi grade --all examples --out /tmp/uzi-examples-final   # rc=1
uzi verify /tmp/uzi-examples-final/report.json           # 第一次
uzi verify /tmp/uzi-examples-final/report.json           # 第二次
```

| 项 | 第一次 | 第二次 |
|:--|:--|:--|
| 退出码 | `0` | `0` |
| matched | `4/4` | `4/4` |
| `report_sha256_match` | `True` | `True` |
| `report_seal_match` | `True` | `True` |
| `verify_sha256` | `83f1aad873fa0b5e02b64534b0fb0285626df884f880c275bc2c547822c519d1` | 同上 |

合成语料 4 项的等级（`/tmp/uzi-examples-final/report.json`，
文件哈希 `c2bf4da1d3afcb7c320880497a9e73dbc35d4f757966355bb1fbbeabd9b09f8e`）：

| 技能 | 档 | 等级 | 分数 | digest 前缀 |
|:--|:--|:--|--:|:--|
| good-exec | exec | L3 | 100.0 | `fee7e2389ab3` |
| good-prose | prose | L2 | 100.0 | `608c6251359e` |
| bad-broken-ref | prose | L1 | 83.33 | `fb5d78a9aa75` |
| bad-template | prose | L0 | 50.0 | `dcb72d2e7b22` |

`uzi grade --all` 因存在 L0/L1 而有 findings，按三态约定返回 `1`，不是失败。

**已证实**：对同一份报告复算两次，结果哈希完全一致；seal 校验能捕获报告被手工改写。

## 3. 干净环境一条命令跑通

```bash
python3 -m venv /tmp/uzi-clean
source /tmp/uzi-clean/bin/activate
pip install -e .
uzi grade --all examples --out /tmp/uzi-clean-out
```

| 项 | 值 |
|:--|:--|
| 安装 | 成功，零运行时依赖 |
| 退出码 | `1`（有 findings） |
| 扫描 | `scanned=4`，`L0=1 L1=1 L2=1 L3=1` |
| `report.md` 哈希 | `7918dba2d0f2b57cc86bbae169dfddb80bd1e9577ff3dbc91d3f852fc4729774`，与开发环境逐字节相同 |
| `report.json` 哈希 | `39b46b1e9288309590e46fbe4b4a07f8ce2fe24bda6b729c94e5917e7799d411`（含生成时间戳，故与开发环境不同） |
| 对该报告 `verify_sha256` | `83f1aad873fa0b5e02b64534b0fb0285626df884f880c275bc2c547822c519d1`，与第 2 节**完全相同** |

**已证实**：干净环境可安装、可评级，且复核结论与开发环境一致。

## 4. 覆盖率：91 项全部有等级

来源：`regrade.json`（file sha256
`f9a986fec25f2e35b575a03fdb74c7f431a32733dd3cec9324b86df823c53e4b`，
内嵌 `regrade_sha256 = b8e1b4c41155444adc3ffe80e3ec51e43ef9c54ec09e1948402b42576d081ff8`）。

| 项 | 值 |
|:--|:--|
| requested / graded / missing | `91 / 91 / 0` |
| 等级为空 | `0` |
| 等级分布 | `L0=17, L1=54, L2=20, L3=0, L4=0, L5=0` |
| `unverifiable` 记录 | `5`，其中缺说明（`missing` 为空）的 `0` 条 |
| 行为记录 | `60` 条，全部标为未执行并写明缺失项 |
| 旧标 GOLD | `40` → 新体系 L1/L2 共 `74` |
| 绝对私有路径 | 全仓 grep 本机用户目录前缀 → 0 命中 |

**已证实**：91/91 有等级，没有留空；无法判定的项都写明了缺什么证据。

## 5. 外部刻度与达标线

来源：`calibration.json`（file sha256
`165cfc4032b6f5cf8c17a7549392878a1c692be9843a3bbd79feca27f1ae1ac6`）。

38 个外部参照技能（`claude-plugins-official` 33 + `codex/.system` 5）按同一套判据分档：

| 档 | n | P50 | P75 | 等级分布 |
|:--|--:|--:|--:|:--|
| exec | 5 | 50.0 | 50.0 | 全部 L0 |
| prose | 33 | 50.0 | 66.67 | 全部 L0 |

达标判定（`regrade.json.summary`）：

| 组 | 达标 | 门槛 | 说明 |
|:--|:--|:--|:--|
| Top 20 旗舰 | **7 / 20** | ≥P75 且 ≥L2 | 13 项未达标，已逐条列出 |
| 其余 | **13 / 71** | ≥P50 且 ≥L2 | 58 项未达标，已逐条列出 |

未达标清单见 `regrade.md` 的「未达标清单（不修饰）」一节，Top20 未达标 slug：
`industry-analysis-assistant, expert-mode-tool, product-design-analyzer,
ab-test-analysis, canvas-strategy, cohort-analysis, enterprise-benchmarking,
financial-analysis-pipeline, financial-data-access, internal-control-assessment,
investment-risk-engine, maturity-model-assessment, prioritization`。

**已证实**：达标线没有因为结果不好看而下调；7/20 与 13/71 是真实结果。
**待验证**：38 个外部参照全部为 L0，主要反映「它们不遵循本工具的 SKILL.md
契约（无 HARD-GATE、无 source 标注）」而不是「质量差」；因此分位数只能当作
**同口径下的相对位置**，不能当作跨生态的质量排名。

## 6. 负向验收：删掉 HARD-GATE 必须掉级

```bash
cp -R examples/good-exec "$T/good-exec"
# 删除 SKILL.md 中 "## HARD-GATE" 整段（843 → 709 字节）
uzi grade "$T/good-exec" --json
```

| 项 | 值 |
|:--|:--|
| 退出码 | `1` |
| 等级 | L3 → **L2** |
| 失败判据 | `M7`（缺少 HARD-GATE 段落） |
| 结果 digest | `ad9cda06ef10c4602b9c312322bd463f85403fe764178d3b7f51ebdbe57ddb81` |
| 输出文件哈希 | `a8800d86f959c78afe4aa4f5d5c56a984f29334f0ef165701bc3bf44ada7f318`（`/tmp/neg.json`） |

**已证实**：删护栏即掉级，评级不是只升不降的装饰。

## 7. 辅助验收

| 项 | 命令 | 结果 |
|:--|:--|:--|
| 单元测试 | `python -m pytest -q` | `39 passed` |
| 徽章签发 | `uzi badge examples/good-prose --out /tmp/badge.svg --date 2026-11-07` | rc=0，`UZI-L2 · 6/6 · sha256:608c625 · 2026-11-07` |
| 徽章拒签 | `uzi badge examples/bad-template --out /tmp/badge-bad.svg` | rc=2，`评级未达 L1（L0 或无等级），不能签发徽章` |
| 截断可判性 | `uzi grade --all examples --max 2 --json` | rc=2，`truncation={truncated: True, limit: 2, omitted_count: 2, omitted: [good-exec, good-prose]}` |
| 行为判据 | `uzi behaviour B1 examples/good-prose` | rc=2，明确输出 `NOT EXECUTED` 与缺失项，不伪造通过 |

## 8. 本轮**没有**做的事（不得声称完成）

以下事项不属于 `uzi-grade` 仓库，本轮未执行，结论保持「待验证」：

1. **B1–B3 行为评测**：60 条记录全部 `unverifiable`（未调用模型、未跑 golden task）。
2. **M7 的真实拒答**：当前是静态覆盖检查（规则是否写明），不是让模型实际拒答 5 条越界语料。
3. **L4 / L5**：没有任何技能提交 `.uzi/attestation.json` 外部证据，故 91 项中 L4/L5 均为 0。
4. **Android 作品展示修复、作品展示合并 PDF、各工具 GitHub star/下载量逐项核验**：
   属于另外的交付物，本仓库不处理，也未修改任何已交付 PDF。

## 9. 最终判断

- 旧「金牌」是文本模板注入 + 正则/字符串打分的结果，不测任务正确性，已作废。
- L1–L3 现在只能由 `uzi grade` 签发，每条判据带命令、退出码与输出哈希，可被第三方复跑。
- 按外部刻度，当前**未达到**自己设定的优质达标线（Top20 7/20、其余 13/71）；这一结果如实公开，没有调阈值凑数。
- 头衔永远不等于实力：能复算的等级才是证据，不能复算的称呼只是称呼。
