# uzi-grade

把「这个技能很强」变成**第三方能复跑**的事。

`uzi-grade` 用 8 条机械判据（M1–M8）+ 3 条行为判据（B1–B3）给技能目录评级，
每条结论都写成一条可复算的证据：

```json
{"check_id": "M4", "status": "fail", "command": "uzi check M4 ./my-skill",
 "exit_code": 1, "output_sha256": "9f2c…"}
```

等级 L1–L3 只能由工具签发；L4/L5 只能由人工录入带 URL 与采集日期的外部证据。
徽章由工具计算后签发，文本固定为 `UZI-L2 · 12/12 · sha256:xxxxxxx · 日期`，
并嵌入可复算的二维码。

---

## 旧体系的「金牌」已作废

上一代 `uzi-inject.py`（保留在 [`legacy/`](legacy/LEGACY-README.md)）把 Markdown
模板注入技能正文，再用 D1–D10 做「某字符串/文件是否存在」的正则检查，输出
「金牌」。它不执行脚本、不运行任务、不比较期望输出，也不检查注入的护栏是否
与技能领域相关。

因此：**旧「金牌」是内部文档分级标签，不是工具实力证明。** 该标签在新体系中
作废，`uzi grade` 的任何计算都不读取它。

---

## 安装

需要 Python ≥ 3.10，零运行时依赖。

```bash
git clone https://github.com/Vane1981-2011/uzi-grade
cd uzi-grade
python -m pip install -e .
uzi --version
```

开发依赖（仅测试）：`python -m pip install -e ".[dev]"`。

## 命令

```bash
uzi grade <skill-dir> [--json]           # 单技能评级
uzi grade --all <root> [--out DIR]       # 全库评级，写 report.json / report.md
uzi verify <report.json> [--root DIR]    # 复算证据链，逐项比对 sha256
uzi badge <skill-dir> --out badge.svg    # 仅当评级由工具算出时签发
uzi selftest                             # 判别力自证（注入 10 类缺陷）
uzi calibrate --ref <dir> [...] --out calibration.json
uzi check M4 ./my-skill                  # 重跑单条判据（报告里的 command 就是它）
uzi behaviour B1 ./my-skill              # B1–B3 存根：输出 rc=2 与缺失证据
```

### 退出码只有三种

| rc | 含义 |
|--:|:--|
| `0` | 全绿 |
| `1` | 判了，有 findings（fail 或 unverifiable） |
| `2` | **判不了**：空集、路径不存在、扫描被截断、判据自身缺陷 |

`--max N` 截断扫描时，报告里的 `truncation.omitted` 会列出**被截掉了什么**，
退出码为 `2`，不会伪装成完整通过。

---

## 判据

每条判据输出 `{check_id, status, command, exit_code, output_sha256}`。
`status ∈ {pass, fail, unverifiable, skip}`；`unverifiable` 必须带 `missing`
（写明缺什么证据），不允许留空。

| 项 | 测什么 | 类型 |
|:--|:--|:--|
| **M1 可发现性** | `name == 目录名`；description 说明「做什么 + 何时用」；可提取 ≥2 个触发词 | 机械 |
| **M2 结构完整性** | 六段结构（定位/何时用/步骤/输出/失败模式/验收）齐备；**去模板化**：与通用骨架的 shingle 相似度 < 0.30 | 机械 |
| **M3 指令可操作性** | 步骤可解析为「动作 + 输入/验收判据」三元组，≥3 步可执行且比例 ≥0.6 | 机械 |
| **M4 资源完整性** | `references/` `assets/` 等被引用的文件断链数 = 0 | 机械 |
| **M5 可执行性** | 含 `scripts/*.py` 时，在沙箱副本中冒烟运行 rc=0 且 < 10s | 机械（exec 档） |
| **M6 可复现性** | 有 `tests/expected.json` 时跑通并逐条比对 stdout 的 sha256 | 机械（exec 档） |
| **M7 安全护栏** | HARD-GATE 段存在，且 5 类越界语料（破坏性写/凭据外泄/未审批上生产/绕过审批/编造证据）各自有**单条**拒绝规则 | 机械（静态） |
| **M8 证据可核验** | 外部数字/事实带 URL 或文件锚点；只有命名来源记 `unverifiable`，完全无来源记 `fail` | 机械 |
| **B1 任务基准** | 3 条 golden task 端到端执行并判分 | 行为（本版未执行） |
| **B2 负例拒答** | 3 条越界请求实际拒答或降级 | 行为（本版未执行） |
| **B3 稳定性** | 同任务 3 次采样，通过率 ≥ 2/3 | 行为（本版未执行） |

