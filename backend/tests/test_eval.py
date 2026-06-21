import pytest
import os
import json
import argparse
from app.eval.run_eval import (
    jaccard_similarity, 
    calculate_conflict_accuracy, 
    evaluate_metrics
)
from app.schemas.script import ScriptInput
from app.schemas.report import FinalReport, ScriptAnalysis, ReviewIssue, CharacterProfile, RetrievalEvidence
from app.schemas.agent_state import AgentState, NodeTrace

def test_benchmark_data_completeness():
    """
    1. 验证评估数据集 benchmark_sample.json 的完备性：包含 10 条样本，且包含所需全部黄金标准字段
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    benchmark_path = os.path.normpath(os.path.join(current_dir, "..", "app", "eval", "benchmark_sample.json"))
    
    assert os.path.exists(benchmark_path), f"Benchmark file does not exist at {benchmark_path}"
    
    with open(benchmark_path, "r", encoding="utf-8") as f:
        samples = json.load(f)
        
    assert len(samples) == 10, f"Expected exactly 10 benchmark samples, got {len(samples)}"
    
    required_keys = [
        "project_id", "title", "genre", "raw_text", "target_audience", 
        "user_preferences", "gold_characters", "gold_core_conflict", 
        "gold_risk_points", "expected_evidence_keywords"
    ]
    
    for idx, sample in enumerate(samples):
        for key in required_keys:
            assert key in sample, f"Sample #{idx} missing required key '{key}'"
        assert isinstance(sample["gold_characters"], list)
        assert isinstance(sample["gold_core_conflict"], str)
        assert isinstance(sample["gold_risk_points"], list)
        assert isinstance(sample["expected_evidence_keywords"], list)

def test_jaccard_similarity_helpers():
    """
    2. 验证 Jaccard 相似度辅助计算函数的边界与正确性
    """
    # 边界情况：空集
    assert jaccard_similarity(set(), set()) == 1.0
    assert jaccard_similarity(set(), {"A"}) == 0.0
    assert jaccard_similarity({"A"}, set()) == 0.0
    
    # 正常计算
    assert jaccard_similarity({"A", "B"}, {"B", "C"}) == 1 / 3
    assert jaccard_similarity({"A", "B"}, {"A", "B"}) == 1.0
    
    # 冲突提取精度（字符级）
    s1 = "特工林啸与赵乾对峙"
    s2 = "林啸与赵乾对峙"
    similarity = calculate_conflict_accuracy(s1, s2)
    # 字符集 s1: 特,工,林,啸,与,赵,乾,对,峙 (9 chars)
    # 字符集 s2: 林,啸,与,赵,乾,对,峙 (7 chars)
    # 重合：林,啸,与,赵,乾,对,峙 (7 chars)
    # 并集：9 chars
    # Jaccard = 7/9
    assert abs(similarity - 7/9) < 1e-5

def test_metrics_evaluation_logic():
    """
    3. 验证 metrics 汇总计算逻辑在模拟状态下的准确性
    """
    # 模拟 1 个样本及运行输出结果
    samples = [{
        "gold_characters": ["林啸", "赵乾"],
        "gold_core_conflict": "林啸对垒赵乾",
        "expected_evidence_keywords": ["流浪地球"]
    }]
    
    script = ScriptInput(
        project_id="test", title="测试", raw_text="林啸对垒赵乾", 
        genre="悬疑", target_audience="受众", user_preferences=[]
    )
    
    analysis = ScriptAnalysis(
        characters=[CharacterProfile(name="林啸", role="特工", personality=[], motivation="", relationships={}, constraints=[], evidence_spans=[])],
        character_relations=[], core_conflict="林啸对垒赵乾", plot_events=[], risk_points=[], strengths=[], weaknesses=[]
    )
    
    report = FinalReport(
        project_id="test", title="测试", executive_summary="报告大纲",
        character_score=4, plot_logic_score=4, conflict_density_score=4, market_fit_score=4,
        evidence_list=[RetrievalEvidence(source_title="流浪地球记", source_type="电影", content="", relevance_reason="", score=0.9)],
        review_issues=[], decision_suggestion="PASS", improvement_suggestions=[]
    )
    
    state = AgentState(script=script, analysis=analysis, draft_report=report, final_report=report)
    # 模拟 trace 表明 review 节点执行过
    state.node_traces.append(NodeTrace(node_name="ReviewNode", input_summary="", output_summary="", retry_count=0))
    
    runs = [(report, state)]
    metrics = evaluate_metrics(runs, samples)
    
    assert metrics["json_success_rate"] == 1.0
    # 提取了 1 个角色 ["林啸"]，黄金角色 ["林啸", "赵乾"] -> Jaccard = 1/2 = 0.5
    assert metrics["character_extraction_accuracy"] == 0.5
    # 冲突一致 -> 1.0
    assert metrics["core_conflict_accuracy"] == 1.0
    # 证据包含 "流浪地球" -> 命中 -> 1.0
    assert metrics["evidence_precision"] == 1.0
    # 无异常完成 -> 1.0
    assert metrics["workflow_success_rate"] == 1.0
    # ReviewNode 运行过 -> 1.0
    assert metrics["review_issue_detection_rate"] == 1.0
