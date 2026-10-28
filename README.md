# EAG-Guard（重建版）

> 原实验代码与数据已全部丢失，本仓库依据《EAG-Guard阶段性研究报告》（2026-10）从零重建。
> 报告里的形式化定义、执行流程与全部实验数字，是这里唯一的规格来源。

**一句话**：把用户请求解析成授权范围 `A=(T,O,P)`，用证据—授权—动作图（EAG）追溯每个参数值的来源 `s(v)`，在执行前由独立语义裁判核对动作是否越权——外部内容可以改变计划，但不能改变授权。

## 现状

> 完整交代见 [复现报告](docs/11-复现报告.md)：做了什么、哪些对得上、哪些对不上、为什么。

| 模块 | 状态 | 说明 |
|---|---|---|
| 授权范围 `A=(T,O,P)` | ✅ 可运行 | 规则解析器；真实实验应替换为 LLM 解析器 |
| EAG 图 + 字段级溯源 `FPR` | ✅ 可运行 | 沿 `supports/derives` 回溯到授权/委托根 |
| 委托边（字段型 / 内容型） | ✅ 可运行 | 字段型只认证据的结构化字段，防止"正文里写个数"冒充委托 |
| 独立语义裁判 | ✅ 可运行 | `RuleJudge`（确定性）+ `LLMJudge`（JSON 契约，解析失败即拒绝） |
| 执行前二次核对 / 输出审核 | ✅ 可运行 | 签名比对；逐字复述外部内容会被裁掉 |
| 评测口径 ASR/UA | ✅ 可运行 | 按对 / 等权 / 工具级，已用报告表 4-1 自洽性校验 |
| 离线 mock 基准 | ✅ 可运行 | 5 个用例覆盖四域四类攻击形态 |
| AgentDojo 适配层 | ✅ 可运行 | `EAGGuardElement` 插在 ToolsExecutor 位置；基准已核对 97/27/629 |
| qwen-plus 真实推理 | ✅ 已接通 | 单对与 25 对切片跑通，见 [首轮真实运行](docs/04-首轮真实运行.md) |
| 25 对切片 | ✅ 已跑 | workspace：28%/0.28 → **0%/0.52**；slack：60%/0.40 → **0%/0.32**（干净上限 0.80） |
| 全量 629 对复跑 | ⬜ 进行中 | 先补委托表示，再上四域 |

mock 上的结果（**不能**与报告数字直接比较，只是链路自检）：

```
=== undefended ===   ASR 100%  UA 1.0000     === eag ===   ASR 0%  UA 1.0000
```

## 快速开始

```powershell
$py = "D:\EAG-GUARD\.venv\Scripts\python.exe"   # 或任意 Python 3.12
$env:PYTHONPATH = "D:\EAG-GUARD\src"

& $py scripts\run_mock.py                        # 跑离线 mock，打印两张结果表
& $py -m pytest -q                               # 跑单元测试
```

不需要安装任何第三方包即可跑通核心链路（stdlib only）。

## 目录

```
src/eag_guard/
  types.py        A、s(v)、Action/Evidence/ToolSpec 等核心类型
  scope.py        授权范围推导（T/O/P）、委托规则
  provenance.py   参数值归因：user-specified / user-delegated / injected
  eag.py          证据—授权—动作图、FPR 回溯
  judge.py        独立语义裁判（规则版 + LLM 版）
  audit.py        输出审核
  pipeline.py     Guard：解析 → 审核循环 → 输出审核
  eval/metrics.py ASR / UA / 工具级 / 等权
  bench/mock.py   离线四域用例
  bench/runner.py 跑批与结果表
tests/            单元测试（含报告表 4-1 的口径校验）
docs/             基线冻结、架构、评测口径
```

## 重建路线

1. **骨架 + 离线闭环**（已完成）：核心判定、委托、裁判、审核、指标，mock 上端到端。
2. **接入 AgentDojo**（下一步）：四域 629 对、`important_instructions`、官方 utility 判定。
3. **接 qwen-plus**：任务解析器、规划器、裁判换成真实模型调用，先跑 25 对切片。
4. **对齐报告**：25 对切片上复现 EAG 4% ASR / 0.92 UA、IPIGuard 20% / 0.80 的量级，再上 629 对。

验收标准：**流程跑通、指标口径一致、数值与报告可比**。

## 断点续跑（长跑必备）

全部实验用一个脚本管理，**随时 Ctrl+C，下次接着跑，已完成的对不会重跑**：

```powershell
.\run_all.cmd -Status          # 只看进度，不跑任何东西
.\run_all.cmd                 # 全部：四域 × 两臂 ×（切片 + 全域）
.\run_all.cmd -Scope slice    # 只跑 25 对切片
.\run_all.cmd -Domains slack  # 只跑一个域
.\run_all.cmd -Arms eag       # 只跑守卫臂
```

- 每个 run 写到固定的 `results\runs\<域>_<范围>_<臂>\`
- 逐对落盘 + `--resume`：已完成的跳过；写坏或带 error 的自动重跑
- 中断最多损失"正在跑的那一对"
- 日志：`logs\run-all-<时间戳>.log`
- 进度也可以随时用 `-Status` 查，不必等跑完

> PowerShell 默认禁止运行 .ps1，所以入口是 `run_all.cmd`（内部用
> `-ExecutionPolicy Bypass` 调 `run_all.ps1`）。直接跑 .ps1 会报安全错误。