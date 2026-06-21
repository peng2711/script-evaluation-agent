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
