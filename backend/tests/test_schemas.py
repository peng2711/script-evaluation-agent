import pytest
from pydantic import ValidationError
from app.schemas.script import ScriptInput
from app.schemas.report import FinalReport, CharacterProfile, PlotEvent, ScriptAnalysis, RetrievalEvidence, ReviewIssue

def test_script_input_validation():
    # 1. 测试合法输入
    script = ScriptInput(
        project_id="proj-101",
        title="测试项目",
        raw_text="正文大纲",
        genre="科幻",
        target_audience="大众",
        user_preferences=["偏好快节奏"]
    )
    assert script.project_id == "proj-101"
    assert script.title == "测试项目"
    assert script.user_preferences == ["偏好快节奏"]

    # 2. 测试非法输入（缺失必填字段 project_id）
    with pytest.raises(ValidationError):
        ScriptInput(title="测试", raw_text="正文")

    # 3. 测试 JSON 序列化与反序列化
    json_data = script.model_dump_json()
    parsed = ScriptInput.model_validate_json(json_data)
    assert parsed.project_id == "proj-101"
    assert parsed.title == "测试项目"

def test_final_report_score_ranges():
    # 构建合法的嵌套字段
    evidence = RetrievalEvidence(
        source_title="相似电影",
        source_type="电影",
        content="内容详情",
        relevance_reason="相似理由",
        score=0.9
    )
    
    # 1. 测试合法输入（分数全为 1-5 之间）
    report = FinalReport(
        project_id="proj-101",
        title="项目名称",
        executive_summary="执行总结说明",
        character_score=5,
        plot_logic_score=4,
        conflict_density_score=3,
        market_fit_score=1,
        evidence_list=[evidence],
        review_issues=[],
        decision_suggestion="PASS",
        improvement_suggestions=["修改台词"]
    )
    assert report.character_score == 5
    assert report.market_fit_score == 1
    
    # 2. 测试非法输入（分数大于 5）
    with pytest.raises(ValidationError):
        FinalReport(
            project_id="proj-101",
            title="项目名称",
            executive_summary="执行总结说明",
            character_score=6,  # 非法！超出了 le=5 限制
            plot_logic_score=4,
            conflict_density_score=3,
            market_fit_score=1,
            evidence_list=[evidence],
            review_issues=[],
            decision_suggestion="PASS",
            improvement_suggestions=[]
        )

    # 3. 测试非法输入（分数小于 1）
    with pytest.raises(ValidationError):
        FinalReport(
            project_id="proj-101",
            title="项目名称",
            executive_summary="执行总结说明",
            character_score=5,
            plot_logic_score=0,  # 非法！低于了 ge=1 限制
            conflict_density_score=3,
            market_fit_score=1,
            evidence_list=[evidence],
            review_issues=[],
            decision_suggestion="PASS",
            improvement_suggestions=[]
        )

    # 4. 测试 JSON 序列化/反序列化
    json_str = report.model_dump_json()
    parsed_report = FinalReport.model_validate_json(json_str)
    assert parsed_report.character_score == 5
    assert parsed_report.plot_logic_score == 4
    assert parsed_report.evidence_list[0].source_title == "相似电影"
