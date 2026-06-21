from ..schemas.agent_state import AgentState
from ..rag.retriever import mock_retriever
import datetime

class RetrievalAgent:
    """
    Retrieval Agent (Mock 实现)：调用 RAG 检索器，匹配同类作品作为评估论证证据，并填入 state.evidences。
    """
    def execute(self, state: AgentState) -> AgentState:
        state.history_logs.append(f"[{datetime.datetime.now().isoformat()}] RetrievalAgent 开始检索相似历史参考作品素材。")
        
        genre = state.script.genre or "通用"
        # 组合剧本大纲、题材及受众进行混合检索
        query_parts = [state.script.raw_text, genre, state.script.target_audience or ""]
        query_string = " ".join(query_parts)
        
        # 检索证据库
        evidences = mock_retriever.search_similar_works(query_string, top_k=2)
        
        state.evidences = evidences
        titles = [ev.source_title for ev in evidences]
        state.history_logs.append(f"[{datetime.datetime.now().isoformat()}] RetrievalAgent 检索完成。获取对比依据: {', '.join(titles) if titles else '无'}")
        return state

# 全局 RetrievalAgent 单例
retrieval_agent = RetrievalAgent()
