import pytest
from app.agents.analysis_agent import AnalysisAgent
from app.schemas.agent_state import AgentState
from app.schemas.script import ScriptInput
from app.schemas.report import ScriptAnalysis, RetrievalEvidence, CharacterProfile, PlotEvent

def test_analysis_agent_evaluation_rules():
    agent = AnalysisAgent()
    
    # 模拟输入状态
    script = ScriptInput(
        project_id="test-analysis-101",
        title="林晚沈知行的契约婚姻",
        raw_text="女主林晚，男主沈知行，两人契约婚姻，女主为了查清父亲死亡真相复仇。",
        genre="都市",
        target_audience="受众群体",
        user_preferences=[]
    )
    
    analysis = ScriptAnalysis(
        characters=[
            CharacterProfile(
                name="林晚",
                role="女主角",
                personality=["坚毅"],
                motivation="查清父亲死亡真相复仇",
                relationships={},
                constraints=[],
                evidence_spans=["女主林晚为了查清父亲死亡真相复仇。"]
            )
        ],
        character_relations=["林晚与沈知行是契约婚姻关系"],
        core_conflict="复仇",
        plot_events=[
            PlotEvent(
                event_id="EVT-001",
                summary="协议婚姻达成",
                characters=["林晚", "沈知行"],
                conflict_type="契约假结婚",
                evidence_span="两人契约婚姻"
            )
        ],
        risk_points=[],
        strengths=[],
        weaknesses=[]
    )
    
    evidences = [
        RetrievalEvidence(
            source_title="隐秘的角落",
            source_type="电视剧",
            content="相似故事大纲",
            relevance_reason="对标作品",
            score=0.95
        ),
        RetrievalEvidence(
            source_title="狂飙",
            source_type="电视剧",
            content="对垒博弈",
            relevance_reason="博弈逻辑参考",
            score=0.88
        )
    ]
    
    state = AgentState(
        script=script,
        analysis=analysis,
        evidences=evidences,
        review_issues=[],
        iterations=1  # 设置为1以生成修正通过的报告，检查具体集数修改建议
    )
    
    # 执行评估
    state = agent.execute(state)
    report = state.draft_report
    
    assert report is not None
    assert report.project_id == "test-analysis-101"
    
    # 1. 验证四大打分字段均在 [1, 5] 合法区间内
    for score in [report.character_score, report.plot_logic_score, report.conflict_density_score, report.market_fit_score]:
        assert 1 <= score <= 5
        
    # 2. 验证打分必须包含理由 (Reason)
    assert "角色人设维度" in report.executive_summary
    assert "分。理由：" in report.executive_summary
    assert "剧情逻辑维度" in report.executive_summary
    
    # 3. 验证建议的具体落地点（绑定具体集数，不可空泛）
    assert len(report.improvement_suggestions) > 0
    episodes_mentioned = ["第 1 集", "第 2 集", "第 3 集"]
    assert any(any(ep in sug for ep in episodes_mentioned) for sug in report.improvement_suggestions)
    
    # 4. 验证重要判断及修改建议与原文证据或检索对标作品绑定
    assert "林晚" in report.executive_summary or "沈知行" in report.executive_summary
    assert "《狂飙》" in report.executive_summary or "《隐秘的角落》" in report.executive_summary
    assert any("林晚" in sug or "沈知行" in sug for sug in report.improvement_suggestions)
