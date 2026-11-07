# UZI v2 全库重评（91 项自有技能）

> 结论先行：旧体系的「金牌」是文本模板注入 + 正则打分的结果，不是工具实力证明。
> 本表所有等级由 `uzi grade` 工具签发；L4/L5 需人工录入带 URL 与采集日期的外部证据。

- 请求重评: **91** / 已评级: **91** / 缺失: 0
- 旧标 GOLD: **40** → 新体系 L1/L2: **74**
- 等级分布: L0=17, L1=54, L2=20, L3=0, L4=0, L5=0
- 达标线（按 exec/prose 分档，来自 calibration.json）: exec: P50=50.0 P75=50.0 (n=5); prose: P50=50.0 P75=66.67 (n=33)
- Top20 达标: 7/20；其余达标: 13/71
- 行为评测 B1-B3: 未执行（Top20 记录 60 条 unverifiable + 缺失说明）
- regrade sha256: `b8e1b4c41155444adc3ffe80e3ec51e43ef9c54ec09e1948402b42576d081ff8`

## Top 20 旗舰（按旧体系分数取前 20）

| 技能 | 档 | 旧分 | 新等级 | 分数 | 未过项 | 结论 |
|:--|:--|--:|:--|--:|:--|:--|
| A/B测试分析 | prose | 10.5 | L1 | 66.67 | M3,M7 | 未达标 |
| agent-research | prose | 10.5 | L2 | 83.33 | M7 | 达标 |
| 商业模式画布 | prose | 10.5 | L1 | 66.67 | M3,M7 | 未达标 |
| 队列分析 | prose | 10.5 | L1 | 66.67 | M3,M7 | 未达标 |
| 合同风险扫描 | prose | 10.5 | L2 | 83.33 | M7 | 达标 |
| PRD需求文档生成 | prose | 10.5 | L2 | 83.33 | M7 | 达标 |
| D2L拆解学习协议 | prose | 11.25 | L2 | 83.33 | M7 | 达标 |
| 保密协议起草 | prose | 10.5 | L2 | 83.33 | M7 | 达标 |
| enterprise-benchmarking | prose | 10.5 | L1 | 50.0 | M3,M7,M8 | 未达标 |
| expert-mode-tool | prose | 10.75 | L0 | 33.33 | M1,M3,M7,M8 | 未达标 |
| financial-analysis-pipeline | prose | 10.5 | L1 | 66.67 | M3,M7 | 未达标 |
| financial-data-access | prose | 10.5 | L1 | 66.67 | M3,M7 | 未达标 |
| 财务报表分析 | prose | 10.5 | L2 | 83.33 | M7 | 达标 |
| 第一性原理推理引擎 | prose | 10.75 | L2 | 83.33 | M7 | 达标 |
| 行业分析助手 | prose | 11.0 | L1 | 66.67 | M3,M7 | 未达标 |
| 内部控制评估 | prose | 10.5 | L1 | 66.67 | M3,M7 | 未达标 |
| investment-risk-engine | prose | 10.5 | L1 | 66.67 | M3,M7 | 未达标 |
| 成熟度模型评估 | prose | 10.5 | L0 | 50.0 | M1,M7,M8 | 未达标 |
| 优先级排序 | prose | 10.5 | L1 | 66.67 | M3,M7 | 未达标 |
| product-design-analyzer | prose | 10.75 | L1 | 50.0 | M3,M4,M7 | 未达标 |

## 未达标清单（不修饰）

