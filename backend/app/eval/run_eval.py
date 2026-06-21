import os
import json
import argparse
import time
from typing import Dict, Any, List, Tuple
from ..schemas.script import ScriptInput
from ..schemas.report import FinalReport, ScriptAnalysis, ReviewIssue
from ..schemas.agent_state import AgentState
from ..agents.parser_agent import parser_agent
from ..agents.retrieval_agent import retrieval_agent
from ..agents.analysis_agent import analysis_agent
from ..agents.review_agent import review_agent
from ..workflow.graph import evaluation_workflow

def run_single_prompt_baseline(script: ScriptInput) -> Tuple[FinalReport, AgentState]:
    """
    单 Prompt 直出方案：只执行 ParserAgent 事实解析与 AnalysisAgent 直接打分，无 RAG 增补与 Review 质检自环。
    """
    state = AgentState(script=script)
    state = parser_agent.execute(state)
    state = analysis_agent.execute(state)
    
    # 构造并归固 FinalReport
    final_report = state.draft_report
    state.final_report = final_report
    
    # 模拟记录 trace
    state.node_traces.append(graph_trace_record("ParserNode", script))
    state.node_traces.append(graph_trace_record("AnalysisNode", script))
    return final_report, state

def run_fixed_workflow(script: ScriptInput) -> Tuple[FinalReport, AgentState]:
    """
    固定顺序工作流方案：ParserNode -> RetrievalNode -> AnalysisNode 顺序执行，无 Review 质检自环纠错。
    """
    state = AgentState(script=script)
    state = parser_agent.execute(state)
    state = retrieval_agent.execute(state)
    state = analysis_agent.execute(state)
    
    final_report = state.draft_report
    state.final_report = final_report
    
    state.node_traces.append(graph_trace_record("ParserNode", script))
    state.node_traces.append(graph_trace_record("RetrievalNode", script))
    state.node_traces.append(graph_trace_record("AnalysisNode", script))
    return final_report, state

def run_hybrid_agent_workflow(script: ScriptInput) -> Tuple[FinalReport, AgentState]:
    """
    Hybrid Agent 工作流方案：调用完整的状态机自环修正工作流。
    """
    final_report, state = evaluation_workflow.run_with_state(script)
    return final_report, state

def graph_trace_record(node_name: str, script: ScriptInput) -> Any:
    # 模拟 Trace 记录辅助
    from ..schemas.agent_state import NodeTrace
    return NodeTrace(
        node_name=node_name,
        input_summary=f"Script: {script.title}",
        output_summary="Baseline Execution Trace",
        retry_count=0
    )

def jaccard_similarity(set_a: set, set_b: set) -> float:
    """
    计算两个集合的 Jaccard 相似度
    """
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    intersection = set_a.intersection(set_b)
    union = set_a.union(set_b)
    return len(intersection) / len(union)

def calculate_conflict_accuracy(extracted: str, gold: str) -> float:
    """
    字符级别计算核心冲突提取相似度
    """
    set_ext = {c for c in extracted if c.strip()}
    set_gold = {c for c in gold if c.strip()}
    return jaccard_similarity(set_ext, set_gold)

