from ..schemas.agent_state import AgentState
from ..tools.router import global_tool_router
import datetime

class RetrievalAgent:
    """
    Retrieval Agent：实现“召回 + Rerank”的两阶段检索链路。
    所有的基建访问全部委托给 ToolRouter 执行，以确保符合统一安全调用规范。
    """
    def execute(self, state: AgentState) -> AgentState:
        state.history_logs.append(f"[{datetime.datetime.now().isoformat()}] RetrievalAgent 启动两阶段检索链。")
        
        genre = state.script.genre or "通用"
        query_parts = [state.script.raw_text, genre, state.script.target_audience or ""]
        query_string = " ".join(query_parts)
        
        # 1. 第一阶段：粗召回 20 条候选对标作品
        state.history_logs.append(
            f"[{datetime.datetime.now().isoformat()}] [召回阶段] 正在调用 similar_work_search_tool 获取候选对比数据。"
        )
        search_res = global_tool_router.call_tool(
            agent_name="RetrievalAgent",
            tool_name="similar_work_search_tool",
            arguments={"query": query_string, "top_k": 20}
        )
        recalled_evidences = search_res.evidences
        
        # 2. 第二阶段：对召回结果进行多维度精细重排 (取 Top 5)
        state.history_logs.append(
            f"[{datetime.datetime.now().isoformat()}] [重排阶段] 正在调用 rerank_tool 对候选证据进行多因子权重重排。"
        )
        rerank_res = global_tool_router.call_tool(
            agent_name="RetrievalAgent",
            tool_name="rerank_tool",
            arguments={"evidences": recalled_evidences, "query": query_string, "top_k": 5}
        )
        reranked_evidences = rerank_res.evidences
        
        # 3. 筛选最终最精准的 Top 2 对标证据，注入状态机上下文
        state.evidences = reranked_evidences[:2]
        
        titles = [ev.source_title for ev in state.evidences]
        state.history_logs.append(
            f"[{datetime.datetime.now().isoformat()}] RetrievalAgent 检索与重排完成。最终锁定对标证据: {', '.join(titles) if titles else '无'}"
        )
        return state

# 全局 RetrievalAgent 单例
retrieval_agent = RetrievalAgent()