| 技能 | 组 | 等级 | 分数 | 门槛 | 缺口 |
|:--|:--|:--|--:|--:|:--|
| A/B测试分析 | Top20 | L1 | 66.67 | 66.67 | 等级 L1 < L2 |
| anti-ai-writing | 其余 | L1 | 66.67 | 50.0 | 等级 L1 < L2 |
| audit-analyst-cross-validation | 其余 | L1 | 66.67 | 50.0 | 等级 L1 < L2 |
| cangjie-skill | 其余 | L1 | 62.5 | 50.0 | 等级 L1 < L2 |
| 商业模式画布 | Top20 | L1 | 66.67 | 66.67 | 等级 L1 < L2 |
| capability-extension | 其余 | L1 | 66.67 | 50.0 | 等级 L1 < L2 |
| cinematic-video-generator | 其余 | L1 | 66.67 | 50.0 | 等级 L1 < L2 |
| 队列分析 | Top20 | L1 | 66.67 | 66.67 | 等级 L1 < L2 |
| comic-layout-engine | 其余 | L1 | 66.67 | 50.0 | 等级 L1 < L2 |
| construction-reconciliation | 其余 | L1 | 66.67 | 50.0 | 等级 L1 < L2 |
| 成本效益分析 | 其余 | L1 | 50.0 | 50.0 | 等级 L1 < L2 |
| creative-origin-engine | 其余 | L1 | 66.67 | 50.0 | 等级 L1 < L2 |
| 客户旅程地图 | 其余 | L1 | 66.67 | 50.0 | 等级 L1 < L2 |
| data-report-builder | 其余 | L1 | 66.67 | 50.0 | 等级 L1 < L2 |
| 前端设计美学 | 其余 | L1 | 66.67 | 50.0 | 等级 L1 < L2 |
| dev-value-gate | 其余 | L1 | 50.0 | 50.0 | 等级 L1 < L2 |
| directory-picker | 其余 | L1 | 66.67 | 50.0 | 等级 L1 < L2 |
| dual-agent-orchestration | 其余 | L1 | 66.67 | 50.0 | 等级 L1 < L2 |
| enterprise-benchmarking | Top20 | L1 | 50.0 | 66.67 | 等级 L1 < L2; 分数 50.0 < 66.67 |
| expert-mode-tool | Top20 | L0 | 33.33 | 66.67 | 等级 L0 < L2; 分数 33.33 < 66.67 |
| finance-operations-suite | 其余 | L0 | 50.0 | 50.0 | 等级 L0 < L2 |
| financial-analysis-pipeline | Top20 | L1 | 66.67 | 66.67 | 等级 L1 < L2 |
| financial-bp-analysis | 其余 | L1 | 50.0 | 50.0 | 等级 L1 < L2 |
| financial-data-access | Top20 | L1 | 66.67 | 66.67 | 等级 L1 < L2 |
| financial-modeling | 其余 | L1 | 66.67 | 50.0 | 等级 L1 < L2 |
| 图片转代码 | 其余 | L0 | 50.0 | 50.0 | 等级 L0 < L2 |
| 图片生成前端 | 其余 | L1 | 66.67 | 50.0 | 等级 L1 < L2 |
| 行业分析助手 | Top20 | L1 | 66.67 | 66.67 | 等级 L1 < L2 |
| 内部控制评估 | Top20 | L1 | 66.67 | 66.67 | 等级 L1 < L2 |
| investment-risk-engine | Top20 | L1 | 66.67 | 66.67 | 等级 L1 < L2 |
| literary-quality-standards | 其余 | L1 | 66.67 | 50.0 | 等级 L1 < L2 |
| liurun-fengtang-advisor | 其余 | L0 | 50.0 | 50.0 | 等级 L0 < L2 |
| liurun-perspective | 其余 | L1 | 50.0 | 50.0 | 等级 L1 < L2 |
| management-advisory | 其余 | L1 | 66.67 | 50.0 | 等级 L1 < L2 |
| market-competitive-intelligence | 其余 | L0 | 50.0 | 50.0 | 等级 L0 < L2 |
| 成熟度模型评估 | Top20 | L0 | 50.0 | 66.67 | 等级 L0 < L2; 分数 50.0 < 66.67 |
| mcp-cli-auto-init | 其余 | L1 | 66.67 | 50.0 | 等级 L1 < L2 |
| media-pipeline-guard | 其余 | L1 | 66.67 | 50.0 | 等级 L1 < L2 |
| methodology-decision | 其余 | L0 | 50.0 | 50.0 | 等级 L0 < L2 |
| novel-serial-writing | 其余 | L1 | 66.67 | 50.0 | 等级 L1 < L2 |
| nuwa-skill | 其余 | L1 | 66.67 | 50.0 | 等级 L1 < L2 |
| obsidian-kb-guard | 其余 | L1 | 62.5 | 50.0 | 等级 L1 < L2 |
| pipeline-governance | 其余 | L0 | 50.0 | 50.0 | 等级 L0 < L2 |
| 优先级排序 | Top20 | L1 | 66.67 | 66.67 | 等级 L1 < L2 |
| 隐私政策起草 | 其余 | L1 | 66.67 | 50.0 | 等级 L1 < L2 |
| product-design-analyzer | Top20 | L1 | 50.0 | 66.67 | 等级 L1 < L2; 分数 50.0 < 66.67 |
| 产品创意构思 | 其余 | L1 | 66.67 | 50.0 | 等级 L1 < L2 |
| Remotion最佳实践 | 其余 | L0 | 66.67 | 50.0 | 等级 L0 < L2 |
| response-craftsmanship | 其余 | L1 | 66.67 | 50.0 | 等级 L1 < L2 |
| security-pentest | 其余 | L1 | 50.0 | 50.0 | 等级 L1 < L2 |
| self-learning-engine | 其余 | L1 | 66.67 | 50.0 | 等级 L1 < L2 |
| self-upgrade | 其余 | L0 | 66.67 | 50.0 | 等级 L0 < L2 |
| 用户情感分析 | 其余 | L1 | 66.67 | 50.0 | 等级 L1 < L2 |
| series-history-writing | 其余 | L1 | 66.67 | 50.0 | 等级 L1 < L2 |
| shiyanwen-financial-advisor | 其余 | L0 | 66.67 | 50.0 | 等级 L0 < L2 |
| 技能生态系统 | 其余 | L1 | 50.0 | 50.0 | 等级 L1 < L2 |
| sp-replacement-eval | 其余 | L0 | 37.5 | 50.0 | 等级 L0 < L2; 分数 37.5 < 50.0 |
| stock-financial-report | 其余 | L1 | 66.67 | 50.0 | 等级 L1 < L2 |
| 用户故事编写 | 其余 | L1 | 66.67 | 50.0 | 等级 L1 < L2 |
| supply-chain-collaboration | 其余 | L0 | 66.67 | 50.0 | 等级 L0 < L2 |
| 税务风险预警 | 其余 | L1 | 66.67 | 50.0 | 等级 L1 < L2 |
| unified-expert-panel | 其余 | L0 | 50.0 | 50.0 | 等级 L0 < L2 |
| unified-inspiration | 其余 | L1 | 66.67 | 50.0 | 等级 L1 < L2 |
| unified-risk-engine | 其余 | L1 | 66.67 | 50.0 | 等级 L1 < L2 |
| unified-storyboard | 其余 | L0 | 50.0 | 50.0 | 等级 L0 < L2 |
| unified-strategy | 其余 | L0 | 50.0 | 50.0 | 等级 L0 < L2 |
| 用户画像 | 其余 | L1 | 66.67 | 50.0 | 等级 L1 < L2 |
| vane-workbench-dev | 其余 | L1 | 66.67 | 50.0 | 等级 L1 < L2 |
| video-production-suite | 其余 | L1 | 66.67 | 50.0 | 等级 L1 < L2 |
| vision-proxy | 其余 | L1 | 66.67 | 50.0 | 等级 L1 < L2 |
| weread-skills | 其余 | L0 | 66.67 | 50.0 | 等级 L0 < L2 |

