import pytest
from app.schemas.agent_state import AgentState
from app.schemas.script import ScriptInput
from app.agents.retrieval_agent import retrieval_agent
from app.tools.router import global_tool_router
from app.tools.tool_schemas import RerankOutput, SimilarWorkSearchOutput

def test_tool_router_can_call_rerank_tool():
    # 模拟初筛数据
    search_res = global_tool_router.call_tool(
        agent_name="RetrievalAgent",
        tool_name="similar_work_search_tool",
        arguments={"query": "科幻末日重工业电影", "top_k": 20}
    )
    assert isinstance(search_res, SimilarWorkSearchOutput)
    assert len(search_res.evidences) > 0
    
    # 模拟重排请求
    rerank_res = global_tool_router.call_tool(
        agent_name="RetrievalAgent",
        tool_name="rerank_tool",
        arguments={
            "evidences": search_res.evidences,
            "query": "科幻末日重工业电影",
            "top_k": 2
        }
    )
    assert isinstance(rerank_res, RerankOutput)
    assert len(rerank_res.evidences) == 2
    assert rerank_res.evidences[0].source_title == "流浪地球"

def test_retrieval_agent_pipeline_integration():
    script_input = ScriptInput(
        project_id="retrieval-test-id",
        title="破晓猎杀",
        raw_text="特工林啸潜入码头，追踪跨国走私商人赵乾的走私帝国。",
        genre="动作",
        target_audience="大众"
    )
    state = AgentState(script=script_input)
    
    # 执行 RetrievalAgent 的两阶段链路
    updated_state = retrieval_agent.execute(state)
    
    # 校验最终锁定的 evidences 数量为 2
    assert len(updated_state.evidences) == 2
    
    # 校验每条 evidence 的字段完整性
    for ev in updated_state.evidences:
        assert ev.source_title in ["狂飙", "隐秘的角落", "流浪地球"]
        assert len(ev.relevance_reason) > 0
        assert "【精排依据】" in ev.relevance_reason
        assert 0.0 <= ev.score <= 1.0
