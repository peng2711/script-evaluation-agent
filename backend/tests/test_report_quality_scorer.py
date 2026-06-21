import pytest
from app.quality.scorer import score_report
from app.schemas.report import FinalReport, ReviewIssue, RetrievalEvidence

def test_perfect_report_score():
    # 模拟一份高水平、完整的报告
    report = {
        "project_id": "proj-perfect",
        "title": "完美剧本计划",
        "executive_summary": "这只是一份高水平的剧本立项执行评估摘要信息说明。",
        "character_score": 5,
        "plot_logic_score": 4,
        "conflict_density_score": 4,
        "market_fit_score": 5,
        "decision_suggestion": "PASS",
        "improvement_suggestions": [
            "在第 1 集开头增加 5 分钟动作追逐场面以吸引核心受众。",
            "在第 3 集结尾安排女主角发现身世秘密的冲突高潮。"
        ],
        "risk_points": ["制作预算有超支风险", "审查存在合规雷区"],
        "evidence_list": [
            {"source_title": "对标作品A", "source_type": "悬疑", "content": "剧情对标证据", "score": 0.85}
        ]
    }
    
    score = score_report(
        report=report,
        review_issues=[],
        evidence_list=report["evidence_list"]
    )
    
    assert score.evidence_score == 100.0
    assert score.structure_score == 100.0
    assert score.actionable_score == 100.0
    assert score.consistency_score == 100.0
    assert score.risk_coverage_score == 100.0
    assert score.final_score == 100.0
    assert len(score.reasons) == 0

def test_missing_evidence_and_unsupported_claim():
    # 缺失证据且有 unsupported_claim 质检问题
    report = {
        "project_id": "proj-bad-evidence",
        "title": "空头证据剧本",
        "executive_summary": "这是一份没有证据的执行摘要。",
        "character_score": 3,
        "plot_logic_score": 3,
        "conflict_density_score": 3,
        "market_fit_score": 3,
        "decision_suggestion": "REVISE",
        "improvement_suggestions": ["合理的长于十个字符修改建议！"],
        "risk_points": ["政策风险"],
        "evidence_list": []
    }
    
    issues = [
        ReviewIssue(
            issue_type="unsupported_claim",
            severity="MEDIUM",
            claim="评分过高",
            reason="缺少对标作品数据支持",
            suggested_fix="补充 RAG 检索对标论证"
        )
    ]
    
    score = score_report(report=report, review_issues=issues)
    
    assert score.evidence_score == 30.0  # 100.0 - 50.0 (空证据) - 20.0 (unsupported_claim)
    assert "evidence_list 为空" in score.reasons[0]
    assert "unsupported_claim" in score.reasons[1]
    assert score.final_score < 100.0

def test_missing_core_fields():
    # 报告严重缺失核心字段
    report = {
        "project_id": "proj-empty",
        "title": "", # 空标题
        "executive_summary": "", # 空摘要
        "decision_suggestion": "",
        "character_score": 0, # 错误评分
        "improvement_suggestions": ["合理的长于十个字符修改建议！"],
        "risk_points": ["政策风险"],
        "evidence_list": [{"source_title": "对标作品A"}]
    }
    
    score = score_report(report=report, review_issues=[])
    
    # 缺失 title, executive_summary, decision_suggestion, character_score, plot_logic_score, conflict_density_score, market_fit_score
    # 7 个核心字段有问题，100.0 - 15.0 * 7 = -5.0 -> max(0, -5.0) = 0.0
    assert score.structure_score == 0.0
    assert len(score.reasons) > 0

def test_empty_or_weak_suggestions():
    # 改进建议为空或太短
    report_empty = {
        "project_id": "proj-sugg",
        "title": "测试",
        "executive_summary": "测试内容大纲摘要信息说明",
        "character_score": 3,
        "plot_logic_score": 3,
        "conflict_density_score": 3,
        "market_fit_score": 3,
        "decision_suggestion": "PASS",
        "improvement_suggestions": [], # 为空
        "risk_points": ["政策风险"],
        "evidence_list": [{"source_title": "对标作品A"}]
    }
    
    score_empty = score_report(report=report_empty)
    assert score_empty.actionable_score == 40.0  # 100.0 - 60.0 (为空)
    
    report_short = {
        "project_id": "proj-sugg",
        "title": "测试",
        "executive_summary": "测试内容大纲摘要信息说明",
        "character_score": 3,
        "plot_logic_score": 3,
        "conflict_density_score": 3,
        "market_fit_score": 3,
        "decision_suggestion": "PASS",
        "improvement_suggestions": ["太短", "也太短了"], # 均短于 10 字符
        "risk_points": ["政策风险"],
        "evidence_list": [{"source_title": "对标作品A"}]
    }
    
    score_short = score_report(report=report_short)
    assert score_short.actionable_score == 70.0  # 100.0 - 30.0 (2 * 15)
    
    issues = [ReviewIssue(issue_type="weak_suggestion", severity="LOW", claim="修改偏空泛", reason="无具体集数", suggested_fix="说明集数")]
    score_weak = score_report(report=report_short, review_issues=issues)
    assert score_weak.actionable_score == 50.0  # 100.0 - 30.0 (2 * 15) - 20.0 (weak_suggestion)

def test_character_inconsistency_and_hallucination():
    # 包含人物矛盾和事实幻觉的报告
    report = {
        "project_id": "proj-consist",
        "title": "一致性测试",
        "executive_summary": "测试大纲内容",
        "character_score": 3,
        "plot_logic_score": 3,
        "conflict_density_score": 3,
        "market_fit_score": 3,
        "decision_suggestion": "PASS",
        "improvement_suggestions": ["合理的长于十个字符修改建议！"],
        "risk_points": ["风险点"],
        "evidence_list": [{"source_title": "对标作品A"}]
    }
    
    issues = [
        ReviewIssue(
            issue_type="character_inconsistency",
            severity="HIGH",
            claim="人设违背设定",
            reason="违反了不杀人设定",
            suggested_fix="修改情节"
        ),
        ReviewIssue(
            issue_type="wrong_relation",
            severity="MEDIUM",
            claim="人物关系错误",
            reason="陈默和苏瑶关系比对不一致",
            suggested_fix="修正描述"
        )
    ]
    
    score = score_report(report=report, review_issues=issues)
    # consistency_score = 100.0 - 40.0 (character_inconsistency) - 30.0 (wrong_relation) = 30.0
    assert score.consistency_score == 30.0

def test_empty_risk_points_and_high_severity_review():
    # 风险点为空，或包含高危质检错误
    report = {
        "project_id": "proj-risk",
        "title": "风险测试",
        "executive_summary": "测试大纲内容",
        "character_score": 3,
        "plot_logic_score": 3,
        "conflict_density_score": 3,
        "market_fit_score": 3,
        "decision_suggestion": "PASS",
        "improvement_suggestions": ["合理的长于十个字符修改建议！"],
        "risk_points": [], # 为空
        "evidence_list": [{"source_title": "对标作品A"}]
    }
    
    score_empty = score_report(report=report)
    assert score_empty.risk_coverage_score == 20.0  # 100.0 - 80.0
    
    issues = [ReviewIssue(issue_type="high_risk", severity="HIGH", claim="安全红线违规", reason="包含涉密内容", suggested_fix="删除敏感内容")]
    score_high = score_report(report=report, review_issues=issues)
    assert score_high.risk_coverage_score == 0.0  # 100.0 - 80.0 - 20.0 = 0.0