## 全部 91 项

| 技能 | 档 | 新等级 | 分数 | 通过/适用 | 证据 sha256（前 12） |
|:--|:--|:--|--:|:--|:--|
| A/B测试分析 | prose | L1 | 66.67 | 4/6 | `10c67ff54d0e` |
| agent-research | prose | L2 | 83.33 | 5/6 | `2b3a0ba45364` |
| anti-ai-writing | prose | L1 | 66.67 | 4/6 | `0e8e9ad45d1d` |
| audit-analyst-cross-validation | prose | L1 | 66.67 | 4/6 | `6e0cc1fafb4a` |
| audit-engineer-agent | prose | L2 | 83.33 | 5/6 | `cc619ead9163` |
| cangjie-skill | exec | L1 | 62.5 | 5/8 | `890f3f9ac071` |
| 商业模式画布 | prose | L1 | 66.67 | 4/6 | `b9e985d95ed7` |
| capability-extension | prose | L1 | 66.67 | 4/6 | `b3536c868cf6` |
| cinematic-video-generator | prose | L1 | 66.67 | 4/6 | `ea354a593cec` |
| 认知决策框架 | prose | L2 | 83.33 | 5/6 | `0ce18d98ed0b` |
| 队列分析 | prose | L1 | 66.67 | 4/6 | `58d889d188a0` |
| comic-layout-engine | prose | L1 | 66.67 | 4/6 | `32bc9677df76` |
| construction-reconciliation | prose | L1 | 66.67 | 4/6 | `e86443561503` |
| 合同风险扫描 | prose | L2 | 83.33 | 5/6 | `32d3d40acb38` |
| 成本效益分析 | prose | L1 | 50.0 | 3/6 | `922cc201afec` |
| 课程作业生成器 | prose | L2 | 83.33 | 5/6 | `a19a68046acb` |
| PRD需求文档生成 | prose | L2 | 83.33 | 5/6 | `d5012c79ea7e` |
| creative-origin-engine | prose | L1 | 66.67 | 4/6 | `a26ff5890a23` |
| 客户旅程地图 | prose | L1 | 66.67 | 4/6 | `a2e0bb6516d7` |
| data-report-builder | prose | L1 | 66.67 | 4/6 | `2db9be0cc36d` |
| D2L拆解学习协议 | prose | L2 | 83.33 | 5/6 | `e26c12740e47` |
| 前端设计美学 | prose | L1 | 66.67 | 4/6 | `47decacc14be` |
| dev-value-gate | prose | L1 | 50.0 | 3/6 | `44c9e8499268` |
| directory-picker | prose | L1 | 66.67 | 4/6 | `0b4e793171e8` |
| 保密协议起草 | prose | L2 | 83.33 | 5/6 | `018ec39e8a78` |
| dual-agent-orchestration | prose | L1 | 66.67 | 4/6 | `860736ecac23` |
| enterprise-benchmarking | prose | L1 | 50.0 | 3/6 | `e000cef2b35a` |
| equity-transfer-statement | prose | L2 | 83.33 | 5/6 | `fec066666fd9` |
| expert-mode-tool | prose | L0 | 33.33 | 2/6 | `ab90d7e2d868` |
| finance-operations-suite | prose | L0 | 50.0 | 3/6 | `663ae11cdb4e` |
| financial-analysis-pipeline | prose | L1 | 66.67 | 4/6 | `4ede28c90a12` |
| financial-bp-analysis | prose | L1 | 50.0 | 3/6 | `3f492b5c654a` |
| financial-data-access | prose | L1 | 66.67 | 4/6 | `ed4253c4133b` |
| financial-modeling | prose | L1 | 66.67 | 4/6 | `3c32fec0511b` |
| 财务报表分析 | prose | L2 | 83.33 | 5/6 | `1e64b75971b3` |
| 第一性原理推理引擎 | prose | L2 | 83.33 | 5/6 | `a8feaf30702b` |
| 统一框架编排器 | prose | L2 | 83.33 | 5/6 | `290f6719cacf` |
| governance-guard | prose | L2 | 83.33 | 5/6 | `308bccb5cab6` |
| 图片转代码 | prose | L0 | 50.0 | 3/6 | `9d218590e2b1` |
| 图片生成前端 | prose | L1 | 66.67 | 4/6 | `1e793d0fffba` |
| 行业分析助手 | prose | L1 | 66.67 | 4/6 | `5230ae179e11` |
| 内部控制评估 | prose | L1 | 66.67 | 4/6 | `d244a9ba449a` |
| investment-risk-engine | prose | L1 | 66.67 | 4/6 | `8012314ea1d1` |
| literary-quality-standards | prose | L1 | 66.67 | 4/6 | `1ac3ede34ca9` |
| liurun-fengtang-advisor | prose | L0 | 50.0 | 3/6 | `99940f0a4d21` |
| liurun-perspective | prose | L1 | 50.0 | 3/6 | `f131f0e56bd4` |
| management-advisory | prose | L1 | 66.67 | 4/6 | `c12adab28d2b` |
| market-competitive-intelligence | prose | L0 | 50.0 | 3/6 | `61597700a76f` |
| 成熟度模型评估 | prose | L0 | 50.0 | 3/6 | `6bbb40ac5bee` |
| mcp-cli-auto-init | prose | L1 | 66.67 | 4/6 | `f0a24dc386c5` |
| media-pipeline-guard | prose | L1 | 66.67 | 4/6 | `6cbc9681ae3e` |
| methodology-decision | prose | L0 | 50.0 | 3/6 | `6b945d744aa8` |
| 错误→方法复盘 | prose | L2 | 83.33 | 5/6 | `99368e17dafb` |
| novel-serial-writing | prose | L1 | 66.67 | 4/6 | `e1241e08ab22` |
| nuwa-skill | prose | L1 | 66.67 | 4/6 | `bd8a1173c0f7` |
| obsidian-kb-guard | exec | L1 | 62.5 | 5/8 | `e9fe09c48e4e` |
| picture-book-creator | prose | L2 | 83.33 | 5/6 | `6e1eecbd5a3c` |
| pipeline-governance | prose | L0 | 50.0 | 3/6 | `0a4adc4e5094` |
| 优先级排序 | prose | L1 | 66.67 | 4/6 | `2e2f972ab3cb` |
| 隐私政策起草 | prose | L1 | 66.67 | 4/6 | `3d77ebcc770b` |
| product-design-analyzer | prose | L1 | 50.0 | 3/6 | `bd0ff7589054` |
| 产品创意构思 | prose | L1 | 66.67 | 4/6 | `2a1066b8b32c` |
| public-account-writing | prose | L2 | 83.33 | 5/6 | `178e61991864` |
| Remotion最佳实践 | prose | L0 | 66.67 | 4/6 | `3a7203721517` |
| response-craftsmanship | prose | L1 | 66.67 | 4/6 | `68ba17aef130` |
| 简历审查优化 | prose | L2 | 83.33 | 5/6 | `0e9475f16369` |
| 根因分析 | prose | L2 | 83.33 | 5/6 | `5946afa3dcca` |
| security-pentest | prose | L1 | 50.0 | 3/6 | `97acffab534c` |
| self-learning-engine | prose | L1 | 66.67 | 4/6 | `b3536c868cf6` |
| self-upgrade | prose | L0 | 66.67 | 4/6 | `1afedbe0b4a6` |
| 用户情感分析 | prose | L1 | 66.67 | 4/6 | `02a7e159c959` |
| series-history-writing | prose | L1 | 66.67 | 4/6 | `6a4f427ed94e` |
| shiyanwen-financial-advisor | prose | L0 | 66.67 | 4/6 | `5f65f0633a94` |
| 技能生态系统 | exec | L1 | 50.0 | 4/8 | `43750daac860` |
| sp-replacement-eval | exec | L0 | 37.5 | 3/8 | `2fd13df5aab0` |
| stock-financial-report | prose | L1 | 66.67 | 4/6 | `3093f99a8fbe` |
| 用户故事编写 | prose | L1 | 66.67 | 4/6 | `036790dc9367` |
| supply-chain-collaboration | prose | L0 | 66.67 | 4/6 | `4f7d4e16e027` |
| 税务风险预警 | prose | L1 | 66.67 | 4/6 | `7819dde1fbd6` |
| 代码库理解 | prose | L2 | 83.33 | 5/6 | `d754f52c85b8` |
| unified-expert-panel | prose | L0 | 50.0 | 3/6 | `5a6698900e5e` |
| unified-inspiration | prose | L1 | 66.67 | 4/6 | `248b29fd8b0a` |
| unified-risk-engine | prose | L1 | 66.67 | 4/6 | `1f3f3bb10493` |
| unified-storyboard | prose | L0 | 50.0 | 3/6 | `e6528c94b0e7` |
| unified-strategy | prose | L0 | 50.0 | 3/6 | `b2dc594deb55` |
| 用户画像 | prose | L1 | 66.67 | 4/6 | `ab219cb95a12` |
| vane-workbench-dev | prose | L1 | 66.67 | 4/6 | `bf5b40da5d87` |
| video-production-suite | prose | L1 | 66.67 | 4/6 | `8348ffff783b` |
| video-understanding | prose | L2 | 83.33 | 5/6 | `3a4b976f4873` |
| vision-proxy | prose | L1 | 66.67 | 4/6 | `6e1dea3a0eae` |
| weread-skills | prose | L0 | 66.67 | 4/6 | `ae1e524faab2` |

## 对外表述替换表

| 旧表述 | 问题 | 替换为 |
|:--|:--|:--|
| 「UZI 金牌技能 86/88」 | 金牌来自模板注入与正则打分，不测任务正确性 | 「UZI v2 评级：L1–L3 由工具签发，逐项附命令/退出码/sha256」 |
| 「金牌认证」 | 认证暗示第三方授权，实际无外部审核 | 「工具签发评级（L2 可交付）」 |
| 「最优 / 第一 / 权威」 | 无同口径横向比较 | 「在 38 个外部参照技能中位于 P50/P75 分位」 |
| 「技能很强」 | 无证据 | 「M1–M8 机械项 x/y 通过，M6 期望输出比对一致」 |
| 「达到优质水准」 | 未定义 | 「≥ 参照语料 P75 且 ≥ L2，未达标项公开列出」 |
