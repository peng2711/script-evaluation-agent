import pytest
from app.eval.run_eval import (
    jaccard_similarity,
    calculate_conflict_accuracy,
    evaluate_metrics
)
from app.schemas.script import ScriptInput
from app.schemas.report import FinalReport, ScriptAnalysis, RetrievalEvidence, CharacterProfile, ReviewIssue
from app.schemas.agent_state import AgentState, NodeTrace

def test_jaccard_similarity_empty():
    assert jaccard_similarity(set(), set()) == 1.0
    assert jaccard_similarity(set(), {"A"}) == 0.0
    assert jaccard_similarity({"A"}, set()) == 0.0

def test_jaccard_similarity_overlap():
    # overlap: A, B vs B, C -> intersection: B (1), union: A, B, C (3) -> Jaccard = 1/3
    assert jaccard_similarity({"A", "B"}, {"B", "C"}) == 1 / 3
    assert jaccard_similarity({"A"}, {"A"}) == 1.0

def test_conflict_accuracy_chars():
    c1 = "特工林啸与赵乾生死博弈"
    c2 = "林啸与赵乾生死博弈"
    # Char overlap: c1 has 11 chars (特,工,林,啸,与,赵,乾,生,死,博,弈)
    # c2 has 9 chars (林,啸,与,赵,乾,生,死,博,弈)
    # intersection has 9 chars, union has 11 chars. Jaccard similarity = 9 / 11.
    acc = calculate_conflict_accuracy(c1, c2)
    assert abs(acc - 9 / 11) < 1e-5

def test_evaluate_metrics_full():
    samples = [
        {
            "gold_characters": ["林啸", "赵乾"],
            "gold_core_conflict": "林啸对垒赵乾",
            "expected_evidence_keywords": ["流浪地球"],
            "injected_errors": ["weak_suggestion"]
        }
    ]
    
    script = ScriptInput(
        project_id="test-eval-metrics",
        title="测试剧本",
        raw_text="林啸对垒赵乾",
        genre="悬疑",
        target_audience="硬核观众",
        user_preferences=[]
    )
    analysis = ScriptAnalysis(
        characters=[
            CharacterProfile(
                name="林啸", role="特工", personality=[], motivation="", relationships={}, constraints=[], evidence_spans=[]
            )
        ],
        character_relations=[],
        core_conflict="林啸对垒赵乾",
        plot_events=[],
        risk_points=[],
        strengths=[],
        weaknesses=[]
    )
    report = FinalReport(
        project_id="test-eval-metrics",
        title="测试剧本",
        executive_summary="对标引用《流浪地球》证据，说明情况。",
        character_score=4,
        plot_logic_score=4,
        conflict_density_score=4,
        market_fit_score=4,
        evidence_list=[
            RetrievalEvidence(
                source_title="流浪地球", source_type="电影", content="", relevance_reason="", score=0.9
            )
        ],
        review_issues=[],
        decision_suggestion="PASS",
        improvement_suggestions=[]
    )
    
    state = AgentState(script=script, analysis=analysis, draft_report=report, final_report=report, evidences=report.evidence_list)
    state.node_traces.append(NodeTrace(node_name="ParserNode", input_summary="", output_summary="", retry_count=0))
    state.node_traces.append(NodeTrace(node_name="ReviewNode", input_summary="", output_summary="", retry_count=0))
    
    # 模拟 Review Agent 检出了错误，放入 state.review_issues 中以测试 review_issue_detection_rate
    state.review_issues = [
        ReviewIssue(
            issue_type="weak_suggestion",
            severity="MEDIUM",
            claim="直接开机",
            reason="太空泛",
            suggested_fix="具体化"
        )
    ]
    
    runs = [(report, state)]
    metrics = evaluate_metrics(runs, samples)
    
    assert metrics["json_success_rate"] == 1.0
    assert metrics["character_extraction_accuracy"] == 0.5  # ['林啸'] vs ['林啸', '赵乾']
    assert metrics["core_conflict_accuracy"] == 1.0
    assert metrics["evidence_precision"] == 1.0
    assert metrics["workflow_success_rate"] == 1.0
    assert metrics["review_issue_detection_rate"] == 1.0
    assert metrics["unsupported_claim_rate"] == 0.0  # mock review has no unsupported_claim issue
