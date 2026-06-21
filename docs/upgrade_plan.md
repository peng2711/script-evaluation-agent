# 剧本评估 Multi-Agent 系统：工程化升级方案设计 (V2)

本方案旨在将现有的剧本评估 Multi-Agent 系统（V1）从一个演示型 Demo 升级为**可生产落地、具备高可控度、高可解释性及持续优化闭环的 Agent 能力工程化项目**。

---

## 1. 核心升级目标

在不影响现有业务功能和逻辑的前提下，围绕以下六个方向进行架构升级与工程化重构：
1. **工具调用标准化**：引入 Tool Registry（工具注册表）与 Tool Router（工具路由器），统一代理（Agent）与外部基础设施（存储、检索）的交互协议。
2. **多维链路追踪（Trace + Metrics）**：升级 Trace 机制，记录 Agent 节点、工具调用的开始时间、结束时间、耗时（Duration）、重试计数和成功标志。
3. **两阶段检索升级**：将现有的单阶段对标检索重构为“Recall (召回) + Rerank (重排)”双阶段管道。
4. **反思式打回机制（Reflection Loop）**：将基于标志位的重试策略升级为真正的“ Critique-driven Reflection（基于质检反馈意见的定点反思修正）”机制。
5. **系统级评测增强**：扩展 Eval 评测脚本，不仅对比质量指标，同时比对工程指标（均值耗时、平均重试、工具成功率），实现综合 Benchmark。
6. **反馈闭环（RLHF 准备）**：加入 Feedback Collector（反馈收集器）与 Reward Scorer（奖励评分器），将用户点评和反馈转换为奖励信号，沉淀失败案例。

---

## 2. 适合插入的核心位置与组件设计

```
+-----------------------------------------------------------------------------------+
|                                 API & Streamlit UI                                |
+-----------------------------------------------------------------------------------+
        |                                                                   ^
        | 1. Submit Script / Evaluate                                       | 6. Collect Feedback
        v                                                                   |
+-----------------------------------------+   5. Calc Reward   +--------------------+
|  evaluation_workflow (Hybrid Workflow)  | -----------------> | Feedback / Scorer  |
+-----------------------------------------+                    +--------------------+
   |                   |               |                                |
   | Run Nodes         | Trace         | Call Tools                     | Write Logs
   v                   v               v                                v
+-------------+   +---------+   +---------------+              +--------------------+
| Agent Nodes |   | Trace   |   |  Tool Router  |              |  feedback_dataset  |
| (Reflection)|   | Metrics |   |  & Registry   |              |       (.json)      |
+-------------+   +---------+   +---------------+              +--------------------+
                                       |
                                       +--> (Save Character / Retrieve Rerank / Memory)
```

### 1) Tool Registry & Router (工具注册器与路由器)
* **位置**：新建 `backend/app/tools/` 目录。
* **组件**：
  - `registry.py`：注册系统内的基建组件为 Tool，如 `save_character_memory`、`load_character_memory`、`save_project_memory`、`load_project_memory`、`search_similar_works`。
  - `router.py`：所有 Agent 必须通过 Router 间接调用工具。Router 自动拦截异常、统计调用耗时并注入 Trace 日志。

### 2) Trace & Metrics (耗时与指标统计)
* **位置**：
  - 修改 `backend/app/schemas/report.py`（增加 `ToolTrace` 及 `NodeTrace` 字段）。
  - 修改 `backend/app/workflow/graph.py`（在 `_execute_node` 开始和结束处打点，统计耗时）。
  - 修改 `backend/app/tools/router.py`（在工具执行前后打点，记录工具耗时与输入输出）。

### 3) Recall + Rerank (检索重排)
* **位置**：
  - 修改 `backend/app/rag/retriever.py`。
  - 在 `MockRetriever` 类中新增 `rerank_candidates` 方法，基于**核心冲突 Jaccard 相似度**与**人物人设重合度**对 TF-IDF 召回的 Top-5 候选作品实施二次加权，最终输出 Top-2 对标证据。

### 4) Reflection Loop (反思机制)
* **位置**：
  - 修改 `backend/app/agents/analysis_agent.py` 与 `backend/app/agents/review_agent.py`。
  - `AnalysisAgent` 在第二轮执行时，不再单纯依据 `iterations == 0`，而是主动读取并解析 `state.review_issues` 中的问题描述与 `suggested_fix`（整改方向），进行有针对性的文本重构和对标绑定，完成“反思纠错”。

