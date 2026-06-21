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
- RAG 知识库基于本地 JSON；
- 记忆模块（Memory）在内存中运行，服务重启后将丢失。
