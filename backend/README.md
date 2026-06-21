# 剧本评估 Agent 系统 (后端骨架与最小可行版本)

本项目是面向影视、短剧内容立项决策的智能评估系统后端骨架。通过多 Agent 协同流，对剧本文本进行深入解析，抽取关键信息，结合 RAG 对比进行风险把控，并生成具有逻辑依据的最终评估报告。

---

## 1. 项目目标与定位

本项目为 **B端决策辅助工具原型**。通过结构化输出与审评质检循环，辅助内容团队筛选优质剧本。
第一阶段实现了项目整体目录结构骨架与 API 校验层，对所有推理节点及检索库进行了 Mock 模拟。

---

## 2. 启动与运行方式

### 环境要求
- Python 3.10+
- 推荐使用 `venv` 虚拟环境

### 本地启动步骤

1. **创建并激活虚拟环境**：
   ```bash
   cd backend
   python -m venv .venv
   # Windows 激活方式:
   .venv\Scripts\activate
   # macOS/Linux 激活方式:
   source .venv/bin/activate
   ```

2. **安装依赖包**：
   ```bash
   pip install -r requirements.txt
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
pytest
```
测试会覆盖数据结构校验、异常请求处理、接口返回类型以及核心工作流的状态流转。

### 运行多机制对比评估脚本 (Eval)
我们提供了一个用于比对单 Prompt 生成、固定工作流、与含有 Review 纠错机制的 Agent 工作流差异的脚本。可在 `backend/` 目录下执行：
```bash
# 确保在 python path 中包含当前 backend 目录
python -m app.eval.run_eval
```
该脚本将测试两种经典剧本大纲，输出三种流程模式下的不同质量结论与决策路径对比。

---

## 4. API 接口调用示例

### 接口 1: 健康检查
- **地址**: `GET /health`
- **返回**:
  ```json
  {"status": "ok"}
  ```

### 接口 2: 剧本立项评估
- **地址**: `POST /evaluate`
- **请求载荷**:
  ```json
  {
    "title": "破晓行动",
    "content": "代号风影的特工林啸正在秘密追查跨国财阀首脑赵乾的走私线索，苏晴进行黑客配合...",
    "author": "编剧张三",
    "genre": "悬疑"
  }
  ```
- **返回格式**: 符合 `EvaluationReport` 强校验结构的 JSON，其中包含 `characters`, `relations`, `events`, `risks`, `references`, 以及 `conclusion` 等字段。

---

## 5. 当前阶段局限性说明

具体详情请参阅文档：[limitations.md](docs/limitations.md)
- 所有推理均为 Mock，不消耗大模型 Token；
- RAG 知识库基于本地 JSON；
- 记忆模块（Memory）在内存中运行，服务重启后将丢失。