**M7 是静态覆盖检查**：它检查护栏文本是否写明了拒绝规则，**不是**真实模型
拒答。真实拒答属于 B2，本版没有模型执行环境，因此所有 B1–B3 记录都是
`unverifiable`，并写明缺的是「golden task 执行环境 / 模型调用记录 / 判分结果」
或「3 次重复采样的通过率记录」。

### exec / prose 分档

| 档 | 判定 | 跑哪些 | 分母 |
|:--|:--|:--|:--|
| `exec` | 含 `scripts/*.py` | M1–M8 | 8 |
| `prose` | 纯 references / 无脚本 | M1–M4, M7, M8 | 6（M5/M6 记 `skip` 并剔除） |

分档是为了避免「没有脚本的散文技能」和「有脚本的工具技能」被同一分母拉歪。
代价是 prose 档缺可执行证据，结构上最高只能到 **L2**。

---

## 等级

| 等级 | 名称 | 签发条件 |
|:--|:--|:--|
| `L0` | 未达最低结构门槛 | M1 或 M2 未通过 |
| `L1` | 存在 | M1 + M2 |
| `L2` | 可交付 | + M3 / M4 / M8（exec 档再加 M5） |
| `L3` | 可复现 | + M6 通过（期望输出比对一致）且 M7 通过 |
| `L4` | 被采用 | **只能人工录入**外部证据 |
| `L5` | 独立验证 | **只能人工录入**第三方复核证据 |

L1–L3 全部由 `uzi grade` 计算，不接受手工填写。L4/L5 即使判据全绿也不会自动授予；
必须在技能目录放 `.uzi/attestation.json`：

```json
{
  "level": "L4",
  "url": "https://example.com/case-study/2026-09",
  "collected_at": "2026-11-07",
  "note": "被采用的具体证据：谁在什么场景用了它、产出在哪里"
}
```

`url` 必须是 `http(s)`，`collected_at` 必须是 `YYYY-MM-DD`，否则申报无效并写入
`reasons`（等级不会提升）。

---

## 徽章

```bash
uzi badge examples/good-exec --out badge.svg --report uzi-report/report.json
```

- 文本固定：`UZI-L3 · 8/8 · sha256:1b2c3d4 · 2026-11-07`
- 二维码载荷：`sha256:<完整 digest>`，可据此复算
- `--report` 会给签发的 digest 加一道锁：报告里的 digest 与当前目录复算不一致时**拒签**
- 评级为 `L0` 时**拒签**（rc=2）
- 徽章与报告中禁用字样：`金牌`、`认证`、`最优`、`第一`、`权威`

---

## 可复算性

`report.json` 里有两层哈希：

- **`report_sha256`（seal）**：对报告**记录内容**的哈希，覆盖 `schema`、
  `tool_version`、`scanned`、`truncation`、`summary`、`flagships` 与每个技能的
  `{checks, behaviour, attestation, digest, level, score, reasons}`。
  手工改 level、改 summary、删一条 check、改一行 reason，seal 立刻不匹配。
- **复算哈希**：`uzi verify` 按 `report.root` 重新评级，再算一次同样的哈希并与记录值
  比对。两层都过才算复算成功。

为了跨机器可复算：

- 哈希**不包含** `generated_at`、绝对 `root`、`root_display`；
- 每条 check 的 `command` 是相对语料根的可重跑命令（`uzi check M4 ./my-skill`），
  不含私有绝对路径；
- 语料被移动到别处时用 `uzi verify report.json --root <new-root>`，证据全部重算。

`uzi verify` 对同一份报告跑两次，`verify_sha256` 必须完全一致（CI 里就是这么断言
的）。

---

## 判别力自证

```bash
uzi selftest
```

构造一个全绿基线技能，然后**一次只注入一类缺陷**，检查对应判据是否变红：

| 缺陷 | 期望变红的判据 |
|:--|:--|
| 删 description | M1 |
| description 空泛化 | M1 |
| 删「何时不用」 | M2 |
| 步骤散文化 | M3 |
| 引用不存在文件 | M4 |
| 脚本强制 `exit 1` | M5 |
| 断言改 `assert True`（输出被改） | M6 |
| 删 HARD-GATE | M7 |
| 数字去来源 | M8 |
| 整段替换为通用骨架 | M2 |

门槛：

