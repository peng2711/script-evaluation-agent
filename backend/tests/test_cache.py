import pytest
import time
from app.cache.simple_cache import SimpleCache, global_cache
from app.agents.parser_agent import parser_agent
from app.agents.retrieval_agent import retrieval_agent
from app.rag.reranker import mock_reranker
from app.schemas.script import ScriptInput
from app.schemas.agent_state import AgentState
from app.schemas.report import RetrievalEvidence
from app.workflow.graph import evaluation_workflow
from app.observability.trace import TraceRecorder, active_trace_recorder

def test_simple_cache_basic_operations():
    cache = SimpleCache()
    cache.set("key1", "value1", ttl_seconds=10)
    
    # 1. 验证基础 get/set 与命中
    assert cache.get("key1") == "value1"
    stats = cache.stats()
    assert stats["hit_count"] == 1
    assert stats["miss_count"] == 0
    assert stats["hit_rate"] == 1.0
    
    # 2. 验证未命中
    assert cache.get("nonexistent") is None
    stats = cache.stats()
    assert stats["miss_count"] == 1
    assert stats["hit_rate"] == 0.5
    
    # 3. 验证 TTL 过期
    cache.set("key2", "value2", ttl_seconds=1)
    # 延迟 1.1 秒以确保过期
    time.sleep(1.1)
    assert cache.get("key2") is None
    
    # 4. 验证清理
    cache.clear()
    assert cache.get("key1") is None
    assert cache.stats()["size"] == 0
    assert cache.stats()["hit_count"] == 0

def test_parser_agent_caching():
    global_cache.clear()
    
    state = AgentState(
        script=ScriptInput(
            project_id="test-parser-cache",
            title="契约婚姻复仇",
            raw_text="女主林晚为了查清父亲死亡真相复仇，与男主沈知行契约婚姻。",
            genre="都市/爱情"
        )
    )
    
    # 第一次执行：未命中
    state = parser_agent.execute(state)
    assert state.analysis is not None
    assert global_cache.stats()["miss_count"] == 1
    assert global_cache.stats()["hit_count"] == 0
    
    # 第二次执行：命中缓存
    state2 = AgentState(
        script=ScriptInput(
            project_id="test-parser-cache",
            title="契约婚姻复仇",
            raw_text="女主林晚为了查清父亲死亡真相复仇，与男主沈知行契约婚姻。",
            genre="都市/爱情"
        )
    )
    state2 = parser_agent.execute(state2)
    assert state2.analysis is not None
    assert global_cache.stats()["hit_count"] == 1

def test_retrieval_agent_caching():
    global_cache.clear()
    
    state = AgentState(
        script=ScriptInput(
            project_id="test-retrieval-cache",
            title="破晓行动",
            raw_text="特工林啸赵乾黑帮走私起获账目",
            genre="悬疑/动作"
        )
    )
    
    # 第一次执行：未命中
    state = retrieval_agent.execute(state)
    assert len(state.evidences) > 0
    # 检索本身会调用 RetrievalAgent (1 miss) + Reranker (1 miss)
    # 因为我们也在 Reranker 加上了缓存
    assert global_cache.stats()["miss_count"] >= 2
    
    # 清理后重新单独测试 RetrievalAgent 对 caching 的命中
    global_cache.clear()
    state_run1 = AgentState(
        script=ScriptInput(
            project_id="test-retrieval-cache",
            title="破晓行动",
            raw_text="特工林啸赵乾黑帮走私起获账目",
            genre="悬疑/动作"
        )
    )
    retrieval_agent.execute(state_run1)
    
    # 保存当前的命中状态
    before_stats = global_cache.stats()
    
    state_run2 = AgentState(
        script=ScriptInput(
            project_id="test-retrieval-cache",
            title="破晓行动",
            raw_text="特工林啸赵乾黑帮走私起获账目",
            genre="悬疑/动作"
        )
    )
    retrieval_agent.execute(state_run2)
    
    after_stats = global_cache.stats()
    # 验证命中次数增加了 1
    assert after_stats["hit_count"] == before_stats["hit_count"] + 1

def test_reranker_caching():
    global_cache.clear()
    
    evidences = [
        RetrievalEvidence(source_title="流浪地球", source_type="电影", content="科幻", relevance_reason="", score=0.0),
        RetrievalEvidence(source_title="老茶馆", source_type="电视剧", content="非遗", relevance_reason="", score=0.0),
    ]
    query = "科幻茶馆"
    
    # 第一次执行：未命中
    res1 = mock_reranker.rerank(evidences, query)
    assert len(res1) > 0
    assert global_cache.stats()["miss_count"] == 1
    
    # 第二次执行：命中
    res2 = mock_reranker.rerank(evidences, query)
    assert len(res2) == len(res1)
    assert global_cache.stats()["hit_count"] == 1

def test_workflow_end_to_end_caching_and_metrics():
    global_cache.clear()
    
    script_input = ScriptInput(
        project_id="test-workflow-cache",
        title="双重对决",
        raw_text="陈默与苏瑶在百年茶馆遭遇李建国强拆抗争资本。",
        genre="商战",
        target_audience="大众"
    )
    
    # 1. 第一次工作流执行：从清空状态开始
    recorder = TraceRecorder()
    token = active_trace_recorder.set(recorder)
    try:
        report1 = evaluation_workflow.run(script_input)
    finally:
        active_trace_recorder.reset(token)
        
    metrics1 = report1.trace["metrics"]
    assert metrics1["cache_miss_count"] > 0
    # 获取非完全缓存下的 LLM 调用次数与成本
    llm_calls_no_cache = metrics1["estimated_llm_calls"]
    cost_no_cache = metrics1["estimated_tool_cost"]
    
    # 2. 第二次工作流执行：由于剧本和参数一致，命中 ParserAgent 与 RetrievalAgent 缓存
    recorder = TraceRecorder()
    token = active_trace_recorder.set(recorder)
    try:
        report2 = evaluation_workflow.run(script_input)
    finally:
        active_trace_recorder.reset(token)
        
    metrics2 = report2.trace["metrics"]
    # 验证命中计数增加且未命中次数比第一轮少
    assert metrics2["cache_hit_count"] > metrics1["cache_hit_count"]
    assert metrics2["cache_miss_count"] < metrics1["cache_miss_count"]
    # 验证估算的 LLM API 调用次数因缓存命中而减少 (ParserAgent 命中)
    assert metrics2["estimated_llm_calls"] < llm_calls_no_cache
    # 验证工具调用次数与服务成本降低
    assert metrics2["estimated_tool_cost"] < cost_no_cache
