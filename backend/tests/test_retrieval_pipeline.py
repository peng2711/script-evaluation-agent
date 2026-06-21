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

def test_hybrid_with_tools_rerank_tool_trace():
    from app.workflow.graph import ScriptEvaluationWorkflow
    
    script_input = ScriptInput(
        project_id="trace-test-rerank-tool-id",
        title="破晓行动",
        raw_text="特工林啸潜入集装箱码头，追踪走走私商人赵乾的走私帝国。",
        genre="动作",
        target_audience="大众"
    )
    
    # 实例化开启 use_tools_via_router 的工作流
    wf = ScriptEvaluationWorkflow(max_iterations=2, use_tools_via_router=True)
    report, state = wf.run_with_state(script_input)
    
    # 验证最终报告含有 trace 属性
    assert state.trace is not None
    events = state.trace.get("events", [])
    
    # 过滤出工具调用事件中，名为 rerank_tool 且状态为 SUCCESS 的记录
    rerank_tool_events = [
        e for e in events 
        if e.get("tool_name") == "rerank_tool" and e.get("status") == "SUCCESS"
    ]
    
    # 验证至少有一次成功的 rerank_tool 追踪事件
    assert len(rerank_tool_events) > 0
    # 验证 trace 的事件中包含了正确的 agent_name
    assert rerank_tool_events[0].get("agent_name") == "RetrievalAgent"
    assert rerank_tool_events[0].get("latency_ms") >= 0.0