- kill-rate **≥ 9/10**（实测 10/10）
- 未变异基线 **0 红**；否则判据自身判红，`verdict=judge-defect`，退出码 `2`
- 误报率 ≤ 10%（实测 0%）

一个从没被证明会失败的检查器只是橡皮图章，所以这一步不做完，后面的分数都不算数。

---

## 外部刻度 `calibration.json`

用同一套判据扫描 **38 个非本项目作者编写**的技能目录：

- `~/.claude/plugins/marketplaces/claude-plugins-official`（33）
- `~/.codex/skills/.system`（5）

```bash
uzi calibrate \
  --ref ~/.claude/plugins/marketplaces/claude-plugins-official \
  --ref ~/.codex/skills/.system \
  --out calibration.json
```

当前刻度（`percentile` = R type 7 线性插值）：

| 档 | n | min | P25 | P50 | P75 | max |
|:--|--:|--:|--:|--:|--:|--:|
| exec | 5 | 12.5 | 37.5 | 50.0 | 50.0 | 62.5 |
| prose | 33 | 33.33 | 50.0 | 50.0 | 66.67 | 66.67 |

**必须同时读的限制**：

- 38 个参照**全部落在 L0**，主要因为 M2（六段结构 + 去模板化）与 M7（HARD-GATE +
  5 类越界规则）是**本工具的交付契约**，第三方技能通常没按此契约写。
  这是**契约差异**，不是「外部技能质量差」。
- 所以这些分位只适合做**同口径阈值**，不是行业排名，也不是对外部作品的评价。
- 判据、阈值、分位口径都不为了凑结果而下调。

阈值用法：Top 20 旗舰技能需 ≥ 同档 P75 且 ≥ L2；其余需 ≥ 同档 P50 且 ≥ L2。
达不到就写「未达标」，并进入公开清单。

---

## 自有 91 项技能：重评结果（如实）

对象为 91 个自有技能（排除 `_base`/`_standby`/vendored）。语料正文**不在本仓库**，
公开的只有「名称 + 等级 + 证据摘要」，见 [`regrade.json`](regrade.json) 与
[`regrade.md`](regrade.md)。

| 等级 | 数量 |
|:--|--:|
| L0 | 17 |
| L1 | 54 |
| L2 | 20 |
| L3 | 0 |
| L4 / L5 | 0 |

- 91/91 有等级，0 项留空。
- 达标线：Top 20 **7/20** 达标；其余 **13/71** 达标。
- 未达标清单在 `regrade.md` 里逐项列出（不修饰），对照表给出「旧表述 → 新表述」。
- B1–B3 未执行，Top 20 的 60 条记录全部是 `unverifiable` + 缺失说明。

**这些降级本身就是工具可信的证据**：散文技能天然过不了 M5/M6，旧「金牌」也没有
测过任务正确性。为了好看而放宽判据，等于把橡皮图章换个壳。

---

## 数据边界与脱敏

- 仓库内只放：工具、4 个**合成**示例技能（`examples/`）、38 个参照的分数、
  自有 91 项的名称/等级/证据摘要。
- 自有技能正文不外泄；`regrade.json` 的路径写成 `<skill-corpus-N>/<slug>`。
- 报告与校准文件不含绝对私有路径（CI 会 grep）。

## 已知限制

1. M1–M8 是**静态**判据：它们证明「写得可执行、可复现、可核验」，**不证明任务做对**。
2. B1–B3 行为评测本版未执行；任何「任务正确率」的说法都缺证据。
3. M7 是静态护栏覆盖，不等于真实拒答。
4. L4/L5 目前没有任何 attestation，因此全部为 0。
5. 外部刻度样本小（exec n=5），P75 的置信度有限；换语料后分位会变，必须重跑。
6. 本仓库只做技能评级，不处理简历 PDF、作品展示页面或移动端链接问题。

## 验收记录

每条完成判据的命令、退出码、sha256 与「已证实 / 待验证」分档见
[`docs/acceptance.md`](docs/acceptance.md)。

## 开发

```bash
python -m pip install -e ".[dev]"
python -m pytest -q        # 39 项
uzi selftest               # kill 10/10, base_red []
uzi grade --all examples   # rc=1（示例里故意有 2 个坏技能）
```

CI（GitHub Actions）在 Python 3.10 / 3.12 上跑同样的命令，并额外断言：
截断扫描 rc=2、`uzi verify` 两次 `verify_sha256` 相同。

## 许可

MIT，见 [LICENSE](LICENSE)。
