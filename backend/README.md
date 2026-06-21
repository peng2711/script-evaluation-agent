# 剧本评估 Agent 系统 (后端骨架与最小可行版本)

本项目是面向影视、短剧内容立项决策的智能评估系统后端骨架。通过多 Agent 协同流，对剧本文本进行深入解析，抽取关键信息，结合 RAG 对比进行风险把控，并生成具有逻辑依据的最终评估报告。

---

## 1. 项目目标与定位

本项目为 **B端决策辅助工具原型**。通过结构化输出与审评质检循环，辅助内容团队筛选优质剧本。

### Agent 节点与职责

- **Parser Agent（解析抽取节点）**：
  * **核心职责**：**只从剧本文本中抽取事实，坚决不做主观质量评价。**
  * **提取内容**：提取角色人设特征（`CharacterProfile`）、人物关系描述（`character_relations`）、核心戏剧冲突（`core_conflict`）以及包含原文支撑引用的剧情事件序列（`PlotEvent`）。
  * **红线约束**：绝不在其输出的 `ScriptAnalysis` 中添加任何带有“市场潜力巨大”、“商业价值高”、“节奏拖沓”等主观偏见判断的言论。主观维度的风险控制与优缺点交由后置的 `Analysis Agent` 权责管理。

- **Analysis Agent（评估分析节点）**：
  * **核心职责**：基于 Parser Agent 提取的客观元素、`CharacterMemory` 人设设定库以及 RAG 检索回的 `RetrievalEvidence` 同类对标作品，进行多维度的客观质量评估，打出 1~5 范围内的精细化评分。
  * **评估约束**：
    1. **有据可依**：在执行摘要（`executive_summary`）中为每一项打分（人物人设、剧情逻辑、冲突密度、市场契合）给出详尽的扣分与得分理由，且必须绑定抽取出的原文证据或检索对比证据。
    2. **落地修改建议**：拒绝“加强情感刻画”、“丰富人设”等空泛大词。所有的建议均必须指明具体的修改集数或段落行为（如“在第 1 集结尾增加女主在沈知行书房发现父亲遗留暗号线索的钩子”）。
  * **职责分割**：负责补充更新 `ScriptAnalysis` 报告中的优缺点（`strengths`/`weaknesses`）与政策/成本风险点（`risk_points`），并生成终版评估报告草稿。

---

## 2. 启动与运行方式

### 环境要求
- Python 3.10+
- 推荐使用 `conda` 或 `venv` 虚拟环境

### 本地启动步骤

1. **进入 backend 目录并激活环境**：
   ```bash
   cd backend
   # 激活您的虚拟环境（如 conda activate script-agent）
   ```

