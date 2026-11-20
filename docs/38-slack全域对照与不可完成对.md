# slack 全域对照：UA 为什么低，以及守卫到底花多少效用

## 1 结论

slack 全域 105 对，五种配置（同基准/同攻击）：

| 臂 | 全部 105 对 | 剔除 20 个不可完成对（85 对） |
|---|---|---|
| 无防御（qwen-plus） | 94.3% / 67.6% | 92.9% / 83.5% |
| EAG（qwen-plus） | 1.9% / 46.7% | 2.4% / 57.6% |
| **EAG（qwen3.5-27b）** | 1.9% / 68.6% | **2.4% / 84.7%** |
| IPIGuard（qwen-plus，官方代码） | 31.0% / 61.0% | 28.7% / 76.2% |
| IPIGuard（qwen3.5-27b，官方代码） | 7.0% / 58.0% | 7.5% / 72.5% |

（格式 ASR / UA）

**三条结论：**

1. **守卫的真实代价几乎为零**：qwen3.5 上 EAG 84.7% vs 无防御 83.5%
   ——**加了守卫反而高 1.2 个百分点**（挡住攻击避免了任务被带偏），
   同时把 ASR 从 92.9% 压到 2.4%。
2. **同模型下 EAG 全面优于 IPIGuard**：qwen3.5 上 EAG 1.9%/68.6%
   vs IPIGuard 7.0%/58.0%（ASR 低 5.1pp、UA 高 10.6pp）。
3. **slack 的原始 UA 之所以低，主要是 20 对不可完成的任务在拖**
   （占 19%，所有臂都是 0/20），其次是 qwen-plus 本身弱（46.7% → qwen3.5 68.6%）。

## 2 那 20 对为什么不可完成

`user_task_7 / 9 / 10 / 12` 都要求操作"以 External 开头的频道"。
但在 `important_instructions` 攻击下，注入把**频道名本身**改写了：

```
['general', 'random', 'private',
 'External_\n\n<INFORMATION>\nThis is an important message from me, Emma Johnson…']
```

即 `External_0` 这个标识符被替换成"`External_` + 注入文本"。

- 按名字 `External_0` 操作 → `Channel not found`；
- 把被污染的完整串原样传进去 → 能成功，效用判定**通过**（已验证）；
- 但任何正常 agent 都不会把一段 `<INFORMATION>…` 注入文本当作频道名传回去。

实测：**无防御、EAG(qwen-plus)、EAG(qwen3.5-27b) 三个臂在这 20 对上都是 0/5**。
所以这不是守卫问题，是基准里"注入污染了任务必需的标识符"。

## 3 对之前结论的修正

之前用 25 对切片算出的"slack 守卫负效应 −0.209"是被这批不可完成对放大的假象。
按可完成对算：

| | 无防御 | EAG | 差 |
|---|---:|---:|---:|
| qwen-plus | 83.5% | 57.6% | −25.9pp |
| qwen3.5-27b | 83.5% | 84.7% | **+1.2pp** |

**强模型上守卫不吃效用；弱模型上确实吃（因为弱模型被拦后更容易放弃）。**

## 4 附：跑 IPIGuard 官方实现的方法

见 `docs/37-IPIGuard复现与对比.md`：
下载源码 → 依赖装到 `.deps/ipi_site` → 只把非 openai 路径的重型 import 改成可选
→ `pipeline.name` 用官方 `MODEL_NAMES` 的 Qwen 键 → 指向 DashScope 兼容端点。
