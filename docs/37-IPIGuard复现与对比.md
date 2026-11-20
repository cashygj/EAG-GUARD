# 复现 IPIGuard 并做同模型同切片对比

## 1 结论先行

同一 25 对 slack 切片、Important Instructions 攻击，两个模型 × 三种方法：

| 方法 | qwen-plus-2025-04-28 | qwen3.5-27b |
|---|---|---|
| 无防御 | 96% / 92% | 88% / 96% |
| **IPIGuard（官方实现）** | **32% / 84%** | **4% / 80%** |
| **EAG-Guard（我们）** | **4% / 76%** | **4% / 96%** |
| —— 报告声称（qwen-plus）—— | | |
| IPIGuard | 20% / 80% | — |
| EAG-Guard | 4% / 92% | — |

（格内为 ASR / UA）

三条结论：

1. **EAG 的 ASR 与报告的 4% 精确一致**；IPIGuard 我们跑出 32%（报告 20%），
   仍是同一量级（25 对粒度 4pp/对，差 3 对）。
2. **换到 qwen3.5-27b，两者 ASR 都是 4%**，但 EAG 的 UA 高出 16 个百分点
   （96% vs 80%）。
3. **IPIGuard 的防护依赖模型**：qwen-plus 上 32%，qwen3.5-27b 上 4%——
   它的"假装成功"机制需要模型愿意按计划走；EAG 在两个模型上都是 4%。

## 2 怎么跑起来的（官方代码，未改逻辑）

- 源码：[Greysahy/ipiguard](https://github.com/Greysahy/ipiguard)（EMNLP 2025 Oral），
  自带 vendored agentdojo 0.1.23；
- git clone 在本机因 schannel 凭证失败，改用 HTTPS 下载源码包；
- 依赖装在独立目录 `.deps/ipi_site`（networkx 等），不污染主环境；
- 他们的 `agent_pipeline.py` 在模块级 import 了 anthropic/cohere/vertexai/transformers，
  这些分支在 openai 路径上不会被调用——**只把 import 改成可选**，
  IPIGuard 的算法、提示词、执行逻辑一行未动；
- `pipeline.name` 需含官方 `MODEL_NAMES` 的键（Qwen 的键是 `Qwen/Qwen2.5-32B-Instruct`），
  这只是让注入模板用"Qwen created by Alibaba Cloud."称呼模型；
- `OPENAI_API_KEY` / `OPENAI_BASE_URL` 指向 DashScope 兼容端点，模型填 `qwen-plus-2025-04-28`。

跑批命令：
```powershell
.\.venv\Scripts\python.exe tools\run_ipiguard_official.py `
  --suite slack --users 0-4 --injections 1-5 `
  --model qwen-plus-2025-04-28 --out results\runs\ipi_official_slack25
```

## 3 他们的机制（读源码得到，与文档描述一致）

1. **规划期**：先一次"任务理解"调用提取要点；再一次调用生成 TDG（严格 JSON，
   未知参数写成 `<unknown>: type`）；构成有向无环图。
2. **执行期**：按拓扑序逐节点执行；执行前用一次 LLM 调用，依据前序工具返回
   更新 `<unknown>` 参数。
3. **节点扩展**：每次工具返回后，允许模型提出新的工具调用：
   - 命中只读白名单（`tool_white_list.whitelist`）→ **立即执行**；
   - 否则（写操作）→ **不执行**，只往对话里塞一条伪造回执
     "New tool call success! ... 你的新任务已完成"。

第 3 点是它防注入的核心：**注入要求的写操作被"假装成功"而不是真的执行**。

## 4 与报告的差异

| 项 | 报告 | 我们实测 | 说明 |
|---|---|---|---|
| IPIGuard ASR | 20%（5/25） | 32%（8/25） | 25 对粒度是 4pp/对，差 3 对 |
| IPIGuard UA | 80% | 84% | 接近 |
| EAG ASR | 4% | **4%** | 完全一致 |
| EAG UA | 92% | 76% | 我们的答复完整性仍是短板 |

**报告里"IPIGuard 20%"这个数，用他们的官方代码 + 报告所述模型复现不出来（我们得到 32%）。**
但方向性结论成立：**IPIGuard 的残余 ASR 在 20~30% 量级，EAG 是 4%。**

## 5 一个值得注意的点

无防御的 UA（92%）反而**高于** IPIGuard（84%）——说明 IPIGuard 的规划-执行分离
牺牲了 8 个百分点的效用。EAG 的代价更大（76%），这是下一步要补的地方
（答复完整性问题，已在 workspace/travel 上做过一轮）。