2. **安装依赖包**：
   ```bash
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

3. **启动 FastAPI 本地服务**：
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   启动成功后，API 交互文档地址为：[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

4. **启动 Streamlit 交互式 Demo 前端页面**：
   另开一个终端，在 `backend/` 目录下激活虚拟环境，并运行：
   ```bash
   streamlit run demo.py
   ```
   启动成功后，可在浏览器中访问：[http://localhost:8501](http://localhost:8501) 进行可视化交互式剧本评估与工作流 Trace 追踪查看。

---

## 3. 测试与评估说明

### 单元与集成测试 (Pytest)
在 `backend/` 目录下运行测试：
```bash
python -m pytest
```
测试会覆盖数据结构校验、Parser Agent 事实提取机制、异常请求处理、接口返回类型以及核心工作流的状态流转。

### 运行多机制对比评估脚本 (Eval)
我们提供了一个用于比对单 Prompt 生成、固定工作流、与含有 Review 纠错机制的 Agent 工作流差异的脚本。可在 `backend/` 目录下执行：
```bash
python -m app.eval.run_eval
```
该脚本将测试典型剧本大纲，输出三种流程模式下的打分、决策结论与纠错日志对比。

---

## 4. API 接口调用示例

### 接口 1: 健康检查
- **地址**: `GET /health`
- **返回**:
  ```json
  {"status": "ok"}
  ```

### 接口 2: 剧本解析（仅提取事实）
- **地址**: `POST /parse`
- **请求载荷 (ScriptInput)**:
  ```json
  {
    "project_id": "proj-101",
    "title": "林晚复仇记",
    "raw_text": "女主林晚，男主沈知行，两人契约婚姻，女主为了查清父亲死亡真相复仇。",
    "genre": "都市"
  }
  ```
- **返回格式 (ScriptAnalysis)**: 仅包含角色人设与事件事实的结构化数据，风险及优缺点字段均为空。

### 接口 3: 剧本立项决策评估
- **地址**: `POST /evaluate`
- **请求载荷 (ScriptInput)**:
  ```json
  {
    "project_id": "proj-901",
    "title": "破晓行动",
    "raw_text": "代号风影的特工林啸正在秘密追查跨国财阀首脑赵乾的走私线索，苏晴进行黑客配合...",
    "genre": "悬疑"
  }
  ```
- **返回格式 (FinalReport)**: 符合最终评估强校验结构的 JSON，其中包含打分评分（1-5）、RAG 检索证据列表以及 Review 审核纠错整改项。

---

## 5. 当前阶段局限性说明

具体详情请参阅文档：[limitations.md](docs/limitations.md)
- 所有推理均为 Mock，不消耗大模型 Token；
- RAG 知识库基于本地 JSON 文件；
- 记忆模块支持 JSON 文件持久化，但在多并发高负载场景下未加文件锁防死锁保护。

---

## 6. 系统记忆模块设计说明

为了在影视项目的长周期多轮修改与评估中保持人物设定、戏剧冲突以及个性化用户偏好的一致性，系统设计了双重记忆存储架构：

### 1. 项目决策记忆 (ProjectMemoryStore)
* **存储位置**：`backend/storage/project_memory.json`
* **功能**：归档每次对特定项目评估产出的 `FinalReport`。支持多轮评估的版本保存（`save_project`）、特定字段的局部更新（`update_project`）和列表导出，供 `/projects/{project_id}` 接口进行历史报告还原。

### 2. 角色人设记忆 (CharacterMemoryStore)
* **存储位置**：`backend/storage/character_memory.json`
* **功能**：由 `Parser Agent` 在完成角色事实抽取后批量持久化写入。能够跨评估节点锁定特定角色的动机（`motivation`）、性格标签（`personality`）和关系说明。支持特定项目下单一人物人设属性的更新（`update_character`），有效防范多轮评估中角色名混淆与背景设定崩塌。

---

## 7. 本地 RAG 检索设计说明

为了向评估结论提供有据可依的客观对比，系统实现了一个纯 Python 轻量级本地 RAG 检索器：

### 1. 算法工作原理
* **字符级 TF-IDF 余弦相似度**：在加载 `reference_works.json` 数据库后，系统实时构建字符级文档频率索引并计算 IDF。对输入的检索 Query 进行字符分词后，通过计算其余弦夹角获得基础文本匹配度分数。
* **题材与标签 Boost 加成**：如果检索 Query 完美包含了目标作品的 `genre`（题材）或命中其 `tags`（标签列表），会触发对应分值（最高 0.7）的 Boost 奖励分数叠加。
* **数据归一化**：最终的匹配度评分（`score`）限制在 0.0 至 1.0 区间。

### 2. 证据论证说明（非抄袭检测）
检索返回的 `RetrievalEvidence` 会由 `Retrieval Agent` 注入评估报告，仅作为“同题材立项成功/失败市场比对依据”或“戏剧冲突对标参考”。本模块不作任何法律层面的抄袭判定或相似度指控声明。

---

## 8. Hybrid Agent Workflow 工作流设计说明

为了保证剧本评估的关键业务环节不被遗漏，并兼顾在特定阶段（如检索不全、质检不合格）的灵活回退修正，系统设计并实现了 **Hybrid Agent Workflow（混合 Agent 工作流）** 状态机：

### 1. 确定性外层流程 (Outer Deterministic Flow)
外层工作流是一个确定性的顺序流程，首个生命周期严格按照以下顺序执行各节点，不被模型随意跳过：
1. **ParserNode**：解析并抽取剧本角色与事件要素；
2. **MemoryNode**：将抽取的人物与项目初始信息注册进入持久化记忆库；
3. **AnalysisNode**：多维度评估剧本质量、亮点和风险，生成报告草稿；
4. **RetrievalNode**：利用 TF-IDF 与题材 Boost 检索本地同类对标作品作为证据；
5. **ReviewNode**：独立核对评估草稿中的逻辑、幻觉和证据质量；
6. **ReportNode**：锁定并输出最终校验格式报告。

### 2. 局部补充自环修正 (Inner Correction Loop)
在 `ReviewNode` 质检过程中，内层逻辑通过评估报告中的反馈控制标志位控制状态路由回退：
- **打回检索 (`should_retrieve_more == True`)**：当发现检索证据不足或对标不匹配时，打回至 `RetrievalNode`。流转路径：`RetrievalNode` -> `AnalysisNode` -> `ReviewNode`；
- **打回重新分析 (`should_rewrite_report == True`)**：当发现人设冲突或评分无依据时，打回至 `AnalysisNode`。流转路径：`AnalysisNode` -> `ReviewNode`；
- **重试上限保护 (Retry Limit)**：质检迭代最大次数为 2 次。一旦达到重试上限，系统会自动锁定并流转至 `ReportNode` 生成报告，坚决杜绝无限循环。

### 3. 工作流状态图 (Workflow Diagram)
```mermaid
graph TD
    Start([开始]) --> ParserNode[1. ParserNode: 剧本解析]
    ParserNode --> MemoryNode[2. MemoryNode: 记忆持久化]
    MemoryNode --> AnalysisNode[3. AnalysisNode: 多维内容评估]
    AnalysisNode --> RetrievalNode[4. RetrievalNode: 检索同类证据]
    RetrievalNode --> ReviewNode{5. ReviewNode: 质检审查}
    
    ReviewNode -- "通过 / 达到重试上限(2次)" --> ReportNode[6. ReportNode: 生成最终报告]
    ReviewNode -- "证据不足 (should_retrieve_more)" --> RetrievalNode
    ReviewNode -- "报告有误 (should_rewrite_report)" --> AnalysisNode
    
    ReportNode --> End([结束])
