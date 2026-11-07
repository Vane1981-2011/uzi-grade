# UZI calibration

- schema: `uzi-grade/calibration/1` / tool `1.0.0`
- percentile method: linear interpolation between closest ranks (R type 7)
- scanned: **38** reference skills

## 这份刻度是什么，不是什么

**是什么**：用同一套 M1–M8 判据、同一份统计口径，对**不是本工具作者写的**技能目录跑出的分数分布。它把「达到优质水准」翻译成一个可复算的数字（P50 / P75），任何人都可以按 README 的命令重新生成。

**不是什么**：

- 不是行业排名，也不是对外部技能质量的评价。38 个参照几乎全部落在 L0，主要因为 M2（六段结构 + 去模板化）与 M7（HARD-GATE + 5 类越界规则）是**本工具的交付契约**，普通第三方技能并未按此契约编写；这是契约差异，不是「它们很差」。分布因此偏高偏硬，只适合做**同口径**阈值。
- 不是任务正确性证明。M7 是静态护栏覆盖检查（文本里是否写明了拒绝规则），不是模型真实拒答；B1–B3 行为评测本轮未执行。
- 不是可以按需下调的分数线。分位值由数据算出；达不到就写「未达标」，不修改判据、不放宽阈值去凑结果。
- exec 与 prose 分档统计：prose 无 scripts/tests，M5/M6 记为 skip 并从分母剔除，所以两个档位的分数不可直接互比。prose 档在 L3（可复现）上缺少可执行证据，结构上最高只能到 L2。

| 来源 | 路径 | 存在 | 扫描数 |
|:--|:--|:--|--:|
| claude-plugins-official | `<HOME>/.claude/plugins/marketplaces/claude-plugins-official` | True | 33 |
| .system | `<HOME>/.codex/skills/.system` | True | 5 |

| 档 | n | min | P25 | P50 | P75 | max | mean |
|:--|--:|--:|--:|--:|--:|--:|--:|
| exec | 5 | 12.5 | 37.5 | 50.0 | 50.0 | 62.5 | 42.5 |
| prose | 33 | 33.33 | 50.0 | 50.0 | 66.67 | 66.67 | 54.04 |
| 全部 | 38 | 12.5 | 50.0 | 50.0 | 66.67 | 66.67 | 52.52 |

| 档 | L0 | L1 | L2 | L3 | L4 | L5 |
|:--|--:|--:|--:|--:|--:|--:|
| exec | 5 | 0 | 0 | 0 | 0 | 0 |
| prose | 33 | 0 | 0 | 0 | 0 | 0 |

calibration sha256: `cbbff98890ac9d2f274cf1c4b967518756f948564e1f60412379567e1b447a57`