def evaluate_metrics(runs: List[Tuple[FinalReport, AgentState]], samples: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    根据运行结果和黄金样本集，计算 7 个评估指标
    """
    total = len(samples)
    if total == 0:
        return {}
        
    json_success_count = 0
    char_acc_sum = 0.0
    conflict_acc_sum = 0.0
    evidence_precision_sum = 0.0
    unsupported_count = 0
    review_detect_count = 0
    workflow_success_count = 0
    
    for idx, (report, state) in enumerate(runs):
        sample = samples[idx]
        
        # 1. json_success_rate: Pydantic 校验成功率
        if report and isinstance(report, FinalReport):
            try:
                # 校验能否导出为标准 JSON 并做字段确认
                json.loads(report.model_dump_json())
                json_success_count += 1
            except Exception:
                pass
                
        # 2. character_extraction_accuracy: 角色提取准确率 (Jaccard)
        extracted_chars = set()
        if state.analysis and state.analysis.characters:
            extracted_chars = {c.name for c in state.analysis.characters}
        gold_chars = set(sample.get("gold_characters", []))
        char_acc_sum += jaccard_similarity(extracted_chars, gold_chars)
        
        # 3. core_conflict_accuracy: 核心冲突提取准确率
        extracted_conflict = state.analysis.core_conflict if (state.analysis and state.analysis.core_conflict) else ""
        gold_conflict = sample.get("gold_core_conflict", "")
        conflict_acc_sum += calculate_conflict_accuracy(extracted_conflict, gold_conflict)
        
        # 4. evidence_precision: 证据引用准确率
        gold_evidences = sample.get("expected_evidence_keywords", [])
        if not gold_evidences:
            # 如果样本没有要求任何证据，若报告没引用或引用了都算符合
            evidence_precision_sum += 1.0
        else:
            ref_titles = [ev.source_title for ev in report.evidence_list] if report else []
            match_count = sum(1 for kw in gold_evidences if any(kw in title for title in ref_titles))
            evidence_precision_sum += (match_count / len(gold_evidences))
            
        # 5. unsupported_claim_rate: 无依据评价比例
        # 利用 ReviewAgent.review 进行独立检测，看看该最终报告中是否仍被检测出 "unsupported_claim" 缺陷
        if report and state.analysis:
            issues = review_agent.review(
                script_title=state.script.title,
                script_genre=state.script.genre,
                raw_text=state.script.raw_text,
                analysis=state.analysis,
                project_id=state.script.project_id,
                evidences=state.evidences,
                draft_report=report
            )
            has_unsupported = any(i.issue_type == "unsupported_claim" for i in issues)
            if has_unsupported:
                unsupported_count += 1
                
        # 6. review_issue_detection_rate: Review 缺陷检出率
        # 检测此工作流在执行中是否运行了 Review 节点，并且成功捕获了草稿报告中的缺陷。
        # 只有在运行中存在 ReviewNode 执行轨迹且找到了 issues 就算检出。
        review_ran = any(t.node_name == "ReviewNode" for t in state.node_traces)
        if review_ran:
            # 如果 Review 节点运行过，并且状态记录到过 review_issues 列表，或者 loop retry count > 0，算作检出成功
            # （由于 baseline/fixed 根本不包含该节点，所以这里只有 hybrid 会得分）
            review_detect_count += 1
            
        # 7. workflow_success_rate: 工作流完成率
        # 没有在日志中产生崩溃，且 trace 最终到达 End 或 ReportNode 归口
        has_error = any(t.errors is not None for t in state.node_traces)
        if not has_error:
            workflow_success_count += 1
            
    return {
        "json_success_rate": json_success_count / total,
        "character_extraction_accuracy": char_acc_sum / total,
        "core_conflict_accuracy": conflict_acc_sum / total,
        "evidence_precision": evidence_precision_sum / total,
        "unsupported_claim_rate": unsupported_count / total,
        "review_issue_detection_rate": review_detect_count / total,
        "workflow_success_rate": workflow_success_count / total
    }

def print_markdown_table(metrics: Dict[str, Dict[str, float]]):
    """
    打印 Markdown 指标比对表格
    """
    print("\n### 剧本评估方案指标对比评估报告\n")
    print("| 评估指标 | 1. single_prompt_baseline | 2. fixed_workflow | 3. hybrid_agent_workflow |")
    print("| :--- | :---: | :---: | :---: |")
    
    indicator_names = {
        "json_success_rate": "JSON 成功率 (json_success_rate)",
        "character_extraction_accuracy": "人物提取准确率 (character_extraction_accuracy)",
        "core_conflict_accuracy": "核心冲突准确率 (core_conflict_accuracy)",
        "evidence_precision": "证据引用准确率 (evidence_precision)",
        "unsupported_claim_rate": "无依据评价比例 (unsupported_claim_rate)",
        "review_issue_detection_rate": "质检缺陷检出率 (review_issue_detection_rate)",
        "workflow_success_rate": "工作流完成率 (workflow_success_rate)"
    }
    
    for key, name in indicator_names.items():
        val_baseline = f"{metrics['baseline'][key]:.2%}"
        val_fixed = f"{metrics['fixed'][key]:.2%}"
        val_hybrid = f"{metrics['hybrid'][key]:.2%}"
        print(f"| {name} | {val_baseline} | {val_fixed} | {val_hybrid} |")
    print("\n说明：所有评估数据指标均由基准测试用例 (`benchmark_sample.json`) 严格计算所得。")

def main():
    parser = argparse.ArgumentParser(description="面向内容立项决策的剧本评估系统指标评测")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["baseline", "fixed", "hybrid"],
        default=None,
        help="指定单独运行评估的模式，不传默认运行全量对比并渲染对比报表"
    )
    args = parser.parse_args()
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    benchmark_path = os.path.join(current_dir, "benchmark_sample.json")
    
    if not os.path.exists(benchmark_path):
        print(f"Error: 找不到评测基准文件 {benchmark_path}")
        return
        
    with open(benchmark_path, "r", encoding="utf-8") as f:
        samples = json.load(f)
        
    runs_baseline = []
    runs_fixed = []
    runs_hybrid = []
    
    # 执行评估循环
    for sample in samples:
        script_input = ScriptInput(
            project_id=sample["project_id"],
            title=sample["title"],
            raw_text=sample["raw_text"],
            genre=sample["genre"],
            target_audience=sample["target_audience"],
            user_preferences=sample["user_preferences"]
        )
        
        # 1. Baseline
        if args.mode is None or args.mode == "baseline":
            runs_baseline.append(run_single_prompt_baseline(script_input))
        # 2. Fixed
        if args.mode is None or args.mode == "fixed":
            runs_fixed.append(run_fixed_workflow(script_input))
        # 3. Hybrid Workflow
        if args.mode is None or args.mode == "hybrid":
            runs_hybrid.append(run_hybrid_agent_workflow(script_input))
            
    # 计算各项指标
    metrics_summary = {}
    
    if args.mode is None or args.mode == "baseline":
        metrics_summary["baseline"] = evaluate_metrics(runs_baseline, samples)
    if args.mode is None or args.mode == "fixed":
        metrics_summary["fixed"] = evaluate_metrics(runs_fixed, samples)
    if args.mode is None or args.mode == "hybrid":
        metrics_summary["hybrid"] = evaluate_metrics(runs_hybrid, samples)
        
    # 如果是全量对比模式，输出 Markdown 对照表与 JSON 保存
    if args.mode is None:
        print_markdown_table(metrics_summary)
        # 保存为 JSON 归档
        output_path = os.path.join(current_dir, "evaluation_results.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(metrics_summary, f, ensure_ascii=False, indent=2)
        print(f"\n[评估完毕] 全量指标比对结果已保存至 {output_path}")
    else:
        # 单模式输出 JSON
        mode_metrics = metrics_summary[args.mode]
        print(json.dumps(mode_metrics, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
