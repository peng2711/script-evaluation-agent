import pytest
from app.agents.review_agent import ReviewAgent
from app.schemas.agent_state import AgentState
from app.schemas.script import ScriptInput
from app.schemas.report import ScriptAnalysis, RetrievalEvidence, CharacterProfile, PlotEvent, FinalReport, ReviewIssue
from app.memory.character_memory import global_character_memory

@pytest.fixture(autouse=True)
def setup_memory():
    # 每次测试前清空人设记忆，防止相互影响
    global_character_memory.clear()
    yield
    global_character_memory.clear()

def create_base_state():
    script = ScriptInput(
        project_id="test-review-project",
        title="测试剧本",
        raw_text="主要讲述了特工林啸与宿敌赵乾在边境集装箱码头进行生死对决的故事，黑客苏晴在外部提供网络战术配合。",
        genre="悬疑/动作",
        target_audience="硬核动作片受众",
        user_preferences=["偏好紧凑"]
    )
    
    analysis = ScriptAnalysis(
        characters=[
            CharacterProfile(
                name="林啸",
                role="特工",
                personality=["冷静", "机警"],
                motivation="缉捕走私犯赵乾",
                relationships={"赵乾": "宿敌", "苏晴": "绝对信任的盟友"},
                constraints=["不能伤害无辜百姓"],
                evidence_spans=["特工林啸", "生死对决"]
            ),
            CharacterProfile(
                name="赵乾",
                role="走私集团首脑",
                personality=["伪善", "残忍"],
                motivation="维持走私帝国",
                relationships={"林啸": "欲除之的眼中钉"},
                constraints=["不能直接触犯官方底线"],
                evidence_spans=["宿敌赵乾"]
            ),
            CharacterProfile(
                name="苏晴",
                role="女黑客",
                personality=["技术高超"],
                motivation="协助林啸",
                relationships={"林啸": "绝对信任的盟友"},
                constraints=[],
                evidence_spans=["黑客苏晴"]
            )
        ],
        character_relations=[
            "林啸与赵乾为宿敌敌对博弈关系",
            "苏晴是林啸强力的技术后盾"
        ],
        core_conflict="林啸对抗赵乾走私集团",
        plot_events=[
            PlotEvent(
                event_id="EVT-001",
                summary="林啸潜入码头",
                characters=["林啸"],
                conflict_type="潜入",
                evidence_span="林啸与宿敌赵乾在边境集装箱码头进行生死对决"
            )
        ],
        risk_points=[],
        strengths=[],
        weaknesses=[]
    )
    
    # 将角色写入 CharacterMemory 以供审查比对
    global_character_memory.save_characters(script.project_id, analysis.characters)
    
    evidences = [
        RetrievalEvidence(
            source_title="隐秘的角落",
            source_type="电视剧",
            content="角色之间高度对峙",
            relevance_reason="博弈心理对标",
            score=0.9
        )
    ]
    
    draft = FinalReport(
        project_id=script.project_id,
        title=script.title,
        executive_summary=(
            "【执行摘要评分报告】\n"
            "1. 角色人设维度: 4分。理由：林啸的特工人设表现良好，赵乾作为反派气场足够。\n"
            "2. 剧情逻辑维度: 4分。理由：起获证据推进链条合理。\n"
            "3. 冲突密度维度: 4分。理由：集装箱对峙拉扯节奏强。\n"
            "4. 市场适应度维度: 4分。理由：对标同题材悬疑证据《隐秘的角落》（检索匹配度 0.90），市场潜力大。\n"
            "建议该剧本经打磨后通过立项。"
        ),
        character_score=4,
        plot_logic_score=4,
        conflict_density_score=4,
        market_fit_score=4,
        evidence_list=evidences,
        review_issues=[],
        decision_suggestion="REVISE",
        improvement_suggestions=[
            "在第 1 集结尾增加林啸在书房发现赵乾秘密走私证据的悬念钩子。"
        ]
    )
    
    state = AgentState(
        script=script,
        analysis=analysis,
        evidences=evidences,
        review_issues=[],
        draft_report=draft,
        iterations=0
    )
    
    return state

