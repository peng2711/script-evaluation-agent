from ..schemas.agent_state import AgentState
from ..rag.retriever import mock_retriever
import datetime

class RetrievalAgent:
    """
    Retrieval Agent (Mock 实现)：检索同类作品或素材库，为评估结论提供证据。
    """
    def execute(self, state: AgentState) -> AgentState:
        state.history_logs.append(f"[{datetime.datetime.now().isoformat()}] RetrievalAgent 开始检索同类作品。")
        
        genre = state.script.genre or "通用"
        query = state.script.content[:100]  # 使用内容的前100字作为简要查询
        
        # 调用 mock 检索器
        references = mock_retriever.retrieve_similar_works(genre, query)
        
        state.retrieved_references = references
        
        titles = [ref.title for ref in references]
        state.history_logs.append(f"[{datetime.datetime.now().isoformat()}] RetrievalAgent 检索完成。找到相似作品：{', '.join(titles) if titles else '无'}")
        return state

# 全局 RetrievalAgent 单例
retrieval_agent = RetrievalAgent()
