import pytest
from pydantic import ValidationError
from app.schemas.script import ScriptSubmission
from app.schemas.report import EvaluationReport, Character, CharacterRelation, PlotEvent, Conflict, RiskPoint, ReferenceWork, ReviewResult, RoleType, SeverityType, DecisionType

def test_script_submission_validation():
    # 正确的数据
    script = ScriptSubmission(
        title="我的科幻大片",
        content="讲述了未来的故事...",
        author="张三",
        genre="科幻"
    )
    assert script.title == "我的科幻大片"
    assert script.author == "张三"

    # 缺失必填字段 title
    with pytest.raises(ValidationError):
        ScriptSubmission(content="仅有正文")

    # 缺失必填字段 content
    with pytest.raises(ValidationError):
        ScriptSubmission(title="仅有标题")

def test_evaluation_report_schema():
    # 测试完整的结构化报告校验
    char1 = Character(name="林啸", role=RoleType.PROTAGONIST, description="特工")
    char2 = Character(name="赵乾", role=RoleType.ANTAGONIST, description="反派")
    
    relation = CharacterRelation(
        source_character="林啸",
        target_character="赵乾",
        relation_type="敌对",
        description="追捕关系"
    )
    
    event = PlotEvent(
        title="潜入起获",
        description="秘密潜入赵乾仓库",
        significance="重要转折"
    )
    
    conflict = Conflict(
        description="黑白对立博弈",
        characters_involved=["林啸", "赵乾"]
    )
    
    risk = RiskPoint(
        category="政策安全",
        description="爆破戏过多",
        severity=SeverityType.HIGH
    )
    
    ref = ReferenceWork(
        title="隐秘的角落",
        similarity_reason="同款暗黑对抗悬疑",
        benchmark_metric="豆瓣 8.8"
    )
    
    review = ReviewResult(
        is_passed=True,
        findings=[],
        revision_suggestions=[]
    )
    
    report = EvaluationReport(
        script_id="test-123",
        title="测试剧本",
        genre="悬疑",
        characters=[char1, char2],
        relations=[relation],
        events=[event],
        conflicts=[conflict],
        risks=[risk],
        references=[ref],
        review=review,
        conclusion=DecisionType.REVISE,
        summary="评估完成"
    )
    
    assert report.script_id == "test-123"
    assert len(report.characters) == 2
    assert report.conclusion == DecisionType.REVISE
    assert report.review.is_passed is True
