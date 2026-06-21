import pytest
from app.agents.parser_agent import ParserAgent
from app.schemas.script import ScriptInput
from app.schemas.agent_state import AgentState
from app.schemas.report import ScriptAnalysis
from app.llm.mock_client import MockLLMClient
from app.observability.trace import TraceRecorder, active_trace_recorder

def test_parser_mock_llm_success(monkeypatch):
    # 使用 MockLLMClient
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    agent = ParserAgent()
    
    script = ScriptInput(
        project_id="test-parser-llm-1",
        title="测试剧本",
        raw_text="林晚和沈知行的假结婚故事。",
        genre="都市"
    )
    
    # 模拟 trace 运行环境
    recorder = TraceRecorder()
    token = active_trace_recorder.set(recorder)
    try:
        analysis = agent.llm_extract(script)
    finally:
        active_trace_recorder.reset(token)
        
    assert isinstance(analysis, ScriptAnalysis)
    # 检查主观字段必须全部为空
    assert analysis.strengths == []
    assert analysis.weaknesses == []
    assert analysis.risk_points == []
    
    # 检查 trace 是否记录了 parser_llm_call
    llm_calls = [e for e in recorder.events if e.tool_name == "parser_llm_call"]
    assert len(llm_calls) == 1
    assert llm_calls[0].status == "SUCCESS"

def test_parser_llm_fallback():
    # 实例化一个会抛出异常的 LLM 客户端
    class FaultyLLMClient:
        def generate_json(self, *args, **kwargs):
            raise ValueError("API error or invalid JSON structure")
            
    agent = ParserAgent(llm_client=FaultyLLMClient())
    
    # 构造能够触发 heuristic parser 规则提取出“林晚”的剧本大纲
    state = AgentState(
        script=ScriptInput(
            project_id="test-parser-llm-2",
            title="契约婚姻复仇",
            raw_text="女主林晚为了查清父亲死亡真相复仇，与男主沈知行契约婚姻。",
            genre="都市/爱情"
        )
    )
    
    recorder = TraceRecorder()
    token = active_trace_recorder.set(recorder)
    try:
        # 执行 ParserAgent
        state = agent.execute(state)
    finally:
        active_trace_recorder.reset(token)
        
    # 验证是否成功回退到启发式解析，仍提取出了林晚人设事实
    assert state.analysis is not None
    char_names = [c.name for c in state.analysis.characters]
    assert "林晚" in char_names
    assert "沈知行" in char_names
    
    # 验证 trace 中记录了并且是 FALLBACK 状态
    llm_calls = [e for e in recorder.events if e.tool_name == "parser_llm_call"]
    assert len(llm_calls) == 1
    assert llm_calls[0].status == "FALLBACK"
    assert "API error" in llm_calls[0].error_message

def test_parser_no_subjective_eval():
    # 即使 MockClient 返回不规范数据或带有主观词，llm_extract 仍会重置它们
    class NonCompliantLLMClient(MockLLMClient):
        def generate_json(self, prompt: str, schema: dict, **kwargs) -> dict:
            # 强行塞入主观评价
            res = super().generate_json(prompt, schema, **kwargs)
            res["strengths"] = ["写得真好"]
            res["weaknesses"] = ["写得真差"]
            res["risk_points"] = ["政治风险"]
            return res
            
    agent = ParserAgent(llm_client=NonCompliantLLMClient())
    script = ScriptInput(
        project_id="test-parser-llm-3",
        title="测试剧本",
        raw_text="林啸和赵乾在集装箱码头起获军火。",
        genre="悬疑"
    )
    
    analysis = agent.llm_extract(script)
    # 确认在输出中主观评估已被定点清除/重置为空列表
    assert analysis.strengths == []
    assert analysis.weaknesses == []
    assert analysis.risk_points == []
