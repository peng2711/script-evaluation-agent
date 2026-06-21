import pytest
from app.agents.review_agent import ReviewAgent
from app.schemas.agent_state import AgentState
from app.schemas.script import ScriptInput
from app.schemas.report import ScriptAnalysis, RetrievalEvidence, CharacterProfile, FinalReport

def create_base_state():
    script = ScriptInput(
        project_id="test-reflection-project",
        title="测试剧本",
        raw_text="主要讲述了特工林啸与宿敌赵乾在边境集装箱码头进行生死对决的故事。",
        genre="悬疑/动作",
        target_audience="硬核动作片受众",
        user_preferences=[]
    )
    analysis = ScriptAnalysis(
        characters=[
            CharacterProfile(
                name="林啸",
                role="特工",
                personality=["冷静"],
                motivation="缉捕走私犯赵乾",
                relationships={"赵乾": "宿敌"},
                constraints=["不能伤害无辜百姓"],
                evidence_spans=["特工林啸"]
            )
        ],
        character_relations=["林啸与赵乾为宿敌"],
        core_conflict="林啸对抗赵乾",
        plot_events=[],
        risk_points=[],
        strengths=[],
        weaknesses=[]
    )
    evidences = [
        RetrievalEvidence(
            source_title="狂飙",
            source_type="电视剧",
            content="双雄对决戏剧张力强",
            relevance_reason="博弈心理对标",
            score=0.9
        )
    ]
    draft = FinalReport(
        project_id=script.project_id,
        title=script.title,
        executive_summary=(
            "【执行摘要评分报告】\n"
            "1. 角色人设维度: 4分。\n"
            "2. 剧情逻辑维度: 4分。\n"
            "3. 冲突密度维度: 4分。\n"
            "4. 市场适应度维度: 4分。对标检索证据作品《狂飙》中宿命对决。\n"
            "建议该剧本经打磨后通过立项。"
        ),
        character_score=4,
        plot_logic_score=4,
        conflict_density_score=4,
        market_fit_score=4,
        evidence_list=evidences,
        review_issues=[],
        decision_suggestion="PASS",
        improvement_suggestions=[
            "在第 1 集结尾增加林啸发现证据的悬念。"
        ]
    )
    return AgentState(
        script=script,
        analysis=analysis,
        evidences=evidences,
        review_issues=[],
        draft_report=draft,
        iterations=0
    )

def test_reflection_pass():
    """
    正常报告没有严重问题，触发 pass
    """
    agent = ReviewAgent()
    state = create_base_state()
    
    state = agent.execute(state)
    assert state.review_decision is not None
    assert state.review_decision.action == "pass"
    assert state.review_decision.passed is True

def test_reflection_retrieve_more():
    """
    无依据评价（如 evidences 为空）触发 retrieve_more
    """
    agent = ReviewAgent()
    state = create_base_state()
    
    # 移除检索证据和摘要中的对标说明
    state.evidences = []
    state.draft_report.evidence_list = []
    state.draft_report.executive_summary = (
        "【执行摘要评分报告】\n"
        "1. 角色人设维度: 4分。\n"
        "2. 剧情逻辑维度: 4分。\n"
        "3. 冲突密度维度: 4分。\n"
        "4. 市场适应度维度: 4分。预计市场表现良好。"
    )
    
    state = agent.execute(state)
    assert state.review_decision is not None
    assert state.review_decision.action == "retrieve_more"
    assert state.review_decision.passed is False

def test_reflection_rewrite_analysis():
    """
    建议太空泛触发 rewrite_analysis
    """
    agent = ReviewAgent()
    state = create_base_state()
    
    # 设置太空泛的建议
    state.draft_report.improvement_suggestions = ["直接开拍。"]
    
    state = agent.execute(state)
    assert state.review_decision is not None
    assert state.review_decision.action == "rewrite_analysis"
    assert state.review_decision.passed is False

def test_reflection_human_check():
    """
    高风险敏感词触发 human_check
    """
    agent = ReviewAgent()
    state = create_base_state()
    
    # 引入高风险关键词
    state.draft_report.executive_summary += "\n故事涉及私刑制裁，具有极大违规风险。"
    
    state = agent.execute(state)
    assert state.review_decision is not None
    assert state.review_decision.action == "human_check"
    assert state.review_decision.passed is False
