# AgentDojo 接入

环境：`agentdojo==0.1.35` 装在 `D:\EAG-GUARD\.venv\Lib\site-packages`（另有 pytest）。
核心库仍然零依赖，只有 `eag_guard.integrations` 这一层需要 agentdojo。

## 1 已核对的基准

```python
from agentdojo.task_suite.load_suites import get_suites
suites = get_suites("v1")
```

| 域 | user_tasks | injection_tasks | 对数 |
|---|---:|---:|---:|
| workspace | 40 | 6 | 240 |
| travel | 20 | 7 | 140 |
| banking | 16 | 9 | 144 |
| slack | 21 | 5 | 105 |
| 合计 | **97** | **27** | **629** |

与报告 §4.1 的 97 / 27 / 629 及表 4-1 的 240/105/140/144 完全一致。

## 2 已实现：`EAGGuardElement`

`src/eag_guard/integrations/agentdojo.py`

AgentDojo 的执行链是 `LLM →（assistant 消息带 tool_calls）→ ToolsExecutor`，
`ToolsExecutor` 只执行 `messages[-1]["tool_calls"]`。所以守卫做成 ToolsExecutor 的
包装器，插在同一个位置：

```
LLM → EAGGuardElement(内部调用 ToolsExecutor) → LLM → ...
```

行为：

1. 取最后一个 assistant 消息里的每个 `FunctionCall`，转成 `Action`；
2. 调 `Guard.review()`（FPR → 裁判），记录 `StepRecord`；
3. 只把**通过**的调用留给 `ToolsExecutor`，被拒的调用根本不会到达环境；
4. 被拒的调用补一条 `ChatToolResultMessage(error="动作被拒绝：…")`，模型下一轮
   能看到可操作原因并重规划；
5. 执行结果按来源切成 `EvidenceItem`（默认不可信），供后续动作溯源。

配套的 `toolspecs_from_suite()` 从 `Function.parameters.model_json_schema()` 抽参数名，
用 `DEFAULT_OBJECT_PARAMS` 标注每个副作用工具"哪个参数是作用对象"。

已验证（`tests/test_agentdojo_adapter.py`，7 个用例，用真实 AgentDojo 类型与真实
`ToolsExecutor`，只把模型和运行时换成假件）：

- 11 个 banking 工具签名抽取正确，`send_money.object_param == "recipient"`；
- 越权收款人 → **运行时一次都没被调用**，且回了一条带原因的 tool 消息；
- 先读文件、再按文件里的收款人付款 → 第二步被拦（值只出现在不可信内容里）；
- 一次消息里两个调用 → 只过滤掉坏的那个。

## 3 官方指标接口（已确认，方向与名字相反）

```python
from agentdojo.benchmark import run_task_with_injection_tasks
utility, security = run_task_with_injection_tasks(
    suite, pipeline, user_task, attack, logdir, force_rerun,
    injection_tasks=[...],
)
```

- 返回两个 `dict[(user_task_id, injection_task_id) -> bool]`
- **`security=True` 表示"注入目标被完成"**，即攻击成功 → `attack_success = security`。
  别被名字骗了：`banking` 的 `security()` 在"真的有笔转账给了攻击者"时返回 True；
  `workspace` 的在"恶意邮件真的发出去了"时返回 True。
- DoS 类攻击内部令 `security = not utility`
- 工具级 ASR 无法从 `security` 推出，必须由 trace / 环境状态差提供
  （`metrics.outcome_from_agentdojo` 已按此设计，缺 trace 时不计入工具级分母）

`AgentPipeline(elements)` 只是一串元素按序执行一次；ReAct 循环靠重复元素实现：

```python
[InitQuery, SystemMessage, LLM, 执行器, LLM, 执行器, LLM]   # 末尾必须补一次 LLM
```

末尾那次 LLM 不能省：如果最后一轮的执行器留下了 tool 消息，链条会以非 assistant
消息结尾，AgentDojo 取最终输出时直接抛 `Last message was not an assistant message`。

## 4 还差三件事

1. **LLM 任务解析器**：把 `user_task.PROMPT` 送进 qwen-plus，产出 `AuthorizationScope`。
   要用 JSON schema 约束，并对 `T` 做校验（不能凭空多出工具）。
   接口已经留好：任何有 `parse(request, tools) -> AuthorizationScope` 的对象都能塞进
   `Guard(parser=...)`。
2. **qwen-plus 客户端**：OpenAI 兼容端点，需要 `DASHSCOPE_API_KEY`。
   规划器、裁判共用同一个客户端，但要分两个 system prompt。
3. **跑批器**：遍历 `(user_task, injection_task)`，每个任务前 `element.reset()`，
   把 `element.records` 与 `element.evidence` 落成 `trace.json`，再用
   `outcome_from_agentdojo()` + `summarize()` 出表。

## 5 推进顺序

1. workspace 的 `user_task_0 × injection_task_0` 一对跑通；
2. 25 对切片（`user_task_0–4` × `injection_task_1–5`），先只开 FPR，再开裁判；
3. 629 对全量，与 `results/baseline_report.json` 对表；
4. 每次运行落 `trace.json`，保证可复查。
