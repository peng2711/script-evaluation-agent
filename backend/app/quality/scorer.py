from typing import Dict, Any, List, Optional
from .schemas import ReportQualityScore

def get_value(obj: Any, key: str, default: Any = None) -> Any:
    """
    通用属性获取助手，兼容字典与对象。
    """
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)

def score_report(
    report: Any,
    review_issues: Optional[List[Any]] = None,
    evidence_list: Optional[List[Any]] = None,
    trace: Optional[Dict[str, Any]] = None
) -> ReportQualityScore:
    """
    对剧本评估报告进行规则化质量评分。
    """
    reasons = []

    # 1. 解析 Report 结构
    if report is None:
        return ReportQualityScore(
            evidence_score=0.0,
            structure_score=0.0,
            actionable_score=0.0,
            consistency_score=0.0,
            risk_coverage_score=0.0,
            final_score=0.0,
            reasons=["报告对象为空"]
        )

    if hasattr(report, "model_dump"):
        report_dict = report.model_dump()
    elif hasattr(report, "__dict__"):
        report_dict = report.__dict__
    elif isinstance(report, dict):
        report_dict = report
    else:
        report_dict = {}

    # 兼容 review_issues 与 evidence_list 的传入
    if review_issues is None:
        review_issues = report_dict.get("review_issues", []) or []
    if evidence_list is None:
        evidence_list = report_dict.get("evidence_list", []) or []

    # --- 评分维度 1: 证据充分性 evidence_score (权重 0.3) ---
    evidence_score = 100.0
    if not evidence_list:
        evidence_score -= 50.0
        reasons.append("证据充分性: evidence_list 为空，扣除 50.0 分。")
    
    unsupported_claims_count = sum(
        1 for issue in review_issues if get_value(issue, "issue_type") == "unsupported_claim"
    )
    if unsupported_claims_count > 0:
        deducted = min(40.0, unsupported_claims_count * 20.0)
        evidence_score -= deducted
        reasons.append(f"证据充分性: 检测到无支持依据的评价 (unsupported_claim) {unsupported_claims_count} 处，扣除 {deducted} 分。")
    evidence_score = max(0.0, min(100.0, evidence_score))

    # --- 评分维度 2: 报告结构完整度 structure_score (权重 0.2) ---
    structure_score = 100.0
    core_fields = [
        "project_id", "title", "executive_summary", "decision_suggestion",
        "character_score", "plot_logic_score", "conflict_density_score", "market_fit_score"
    ]
    for field in core_fields:
        val = report_dict.get(field)
        # 针对字符串判断非空，针对数字判断合法范围
        is_empty = False
        if val is None:
            is_empty = True
        elif isinstance(val, str) and not val.strip():
            is_empty = True
        elif isinstance(val, (int, float)) and val <= 0:
            is_empty = True

        if is_empty:
            structure_score -= 15.0
            reasons.append(f"报告结构: 缺少核心字段或该字段内容非法 '{field}'，扣除 15.0 分。")
    structure_score = max(0.0, min(100.0, structure_score))

    # --- 评分维度 3: 建议可执行性 actionable_score (权重 0.2) ---
    actionable_score = 100.0
    suggestions = report_dict.get("improvement_suggestions", []) or []
    if not suggestions:
        actionable_score -= 60.0
        reasons.append("建议可执行性: improvement_suggestions 为空，扣除 60.0 分。")
    else:
        short_suggestions_count = sum(1 for s in suggestions if len(str(s).strip()) < 10)
        if short_suggestions_count > 0:
            deducted = min(30.0, short_suggestions_count * 15.0)
            actionable_score -= deducted
            reasons.append(f"建议可执行性: 存在过于空泛或极短的修改建议共 {short_suggestions_count} 条，扣除 {deducted} 分。")

    has_weak_suggestion = any(
        get_value(issue, "issue_type") == "weak_suggestion" for issue in review_issues
    )
    if has_weak_suggestion:
        actionable_score -= 20.0
        reasons.append("建议可执行性: 质检复核存在空泛口号型建议 (weak_suggestion)，扣除 20.0 分。")
    actionable_score = max(0.0, min(100.0, actionable_score))

    # --- 评分维度 4: 人物和剧情一致性 consistency_score (权重 0.2) ---
    consistency_score = 100.0
    has_character_inconsistency = any(
        get_value(issue, "issue_type") == "character_inconsistency" for issue in review_issues
    )
    if has_character_inconsistency:
        consistency_score -= 40.0
        reasons.append("一致性评估: 质检复核发现人物人设冲突风险 (character_inconsistency)，扣除 40.0 分。")

    mismatch_issues = sum(
        1 for issue in review_issues 
        if get_value(issue, "issue_type") in ("wrong_relation", "hallucinated_event")
    )
    if mismatch_issues > 0:
        deducted = min(60.0, mismatch_issues * 30.0)
        consistency_score -= deducted
        reasons.append(f"一致性评估: 质检复核发现人设关系或剧情事实幻觉缺陷 {mismatch_issues} 处，扣除 {deducted} 分。")
    consistency_score = max(0.0, min(100.0, consistency_score))

    # --- 评分维度 5: 风险覆盖度 risk_coverage_score (权重 0.1) ---
    risk_coverage_score = 100.0
    risk_points = report_dict.get("risk_points", []) or []
    if not risk_points:
        risk_coverage_score -= 80.0
        reasons.append("风险覆盖度: risk_points 风险评估列表为空，扣除 80.0 分。")

    has_high_risk = any(
        get_value(issue, "issue_type") == "high_risk" or get_value(issue, "severity") == "HIGH" 
        for issue in review_issues
    )
    if has_high_risk:
        risk_coverage_score -= 20.0
        reasons.append("风险覆盖度: 质检拦截发现未妥善声明的潜在高风险或安全红线缺陷，扣除 20.0 分。")
    risk_coverage_score = max(0.0, min(100.0, risk_coverage_score))

    # --- 综合得分计算 ---
    final_score = (
        0.3 * evidence_score +
        0.2 * structure_score +
        0.2 * actionable_score +
        0.2 * consistency_score +
        0.1 * risk_coverage_score
    )
    final_score = max(0.0, min(100.0, final_score))

    return ReportQualityScore(
        evidence_score=evidence_score,
        structure_score=structure_score,
        actionable_score=actionable_score,
        consistency_score=consistency_score,
        risk_coverage_score=risk_coverage_score,
        final_score=final_score,
        reasons=reasons
    )
