import uuid
from typing import List, Optional
from .schemas import FeedbackInput
from .store import global_feedback_store
from ..failure.schemas import FailureCase
from ..failure.case_store import global_failure_case_store
from ..memory.project_memory import global_project_memory

class FeedbackCollector:
    """
    负责收集并分析用户反馈，根据定义的判定标准自动沉淀失败案例。
    """
    def collect_feedback(self, feedback: FeedbackInput) -> Optional[FailureCase]:
        # 1. 保存反馈
        global_feedback_store.save_feedback(feedback)
        
        # 2. 从项目记忆库加载当时评估的最终报告，提取 Trace 和 Review 异常
        report_dict = global_project_memory.load_project(feedback.project_id)
        
        has_high_review_issue = False
        has_trace_failure = False
        failed_node = None
        failed_tool = None
        review_issues_desc = []
        bad_output_summary = "无相关评估摘要。"
        
        if report_dict:
            # 提取报告摘要作为 bad_output_summary
            bad_output_summary = report_dict.get("executive_summary", "")[:300]
            
            # 提取 Review Agent 检测的错误
            issues = report_dict.get("review_issues", [])
            for issue in issues:
                issue_type = issue.get("issue_type")
                severity = issue.get("severity")
                claim = issue.get("claim")
                reason = issue.get("reason")
                desc = f"[{severity}] {issue_type}: {claim} - 原因: {reason}"
                review_issues_desc.append(desc)
                if severity == "HIGH":
                    has_high_review_issue = True
                    
            # 提取 Trace 中的 FAILED / FALLBACK
            trace = report_dict.get("trace") or {}
            events = trace.get("events", [])
            for event in events:
                status = event.get("status")
                if status in ("FAILED", "FALLBACK"):
                    has_trace_failure = True
                    if event.get("node_name"):
                        failed_node = event.get("node_name")
                    if event.get("tool_name"):
                        failed_tool = event.get("tool_name")
        
        # 3. 判定失败案例的标准
        should_save_case = (
            not feedback.helpful or
            not feedback.evidence_accurate or
            len(feedback.wrong_claims) > 0 or
            has_high_review_issue or
            has_trace_failure
        )
        
        if not should_save_case:
            return None
            
        # 4. 归纳失败类别 (failure_type) 与分析修复方案
        failure_types = []
        root_causes = []
        suggested_fixes = []
        
        if not feedback.helpful:
            failure_types.append("USER_UNHELPFUL")
            root_causes.append("用户反馈评估报告整体‘无用’")
            suggested_fixes.append("重新优化评估打分标准与内容提示词（Prompt）")
            
        if not feedback.evidence_accurate:
            failure_types.append("INACCURATE_EVIDENCE")
            root_causes.append("用户反馈引用的相似作品对标证据‘不准确’")
            suggested_fixes.append("调整 RAG 初筛召回权重及 Reranker 各指标精排比重")
            
        if len(feedback.wrong_claims) > 0:
            failure_types.append("WRONG_CLAIMS")
            root_causes.append(f"用户指出事实错误: {feedback.wrong_claims}")
            suggested_fixes.append("优化 Parser Agent 针对人物角色和剧情主要事件事实抽取的精细度")
            
        if has_high_review_issue:
            failure_types.append("CRITICAL_REVIEW_ISSUE")
            root_causes.append("Review Agent 诊断出严重人设冲突/幻觉/红线质量问题")
            suggested_fixes.append("退回打磨前置节点的输出规则，增强人设及合规拦截")
            
        if has_trace_failure:
            failure_types.append("PROCESS_FAILED_OR_FALLBACK")
            root_causes.append(f"可观测性链路 Trace 检测到节点/工具失败或降级（Node: {failed_node}, Tool: {failed_tool}）")
            suggested_fixes.append("检查工具白名单鉴权配置或工具底层执行接口的稳定性与容错")
            
        failure_type = "+".join(failure_types)
        root_cause = "；".join(root_causes)
        suggested_fix = "；".join(suggested_fixes)
        
        # 5. 构造并保存失败案例
        case_id = f"fc-{uuid.uuid4().hex[:8]}"
        failure_case = FailureCase(
            case_id=case_id,
            project_id=feedback.project_id,
            trace_id=feedback.trace_id,
            failure_type=failure_type,
            failed_node=failed_node,
            failed_tool=failed_tool,
            review_issues=review_issues_desc,
            bad_output_summary=bad_output_summary,
            root_cause=root_cause,
            suggested_fix=suggested_fix
        )
        
        global_failure_case_store.save_failure_case(failure_case)
        return failure_case

global_feedback_collector = FeedbackCollector()
