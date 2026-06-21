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
        
        import hashlib
        from ..cache.simple_cache import global_cache
        
        cache_key = f"retrieval:{hashlib.md5(query_string.encode('utf-8')).hexdigest()}"
        cached_evidences = global_cache.get(cache_key)
        if cached_evidences is not None:
            state.evidences = cached_evidences
            titles = [ev.source_title for ev in state.evidences]
            state.history_logs.append(
                f"[{datetime.datetime.now().isoformat()}] RetrievalAgent 缓存命中，直接恢复检索到的对标证据: {', '.join(titles) if titles else '无'}"
            )
            return state

        state.history_logs.append(f"[{datetime.datetime.now().isoformat()}] RetrievalAgent 缓存未命中，执行两阶段检索。")

        # 1. 第一阶段：粗召回 20 条候选对标作品
        state.history_logs.append(
            f"[{datetime.datetime.now().isoformat()}] [召回阶段] 获取候选对比数据。"
        )
        if state.use_tools_via_router:
            search_res = global_tool_router.call_tool(
                agent_name="RetrievalAgent",
                tool_name="similar_work_search_tool",
                arguments={"query": query_string, "top_k": 20}
            )
            recalled_evidences = search_res.evidences
        else:
            from ..rag.retriever import mock_retriever
            recalled_evidences = mock_retriever.search_similar_works(query_string, top_k=20)
        
        # 2. 第二阶段：对召回结果进行多维度精细重排 (取 Top 5)
        state.history_logs.append(
            f"[{datetime.datetime.now().isoformat()}] [重排阶段] 对候选证据进行多因子权重重排。"
        )
        if state.use_tools_via_router:
            rerank_res = global_tool_router.call_tool(
                agent_name="RetrievalAgent",
                tool_name="rerank_tool",
                arguments={"evidences": recalled_evidences, "query": query_string, "top_k": 5}
            )
            reranked_evidences = rerank_res.evidences
        else:
            from ..rag.reranker import mock_reranker
            reranked_evidences = mock_reranker.rerank(recalled_evidences, query_string, top_k=5)

        # 3. 筛选最终最精准的 Top 2 对标证据，注入状态机上下文
        state.evidences = reranked_evidences[:2]
        
        # 存入缓存
        global_cache.set(cache_key, state.evidences)
        
        titles = [ev.source_title for ev in state.evidences]
        state.history_logs.append(
            f"[{datetime.datetime.now().isoformat()}] RetrievalAgent 检索与重排完成。最终锁定对标证据: {', '.join(titles) if titles else '无'}"
        )
        return state

# 全局 RetrievalAgent 单例
retrieval_agent = RetrievalAgent()
