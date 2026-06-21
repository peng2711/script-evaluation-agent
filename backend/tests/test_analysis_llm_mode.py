import pytest
from app.agents.analysis_agent import AnalysisAgent
from app.agents.review_agent import ReviewAgent
from app.schemas.script import ScriptInput
from app.schemas.agent_state import AgentState
from app.schemas.report import ScriptAnalysis, RetrievalEvidence, FinalReport
from app.observability.trace import TraceRecorder, active_trace_recorder
from app.llm.mock_client import MockLLMClient

def test_analysis_mock_llm_success(monkeypatch):
    # 使用 MockLLMClient
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    agent = AnalysisAgent()
    
    script = ScriptInput(
        project_id="test-analysis-llm-1",
        title="契约婚姻复仇记",
        raw_text="女主林晚为了查清父亲死亡真相复仇，与男主沈知行契约婚姻。",
        genre="都市"
    )
    
    state = AgentState(
        script=script,
        analysis=ScriptAnalysis(
            characters=[],
            character_relations=[],
            core_conflict="林晚与沈知行的契约婚姻复仇",
            plot_events=[],
            risk_points=[],
            strengths=[],
            weaknesses=[]
        ),
        evidences=[
            RetrievalEvidence(
                source_title="隐秘的角落",
                source_type="电视剧",
                content="悬疑推理对标",
                relevance_reason="相似的复仇与宿命对抗",
                score=0.95
            )
        ],
        iterations=1
    )
    
    recorder = TraceRecorder()
    token = active_trace_recorder.set(recorder)
    try:
        state = agent.execute(state)
    finally:
        active_trace_recorder.reset(token)
        
    assert isinstance(state.draft_report, FinalReport)
    assert state.draft_report.project_id == "test-analysis-llm-1"
    
    # 验证评分与非空建议
    assert 1 <= state.draft_report.character_score <= 5
    assert 1 <= state.draft_report.plot_logic_score <= 5
    assert 1 <= state.draft_report.conflict_density_score <= 5
    assert 1 <= state.draft_report.market_fit_score <= 5
    assert len(state.draft_report.improvement_suggestions) > 0
    
    # 验证 trace 是否记录了 analysis_llm_call
    llm_calls = [e for e in recorder.events if e.tool_name == "analysis_llm_call"]
    assert len(llm_calls) == 1
    assert llm_calls[0].status == "SUCCESS"

def test_analysis_llm_fallback():
    # 实例化一个会抛出错误的 LLM 客户端
    class FaultyLLMClient:
        def generate_json(self, *args, **kwargs):
            raise ValueError("API connection timeout or invalid JSON")
            
    agent = AnalysisAgent(llm_client=FaultyLLMClient())
    
    script = ScriptInput(
        project_id="test-analysis-llm-2",
        title="契约婚姻复仇记",
        raw_text="女主林晚为了查清父亲死亡真相复仇，与男主沈知行契约婚姻。",
        genre="都市"
    )
    
    state = AgentState(
        script=script,
        analysis=ScriptAnalysis(
            characters=[],
            character_relations=[],
            core_conflict="林晚与沈知行的契约婚姻复仇",
            plot_events=[],
            risk_points=[],
            strengths=[],
            weaknesses=[]
        ),
        evidences=[
            RetrievalEvidence(
                source_title="隐秘的角落",
                source_type="电视剧",
                content="悬疑推理对标",
                relevance_reason="相似的复仇与宿命对抗",
                score=0.95
            )
        ],
        iterations=1
    )
    
    recorder = TraceRecorder()
    token = active_trace_recorder.set(recorder)
    try:
        state = agent.execute(state)
    finally:
        active_trace_recorder.reset(token)
        
    # 确认回退到启发式评估，仍然成功生成报告
    assert isinstance(state.draft_report, FinalReport)
    assert state.draft_report.character_score == 4
    assert state.draft_report.plot_logic_score == 3
    assert state.draft_report.decision_suggestion == "REVISE"
    
    # 验证 trace 记录了并且是 FALLBACK 状态
    llm_calls = [e for e in recorder.events if e.tool_name == "analysis_llm_call"]
    assert len(llm_calls) == 1
    assert llm_calls[0].status == "FALLBACK"
    assert "API connection timeout" in llm_calls[0].error_message

def test_analysis_missing_evidence_review_catches(monkeypatch):
    # 模拟没有 RAG 检索证据时，Review Agent 能拦截报告并判定为 unsupported_claim
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    agent = AnalysisAgent()
    review_agent = ReviewAgent()
    
    script = ScriptInput(
        project_id="test-analysis-llm-3",
        title="契约婚姻复仇记",
        raw_text="女主林晚为了查清父亲死亡真相复仇，与男主沈知行契约婚姻。",
        genre="都市"
    )
    
    # 故意将 evidences 设为空列表
    state = AgentState(
        script=script,
        analysis=ScriptAnalysis(
            characters=[],
            character_relations=[],
            core_conflict="林晚与沈知行的契约婚姻复仇",
            plot_events=[],
            risk_points=[],
            strengths=[],
            weaknesses=[]
        ),
        evidences=[], # 空的对标证据
        iterations=1
    )
    
    state = agent.execute(state)
    state = review_agent.execute(state)
    
    # 确认未通过 Review，且存在 unsupported_claim 质量缺陷
    assert state.review_decision.passed is False
    assert any(issue.issue_type == "unsupported_claim" for issue in state.review_issues)
