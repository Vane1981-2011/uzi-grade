# legacy/uzi-inject.py — 已退役，不参与任何评分

这个脚本是上一代「金牌」的生成器，保留在此仅作历史记录。

## 它做了什么

`uzi-inject.py` 把 `UZI_MODULES` 里的 **Markdown 模板**注入到技能正文
（HARD-GATE、When NOT to Use、Safety & Guardrails、Failure Modes、
Completion Criteria），再用 D1–D10 十项检查打分。十项检查全部是
「某个字符串/文件在不在」的正则或存在性判断：

- 不执行技能里的任何脚本；
- 不运行任何任务；
- 不比较期望输出；
- 不检查被注入的护栏是否与技能领域相关。

因此它给出的「金牌」是**内部文档分级标签**：它证明模板被写进了文件，
不证明工具能完成任务。

## 结论（已确认，不再重复论证）

- 旧报告 `uzi-score-report.json`：约 88 个技能、86 个「金」，阈值 7.0 / 满分 11.5。
- 该「金牌」**不是工具实力证明**，在新体系中作废。
- 本脚本**不再参与** `uzi grade` / `uzi badge` / `uzi verify` / `uzi calibrate`
  的任何计算，也不被 `uzi selftest` 调用。

新体系请使用仓库根目录的 `uzi` CLI；它把每条结论写成
`{check_id, status, command, exit_code, output_sha256}`，第三方可复跑。

## 保留原因

审计可追溯：任何人可以对照旧脚本，验证「旧金牌来自模板注入」这一判断，
而不是只听一句声明。