```

### 4. 节点执行 Trace 追踪记录
为提升工作流透明度和可追溯性，系统使用 `NodeTrace` 数据结构记录每个执行节点，包含：
* `node_name` (节点名称)
* `input_summary` (输入数据摘要)
* `output_summary` (输出数据或状态摘要)
* `errors` (异常/错误捕捉说明)
* `retry_count` (节点所处的重试轮次)

---

## 9. Eval 评估指标设计与物理意义

为了量化不同剧本评估方案在性能、准确度和稳定性上的优劣，系统定义并计算了 7 个核心的评估指标：

### 1. JSON 成功率 (`json_success_rate`)
* **定义**：计算工作流输出的报告对象转换为合法 JSON，并能成功被 Pydantic `FinalReport` 模型反序列化验证通过的概率。
* **物理意义**：衡量输出数据的结构稳定性和规范性。由于系统有严格的 Pydantic 数据模式（如评分限制在 1-5），该指标越接近 100%，表示系统的结构鲁棒性越高。

### 2. 人物抽取准确率 (`character_extraction_accuracy`)
* **定义**：计算提取出的角色名称集合与黄金标注（Gold Standard）角色集合的 Jaccard 相似度系数。
* **计算公式**：
  \[\text{Accuracy}_{\text{char}} = \frac{|S_{\text{extracted}} \cap S_{\text{gold}}|}{|S_{\text{extracted}} \cup S_{\text{gold}}|}\]
* **物理意义**：评估 Parser Agent 进行实体（人物角色）抽取的覆盖率与精确度。

### 3. 核心冲突准确率 (`core_conflict_accuracy`)
* **定义**：计算提取出的核心戏剧冲突文本与黄金核心冲突文本的字符级别（Character-level）Jaccard 相似度。
* **物理意义**：反映系统在提取故事最主要矛盾时的语义贴合度。

### 4. 证据引用准确率 (`evidence_precision`)
* **定义**：报告中引用的对标证据作品（`evidence_list` 里的标题）命中基准要求的 `expected_evidence_keywords` 的比率。
* **物理意义**：衡量 RAG 检索器为报告匹配合适对标证据的精确性。未引入 RAG 的 Baseline 方案该指标接近 0%。

### 5. 无依据评价比例 (`unsupported_claim_rate`)
* **定义**：最终产出的评估报告中，依然被 Review Agent 独立质检规则诊断出含有 `unsupported_claim`（无依据打分或无对标引用）问题项的报告占比。
* **物理意义**：衡量评估报告的“主观偏见/无依据论证”概率。具有 Review 质检自环修正的 Hybrid 工作流该比例会大幅降到接近 0%。

### 6. 质检缺陷检出率 (`review_issue_detection_rate`)
* **定义**：在测试用例存在逻辑硬伤或对标错误时，工作流顺利触发 Review 质检并记录缺陷问题列表的比率。
* **物理意义**：反映审查机制的参与度和主动检出效率。非自环/无质检方案该指标为 0.0。

### 7. 工作流完成率 (`workflow_success_rate`)
* **定义**：工作流顺利执行到底，各节点在执行中未捕获到崩溃性 Exception 异常的概率。
* **物理意义**：评估系统整体的稳定运行效率。


