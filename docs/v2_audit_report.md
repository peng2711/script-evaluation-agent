# script-evaluation-agent V2 代码审计报告 (Code Audit Report)

本报告针对面向内容立项决策的剧本评估 Agent 系统（后端 `backend/app/` 目录及相关测试、文档）进行深度代码审计。本次审计在不修改业务代码、不重写已有模块、不引入新依赖的前提下，全面梳理了系统现有的能力、文档与代码的一致性、测试覆盖率以及未来的演进方向。

---

## 1. 已完成能力 (Implemented Capabilities)

经过对 `backend/app/` 目录下各核心模块的阅读与分析，系统已具备以下高度可控、可观测、可闭环评估的核心工程架构：

1. **確定性外層流程与內層纠错自环的 Hybrid Workflow (状态机协调器)**：
   - 核心代码：[graph.py](file:///c:/Users/pengjiaying/Desktop/面向内容立项决策的剧本评估 Agent 系统/backend/app/workflow/graph.py)
   - 系统实现了一个外层为确定性顺序的 Pipeline（`ParserNode` $\rightarrow$ `MemoryNode` $\rightarrow$ `AnalysisNode` $\rightarrow$ `RetrievalNode` $\rightarrow$ `ReviewNode` $\rightarrow$ `ReportNode` $\rightarrow$ `End`），确保合规审查不被随意跳过。
   - `ReviewNode` 能够根据审核问题决定自环回退路由：证据不足或错配打回至 `RetrievalNode`（流转动作：`retrieve_more`）；报告人设矛盾或建议太空泛打回至 `AnalysisNode`（流转动作：`rewrite_analysis`）。
   - 内部设计了 `max_iterations = 2` 的重试上限防护机制，避免模型陷入死循环。
   - 针对政策高危（`human_check`）动作，实现了拦截立项、在最终报告 executive_summary 中前置注入 `【建议人工复核】` 的硬编码阻断机制。

2. **安全白名单与输入输出强校验的 Tool Registry & Tool Router (工具调用网关)**：
   - 核心代码：[base.py](file:///c:/Users/pengjiaying/Desktop/面向内容立项决策的剧本评估 Agent 系统/backend/app/tools/base.py)、[registry.py](file:///c:/Users/pengjiaying/Desktop/面向内容立项决策的剧本评估 Agent 系统/backend/app/tools/registry.py)、[router.py](file:///c:/Users/pengjiaying/Desktop/面向内容立项决策的剧本评估 Agent 系统/backend/app/tools/router.py)
   - 实现了 6 个核心工具子类并统一向 `global_tool_registry` 注册，每个工具通过 `input_schema` 和 `output_schema` 进行 Pydantic 强类型约束，并附带 `allowed_agents` 白名单。
   - `ToolRouter` 提供全局调用网关，内置白名单鉴权（`validate_agent_permission`）、输入校验、执行报错降级（`get_tool_fallback`）以及输出结果校验。
   - 工作流协调器与各个 Agent（Parser、Retrieval、Analysis、Review）完全支持 `use_tools_via_router` 配置，在开启时所有外部交互走 `global_tool_router` 网关。

3. **双重持久化系统记忆模块 (Memory System)**：
   - 核心代码：[character_memory.py](file:///c:/Users/pengjiaying/Desktop/面向内容立项决策的剧本评估 Agent 系统/backend/app/memory/character_memory.py)、[project_memory.py](file:///c:/Users/pengjiaying/Desktop/面向内容立项决策的剧本评估 Agent 系统/backend/app/memory/project_memory.py)
   - 实现了项目决策记忆（存储历次评估报告 `FinalReport`）和角色人设记忆（在解析阶段将抽取的 `CharacterProfile`、性格标签、人设约束写入记忆库），避免多轮修改评估中人设坍塌。

4. **两阶段检索 (Recall + Rerank) 检索链路**：
   - 核心代码：[retriever.py](file:///c:/Users/pengjiaying/Desktop/面向内容立项决策的剧本评估 Agent 系统/backend/app/rag/retriever.py)、[retrieval_agent.py](file:///c:/Users/pengjiaying/Desktop/面向内容立项决策的剧本评估 Agent 系统/backend/app/agents/retrieval_agent.py)
   - **粗召回**：使用字符级 TF-IDF 相似度计算文本距离，配合题材（genre）与标签（tags）的相似度 Boost 加成，快速检索 Top 20 候选对标作品。
   - **精排**：实现 `Reranker` 重排模块，基于精确的加权公式（`0.3 * genre_match + 0.3 * tag_overlap + 0.3 * conflict_similarity + 0.1 * character_setup`）重新打分并筛选 Top 5，输出包含详细得分比重的 `relevance_reason`。
   - `RetrievalAgent` 精选 Top 2 证据注入状态机，保证市场对标的客观性。

5. **链路追踪与指标统计 (Observability Tracing & Metrics)**：
   - 核心代码：[trace.py](file:///c:/Users/pengjiaying/Desktop/面向内容立项决策的剧本评估 Agent 系统/backend/app/observability/trace.py)、[metrics.py](file:///c:/Users/pengjiaying/Desktop/面向内容立项决策的剧本评估 Agent 系统/backend/app/observability/metrics.py)、[logger.py](file:///c:/Users/pengjiaying/Desktop/面向内容立项决策的剧本评估 Agent 系统/backend/app/observability/logger.py)
   - 采用线程/协程安全的 `ContextVar` 实现全局统一的追踪记录器 `active_trace_recorder`。
   - 全方位埋点：工作流各个 Node 的启动、终止、报错，以及 ToolRouter 内工具调用的延迟、结果状态均实时记录为 `TraceEvent`，并以 JSON 格式输出至日志。
   - 实现评测指标计算（`calculate_metrics`），自动汇总总延迟、工具调用数、失败/降级数、重试数以及工作流成功标记。在最终的 `/evaluate` 返回中提供 `trace` 追踪链路。

6. **质检反思与审查规则 (Review Agent)**：
   - 核心代码：[review_agent.py](file:///c:/Users/pengjiaying/Desktop/面向内容立项决策的剧本评估 Agent 系统/backend/app/agents/review_agent.py)
   - 在独立上下文内运行，实现了编造剧情事件/人物、违背设定约束、人物关系错误、空泛建议、证据题材不匹配、政策红线合规等 7 种检查，并基于问题严重性给出 `retrieve_more`、`rewrite_analysis` 或 `human_check` 等修正反思动作。

7. **系统离线评测基准 (Eval Benchmark)**：
   - 核心代码：[run_eval.py](file:///c:/Users/pengjiaying/Desktop/面向内容立项决策的剧本评估 Agent 系统/backend/app/eval/run_eval.py)、[compare_modes.py](file:///c:/Users/pengjiaying/Desktop/面向内容立项决策的剧本评估 Agent 系统/backend/app/eval/compare_modes.py)
   - 支持对 10 条自带 Gold Standard 的样本数据进行批处理评测，动态计算包括 JSON 成功率、人设抽取准确度、冲突重合度、无依据评价比例在内的 10 个数学指标，并在控制台与 [eval_report.md](file:///c:/Users/pengjiaying/Desktop/面向内容立项决策的剧本评估 Agent 系统/backend/app/eval/eval_report.md) 中输出渲染好的 Markdown 跨模式对比图表。

---

## 2. 文档写了但代码不完整的地方 (Documentation vs. Code Discrepancies)

系统在工程框架上非常完备，但在“由 Mock 迈向真实生产环境”的过渡期，有部分代码在功能广度与通用性上弱于文档或 README 的描述：

1. **大语言模型未接入（纯 Python 启发式 Mock 占位）**：
   - **文档声称**：各个 Agent 能够智能阅读、客观抽取、评估打分。
   - **代码现状**：`ParserAgent`、`AnalysisAgent`、`ReviewAgent` 所有的实体抽取、主观质量判定、建议生成和质检规则，在代码中目前全都是**硬编码匹配测试样本关键字**（"林晚"、"林啸"、"陈默" 等）并返回静态 Mock 数据。当用户输入任意其它的非测试剧本时，系统会走向 Fallback 分支，退化成简陋的默认配置。真实大模型 API 尚未实际接入代码。

2. **评测指标在 Mock 状态下存在虚高**：
   - **文档声称**：Benchmark 通过基准评测来评估系统架构的优势（如 `json_success_rate` 可反向评估 JSON 反序列化的稳定性）。
   - **代码现状**：因为目前所有 Agent 节点均为硬编码 Python 代码直接实例化 Pydantic 类并将其赋值，而非真实 LLM 吐出 JSON 字符串再由代码解析。因此目前评测所得的 `json_success_rate` 恒定为 100.00%，无法真实体现架构拦截大模型不稳定输出（格式错乱、字段缺失等）的控制效果。

3. **并发隔离与读写文件锁缺失**：
   - **文档声称**：记忆库基于本地 JSON 文件，在高负载多并发下容易失效，但在升级计划等文档中提到了要处理并发。
   - **代码现状**：`project_memory.py` 和 `character_memory.py` 对本地 JSON 文件的读写属于最基础的 Python `json.load()` 和 `json.dump()`。没有任何文件锁机制（例如 `portalocker`），若有多个并发调用 `/evaluate` 请求同时更新同一个 `project_id` 或进行角色表写入，极易发生写冲突、文件内容损坏或数据覆盖丢失。

4. **无中文分词的 naive TF-IDF 召回**：
   - **文档声称**：使用了 TF-IDF 进行相似作品召回匹配。
   - **代码现状**：`rag/retriever.py` 中的 `_tokenize` 仅仅是利用 `re.findall` 保留了所有的汉字/英文字符并存入 `set`。它是一个“单字级”匹配器，并没有真正进行中文词组切分（没有引入如 `jieba` 分词等）。例如，搜索“拂晓”可能因为“拂”和“晓”字频原因无法良好召回“破晓”。

5. **Review 规则数量描述差异**：
   - **文档现状**：`README.md` 的 Section 5.3 声明 “Review Agent 在独立上下文内运行 6 种维度的启发式检测规则”。
   - **代码现状**：代码在 `review_agent.py` 内共实现了 7 种检测：`unsupported_claim`、`character_inconsistency`、`wrong_relation`、`hallucinated_event`、`weak_suggestion`、`evidence_mismatch` 以及额外的 `high_risk`（政策安全高危）。文档在此处的数字描述略显滞后。

---

## 3. 测试缺口 (Test Gaps)

虽然当前 pytest 测试套件拥有 62 个全通过（100% Passed）的用例，但在真实生产上线前仍存在以下测试覆盖盲区：

1. **真实 API 请求边界与异常测试缺口**：
   - 目前缺少传入真实 `llm_client` 后接口连接失败、Token 额度超限（Rate Limit）、或者是网络延迟严重时系统的鲁棒性测试，Agent 调用目前皆处在理想的同步 Mock 状态下。
2. **多进程并发与读写竞争测试缺口**：
   - 测试套件中完全没有针对本地 JSON 记忆库进行并发写压力测试（如开启 10 个线程同时对同一个 `project_id` 写入修改），没有验证在高吞吐下文件 I/O 读写是否安全。
3. **退化分支（未知未知剧本）测试缺口**：
   - 目前的集成测试都限定在预置的黄金样本剧本上。对于输入完全随机垃圾字符或大段无关叙事文本的外部剧本，没有针对 fallback 状态流转、Jaccard 语义重合底线以及质检是否会触发无限退回做详尽测试。
4. **Tool Router 的核心执行抛错测试缺口**：
   - 现有的测试主要覆盖了 Router 的白名单拦截与入参格式拦截。但如果工具的 `run` 方法本身执行报错（例如 RAG 知识库 json 读取损坏或缺失），Router 的异常捕获、`get_tool_fallback` 返回值与 trace 链路记录的正确性尚未进行充分的断言测试。

---

## 4. 下一步优先级 (Next Steps & Priorities)

为了让 script-evaluation-agent 从“Demo 骨架”升级为能服务真实影视立项的“生产级 AI 评估系统”，建议接下来的工作按以下优先级执行：

| 优先级 | 功能模块 | 具体任务建议 | 目的 / 物理意义 |
| :---: | :--- | :--- | :--- |
| **P0** | **真实 LLM 接入** | 将 `Parser`、`Analysis` 和 `Review` 节点的硬编码匹配，用真实的 Prompt 大模型接口调用（如 OpenAI / Gemini API）进行重写。 | 彻底摆脱 Mock 数据，实现对通用未知剧本的智能化信息提取与评分。 |
| **P1** | **数据库升级与事务隔离** | 将现有的本地 `character_memory.json` 与 `project_memory.json` 迁移至轻量级的本地 `SQLite`（或企业级 `PostgreSQL`），并使用 SQLAlchemy 的事务机制实现并发隔离。 | 解决本地并发读写冲突与死锁风险，为多用户并发提供底层技术支撑。 |
| **P1** | **向量化 RAG 检索器** | 舍弃 naive 的字符级 TF-IDF 匹配，将参考库和 Query 使用 Embedding 向量化，并接入向量数据库（如本地 Chroma / Qdrant）。 | 解决语义不匹配、近义词错召回、错对标等硬伤，提高 RAG 证据匹配度。 |
| **P2** | **评测基准真实化** | 接入真实 LLM 后，使用已注入错误的样本跑测 `compare_modes`。 | 观察真实的 `json_success_rate` 与 `review_issue_detection_rate` 等指标，优化各节点在真实生产环境下的纠错性价比。 |
| **P2** | **前端 Trace 可视化增强** | 在 Streamlit 页面上以图形化形式（如基于 Mermaid 渲染流程变化树或加载带色彩的时间线仪表盘）展示 trace 链路。 | 提升 B端 商业决策的可解释性与系统的交互体验。 |

---

## 5. 不建议继续做的方向 (Not Recommended Directions)

系统设计应该避免进入“低边际效应、高维护成本”的工程误区，不建议在以下方向投入开发精力：

1. **不建议在本地 JSON 文件存储上耗费精力开发锁机制**：
   - **原因**：试图在 `memory/` 中用原生 Python 手写复杂的读写文件锁以应对并发是极易出错且维护成本极高的。正确且成本最低的做法是直接引入关系型数据库（如 SQLite），利用其自带的页级锁/事务锁轻松解决高并发问题。

2. **不建议继续优化当前的字符级 TF-IDF 匹配算法**：
   - **原因**：由于中文字符的多样性与同义词泛化，字符级 TF-IDF 几乎无法支持影视立项中语义跨度极大的对标匹配。在该算法上调整参数或写复杂的 Boost 规则只是“螺蛳壳里做道场”，应果断转向向量嵌入（Vector Embedding）加余弦相似度的检索方案。

3. **不建议过度追求 100% 的 Mock 状态测试覆盖率**：
   - **原因**：现有的 Mock 测试集已经完全通过了核心状态机的所有逻辑覆盖。在不接入真实大模型接口的前提下，对 Mock 关键字分支编写更细致的单元测试，无法解决通用化问题，属于无意义的代码 churn。

4. **不建议在工作流中设计过深的自纠错迭代路由**：
   - **原因**：将质检反思打回的最大迭代次数 `max_iterations` 调高（例如重试 5-6 轮）虽然可能提高报告质量，但在真实 API 下会造成单次评估时间耗时达数分钟以上，并造成 Token 费用指数级暴涨。最大迭代保持为 2 次是在可用性、耗时与成本之间的最佳平衡点。