### 5) Feedback & Reward Scorer (反馈与奖励计算)
* **位置**：
  - 新建 `backend/app/feedback/` 目录，存放 `collector.py` 和 `scorer.py`。
  - 在 `backend/app/schemas/feedback.py` 定义用户满意度反馈模型。
  - 修改 `backend/app/api/routes.py` 新增 `POST /feedback` 路由，处理前端反馈并持久化。

---

## 3. 升级实施计划

### Phase 1: 基础定义与数据结构模型设计
* **主要目标**：确立 Tool 链路、Trace 指标与反馈的 Pydantic 规范。
* **修改/新建文件**：
  - `[NEW]` [feedback.py](file:///c:/Users/pengjiaying/Desktop/面向内容立项决策的剧本评估 Agent 系统/backend/app/schemas/feedback.py): 定义用户反馈模型 `FeedbackInput` 和持久化数据结构。
  - `[MODIFY]` [report.py](file:///c:/Users/pengjiaying/Desktop/面向内容立项决策的剧本评估 Agent 系统/backend/app/schemas/report.py): 
    - 扩展 `NodeTrace`：增加 `start_time`、`end_time`、`duration_ms` 及 `success` 状态。
    - 新增 `ToolTrace`：记录 `tool_name`、`arguments`、`result_summary`、`success`、`errors`、`duration_ms`。
    - 扩展 `FinalReport`：整合 `tool_traces` 字段以暴露给 API。
  - `[MODIFY]` [agent_state.py](file:///c:/Users/pengjiaying/Desktop/面向内容立项决策的剧本评估 Agent 系统/backend/app/schemas/agent_state.py): 增加 `tool_traces` 列表。
* **风险评估**：Schema 兼容性。需要保证新增字段拥有合理的默认值（如 `default_factory=list`），以防现有的 API 接口与旧数据在反序列化时发生崩溃。
* **验收标准**：通过本地 pytest 运行 `test_schemas.py` 成功。

### Phase 2: Tool Registry & Router 落地与 Agent 接入
* **主要目标**：构建解耦的工具体系，所有 Agent 原生 import 全局 Store 更改为路由调用。
* **修改/新建文件**：
  - `[NEW]` [registry.py](file:///c:/Users/pengjiaying/Desktop/面向内容立项决策的剧本评估 Agent 系统/backend/app/tools/registry.py): 实现 `BaseTool` 基类，注册记忆库读写和 RAG 检索 5 个系统工具。
  - `[NEW]` [router.py](file:///c:/Users/pengjiaying/Desktop/面向内容立项决策的剧本评估 Agent 系统/backend/app/tools/router.py): 实现 `ToolRouter` 类，提供 `call_tool(name, args, state)` 接口。
  - `[MODIFY]` [parser_agent.py](file:///c:/Users/pengjiaying/Desktop/面向内容立项决策的剧本评估 Agent 系统/backend/app/agents/parser_agent.py): 替换角色持久化写逻辑为 `save_character_memory` 工具调用。
  - `[MODIFY]` [analysis_agent.py](file:///c:/Users/pengjiaying/Desktop/面向内容立项决策的剧本评估 Agent 系统/backend/app/agents/analysis_agent.py): 替换角色加载逻辑为 `load_character_memory` 工具调用。
  - `[MODIFY]` [retrieval_agent.py](file:///c:/Users/pengjiaying/Desktop/面向内容立项决策的剧本评估 Agent 系统/backend/app/agents/retrieval_agent.py): 替换检索逻辑为 `search_similar_works` 工具调用。
  - `[MODIFY]` [graph.py](file:///c:/Users/pengjiaying/Desktop/面向内容立项决策的剧本评估 Agent 系统/backend/app/workflow/graph.py): 替换最终报告持久化归口为 `save_project_memory` 工具调用，并更新 `_execute_node` 逻辑实现节点耗时测算。
* **风险评估**：Agent 动态传参匹配。`ToolRouter` 在解析 Pydantic 字典时若存在类型不一致可能导致运行时异常。
* **验收标准**：通过新建的 `tests/test_tools.py`，验证工具注册和代理调用成功，工具执行时间成功被收集。

### Phase 3: Retrieval 检索升级 (召回 + Rerank)
* **主要目标**：提升检索可信度，形成两阶段检索链路。
* **修改/新建文件**：
  - `[MODIFY]` [retriever.py](file:///c:/Users/pengjiaying/Desktop/面向内容立项决策的剧本评估 Agent 系统/backend/app/rag/retriever.py):
    - 重构 `search_similar_works`，将候选数扩大为 `top_k = 5`（第一阶段：Recall 召回）。
    - 引入 `rerank_candidates`（第二阶段：Rerank 重排），通过两剧本核心冲突与人设性格的 Jaccard 字符交集对 Top-5 进行二次精细打分，输出 Top-2。
* **风险评估**：重排算法计算开销过大。因为是字符级比对，若单部剧本大纲过长，计算量会增加。可以通过提取关键词进行集合比对优化。
* **验收标准**：通过 `tests/test_retriever.py`，验证检索输出的 `score` 经过重排更新，且最终打分均合理约束在 `[0.0, 1.0]` 范围内。

### Phase 4: Critique-Driven 反思纠错回路 (Reflection)
* **主要目标**：使得重写逻辑具备“因果引导性”，而非基于状态次数的 Hardcode 判定。
* **修改/新建文件**：
  - `[MODIFY]` [analysis_agent.py](file:///c:/Users/pengjiaying/Desktop/面向内容立项决策的剧本评估 Agent 系统/backend/app/agents/analysis_agent.py):
    - 重构主逻辑：首先检查 `state.review_issues`。
    - 如果存在问题，遍历问题列表：
      - 若含 `unsupported_claim`：从对标检索结果中挑选合适案例，强行嵌入报告摘要，实现“有据可依”。
      - 若含 `character_inconsistency`：查找被指出的角色冲突，修改建议列表以符合 Memory 中的 character 设定。
      - 若含 `weak_suggestion`：定位空泛词汇（如“直接开拍”），定点将其改写为细化到剧集的落地操作。
* **风险评估**：自环死循环风险。如果 Analysis Agent 反思编写有逻辑漏洞，无法完全消除缺陷，可能导致 workflow 始终无法通过 Review 质检。
* **防护机制**：在 `graph.py` 中强制维持 `retry_count < 2`（Cap = 2）的硬阈值拦截，即使未完全解决也必须在第三次输出当前成果。
* **验收标准**：编写 `tests/test_reflection.py`，模拟输入带 ReviewIssue 的状态，断言 Analysis Agent 能动态修复该 Issue。

### Phase 5: Feedback 收集器与 Reward Scorer 闭环设计
* **主要目标**：沉淀人机交互反馈，用工程化数据反馈指导 Agent 参数/提示词优化。
* **修改/新建文件**：
  - `[NEW]` [collector.py](file:///c:/Users/pengjiaying/Desktop/面向内容立项决策的剧本评估 Agent 系统/backend/app/feedback/collector.py): 接收并持久化保存用户的 1-5 星打分和文本点评到 `backend/storage/feedback_dataset.json` 中。
  - `[NEW]` [scorer.py](file:///c:/Users/pengjiaying/Desktop/面向内容立项决策的剧本评估 Agent 系统/backend/app/feedback/scorer.py): 基于“用户评分、重试次数惩罚、运行报错惩罚、报告缺陷残留惩罚”计算自动化综合 Reward 奖励分（范围为 `[-1.0, 1.0]`）。
  - `[MODIFY]` [routes.py](file:///c:/Users/pengjiaying/Desktop/面向内容立项决策的剧本评估 Agent 系统/backend/app/api/routes.py): 新增 `POST /feedback` 路由，接受用户反馈并返回计算所得的 Reward 分值。
* **风险评估**：JSON 频繁写冲突。多用户评估并发时，读写同一个 JSON 可能会导致数据覆盖。
* **防护机制**：设计简易的排他写锁，或者在写文件前执行异常捕获并支持指数退避重试。
* **验收标准**：通过 `tests/test_feedback.py` 验证 feedback 写入持久化且 Reward 测算准确。

### Phase 6: 评测 Benchmark 升级与前端接入
* **主要目标**：展现工程化系统改进效果，建立直观监控。
* **修改/新建文件**：
  - `[MODIFY]` [run_eval.py](file:///c:/Users/pengjiaying/Desktop/面向内容立项决策的剧本评估 Agent 系统/backend/app/eval/run_eval.py):
    - 引入耗时记录，每次评估迭代累加耗时和工具调用次数。
    - 升级报表，对比三个方案的：平均端到端时延（`avg_latency_ms`）、平均打回重试次数（`avg_retries`）、工具调用总数及成功率。
  - `[MODIFY]` [demo.py](file:///c:/Users/pengjiaying/Desktop/面向内容立项决策的剧本评估 Agent 系统/backend/demo.py):
    - 在界面下方新增“用户反馈与打分”卡片（支持 Rating 星级与评语输入），点击可直接调用 `/feedback` 端点。
    - 在 Trace 选项卡中增加“Tool Call Traces（工具调用详情）”展示区，清晰渲染每个工具的耗时和参数。
* **风险评估**：Mock 模型速度过快导致耗时数据为 0。
* **处理方案**：在 Mock 阶段（若未接入真实 API 之前），可在 Tool 执行中加入 `time.sleep(0.01)` 以模拟真实网络开销，使 Benchmark 延时数据看起来更符合工业实际。
* **验收标准**：运行评测脚本，成功输出带有质量指标和耗时指标的完整 Markdown 对比表。

---

## 4. 推荐升级步骤与开发排期

| 顺序 | 升级阶段 | 核心改造文件 | 需覆盖的单元测试 | 预期输出 |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **Phase 1: 链路 Trace/Feedback 结构定义** | `schemas/report.py`<br>`schemas/agent_state.py`<br>`schemas/feedback.py` | `tests/test_schemas.py` | 确定 Trace 与 Feedback 数据规范 |
| **2** | **Phase 2: Tool Router 与 Registry 接入** | `tools/registry.py`<br>`tools/router.py`<br>`agents/` 目录所有 Agent<br>`workflow/graph.py` | `tests/test_tools.py` | 所有外部读写实现标准工具化调用，可追踪耗时 |
| **3** | **Phase 3: 双阶段检索 (Recall + Rerank)** | `rag/retriever.py`<br>`agents/retrieval_agent.py` | `tests/test_retriever.py` | 实现精细重排以防对标失真 |
| **4** | **Phase 4: Critique 反思质检自环** | `agents/analysis_agent.py`<br>`agents/review_agent.py` | `tests/test_reflection.py` | 打分和建议能根据 Review 意见定点修正 |
| **5** | **Phase 5: 反馈闭环与 Reward Scorer** | `feedback/collector.py`<br>`feedback/scorer.py`<br>`api/routes.py` | `tests/test_feedback.py` | 接口可接收用户评星、意见，计算综合收益并沉淀数据集 |
| **6** | **Phase 6: Benchmark 评测升级与 UI 渲染** | `eval/run_eval.py`<br>`demo.py` | `tests/test_eval.py` | 页面支持展示工具调用和满意度打分，Eval 输出完整性能指标 |

---

## 5. 测试覆盖设计要求

升级后，系统必须在原有的 30 项测试基础上增加以下测试以确保工程可靠性：

1. **`tests/test_tools.py`**：
   - 验证 `ToolRegistry` 重复注册工具时抛出异常。
   - 验证 `ToolRouter` 拦截不存在的工具名。
   - 验证工具正常调用时，`AgentState` 的 `tool_traces` 成功增加一条，且 `duration_ms > 0`。
   - 验证工具抛出异常时，Router 成功记录并抛出或处理，且 `success=False`。
2. **`tests/test_retriever_rerank.py`**：
   - 验证 TF-IDF 召回数量为 5，重排后最终裁剪为 2。
   - 验证重排后的第一名得分在对标冲突强时明显高于召回库其它数据。
3. **`tests/test_reflection.py`**：
   - 验证当输入 `review_issues` 中包含 `unsupported_claim` 时，AnalysisAgent 修正后的 `executive_summary` 中成功提及对标书名（形如《...》）。
   - 验证当输入 `review_issues` 中包含 `character_inconsistency` 时，修正建议中关于违规角色的动作得到了合规处理。
4. **`tests/test_feedback.py`**：
   - 验证 `POST /feedback` 提交不合法的评分范围（如 6 星）时返回 422 校验错误。
   - 验证对于有 errors 或是 retry_count 高的 trace，其 Reward 计算值有显著降级扣分。
   - 验证反馈文件 `feedback_dataset.json` 被正确写入。