def test_review_agent_fabricated_character():
    """
    1. 测试编造人物 (hallucinated_event)
    """
    agent = ReviewAgent()
    state = create_base_state()
    
    # 故意在摘要里引用一个没有在 ScriptAnalysis.characters 里出现的角色 '王强'
    state.draft_report.executive_summary += "\n在后续剧情中引入了配角王强的搞笑情节。"
    
    state = agent.execute(state)
    
    # 应该审查出问题，并且 should_rewrite_report 应该为 True
    assert state.should_rewrite_report is True
    assert len(state.review_issues) > 0
    
    # 查找是否有 hallucinated_event 类型的 issue
    fab_char_issues = [i for i in state.review_issues if i.issue_type == "hallucinated_event" and "王强" in i.claim]
    assert len(fab_char_issues) == 1
    
    issue = fab_char_issues[0]
    assert issue.severity == "HIGH"
    assert "王强" in issue.claim
    assert "不存在" in issue.reason
    assert issue.suggested_fix
    assert len(issue.suggested_fix) > 0

def test_review_agent_wrong_relationship():
    """
    2. 测试错误人物关系 (wrong_relation)
    """
    agent = ReviewAgent()
    state = create_base_state()
    
    # 原本林啸和赵乾是宿敌，故意写成他们是父子
    state.draft_report.executive_summary += "\n核心冲突展示了林啸与赵乾为父子的深层血缘张力。"
    
    state = agent.execute(state)
    
    assert state.should_rewrite_report is True
    wrong_rel_issues = [i for i in state.review_issues if i.issue_type == "wrong_relation"]
    assert len(wrong_rel_issues) > 0
    
    issue = wrong_rel_issues[0]
    assert "父子" in issue.claim
    assert "实际关系" in issue.reason
    assert "宿敌" in issue.reason
    assert len(issue.suggested_fix) > 0

def test_review_agent_unsupported_score():
    """
    3. 测试无依据评分 (unsupported_claim)
    """
    agent = ReviewAgent()
    state = create_base_state()
    
    # 移除所有的检索证据，并且摘要中不引用任何对标作品
    state.evidences = []
    state.draft_report.evidence_list = []
    state.draft_report.executive_summary = (
        "【执行摘要评分报告】\n"
        "1. 角色人设维度: 4分。理由：特工行当描写符合套路。\n"
        "2. 剧情逻辑维度: 3分。理由：主线脉络还算通顺。\n"
        "3. 冲突密度维度: 4分。理由：动作博弈较多。\n"
        "4. 市场适应度维度: 4分。理由：市场表现预计尚可。\n"
        "直接建议通过。"
    )
    
    state = agent.execute(state)
    
    assert state.should_rewrite_report is True
    # 因为 evidences 为空，并且没有 《...》 引用，应该判定为 unsupported_claim
    unsupported_issues = [i for i in state.review_issues if i.issue_type == "unsupported_claim"]
    assert len(unsupported_issues) > 0
    
    issue = unsupported_issues[0]
    assert "evidence_mismatch" not in issue.issue_type
    assert len(issue.claim) > 0
    assert len(issue.reason) > 0
    assert len(issue.suggested_fix) > 0

def test_review_agent_nonexistent_plot():
    """
    4. 测试引用不存在剧情 (hallucinated_event)
    """
    agent = ReviewAgent()
    state = create_base_state()
    
    # 剧本是特工枪战动作，故意在建议里提到了‘穿越到古代’的剧情
    state.draft_report.improvement_suggestions.append(
        "在第 2 集设计男主通过量子力学穿越到古代的情节点以丰富人物维度。"
    )
    
    state = agent.execute(state)
    
    assert state.should_rewrite_report is True
    plot_hallucinate_issues = [i for i in state.review_issues if i.issue_type == "hallucinated_event" and "穿越" in i.claim]
    assert len(plot_hallucinate_issues) == 1
    
    issue = plot_hallucinate_issues[0]
    assert "穿越" in issue.claim
    assert "剧情事件纯属报告幻觉编造" in issue.reason
    assert len(issue.suggested_fix) > 0

def test_review_agent_vague_suggestion():
    """
    5. 测试建议太空泛 (weak_suggestion)
    """
    agent = ReviewAgent()
    state = create_base_state()
    
    # 增加两个太空泛的建议
    state.draft_report.improvement_suggestions = ["直接开拍。", "加强人物塑造。"]
    
    state = agent.execute(state)
    
    assert state.should_rewrite_report is True
    vague_issues = [i for i in state.review_issues if i.issue_type == "weak_suggestion"]
    assert len(vague_issues) >= 1
    
    issue = vague_issues[0]
    assert "直接开拍" in issue.claim or "加强人物塑造" in issue.claim
    assert "过于空泛笼统" in issue.reason
    assert "具体集数" in issue.suggested_fix
