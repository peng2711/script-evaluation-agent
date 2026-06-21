import os
import json
import argparse
import time
import re
from typing import Dict, Any, List, Tuple
from ..schemas.script import ScriptInput
from ..schemas.report import FinalReport, ScriptAnalysis, ReviewIssue, RetrievalEvidence, NodeTrace
from ..schemas.agent_state import AgentState
from ..agents.parser_agent import parser_agent
from ..agents.retrieval_agent import retrieval_agent
from ..agents.analysis_agent import analysis_agent
from ..agents.review_agent import review_agent
from ..workflow.graph import ScriptEvaluationWorkflow, inject_errors_into_state

def run_single_prompt_baseline(script: ScriptInput, injected_errors: List[str] = None) -> Tuple[FinalReport, AgentState]:
    """
    单 Prompt 直出方案：只执行 ParserAgent 事实解析与 AnalysisAgent 直接打分，无 RAG 增补与 Review 质检自环。
    """
    state = AgentState(script=script)
    state.use_tools_via_router = False
    state.injected_errors = injected_errors or []
    
    state = parser_agent.execute(state)
    state = analysis_agent.execute(state)
    
    # 模拟在 iterations == 0 时注入错误（用于 Review 测试检测）
    if state.injected_errors:
        inject_errors_into_state(state, state.injected_errors)
        
    final_report = state.draft_report
    state.final_report = final_report
    
    # 记录 mock trace
    state.node_traces.append(NodeTrace(
        node_name="ParserNode",
        input_summary=f"Script: {script.title}",
        output_summary="Baseline Parser execution",
        retry_count=0
    ))
    state.node_traces.append(NodeTrace(
        node_name="AnalysisNode",
        input_summary=f"Script: {script.title}",
        output_summary="Baseline Analysis execution",
        retry_count=0
    ))
    return final_report, state

def run_fixed_workflow(script: ScriptInput, injected_errors: List[str] = None) -> Tuple[FinalReport, AgentState]:
    """
    固定顺序工作流方案：ParserNode -> RetrievalNode -> AnalysisNode 顺序执行，无 Review 质检自环纠错。
    """
    state = AgentState(script=script)
    state.use_tools_via_router = False
    state.injected_errors = injected_errors or []
    
    state = parser_agent.execute(state)
    state = retrieval_agent.execute(state)
    state = analysis_agent.execute(state)
    
    # 模拟在 iterations == 0 时注入错误（用于 Review 测试检测）
    if state.injected_errors:
        inject_errors_into_state(state, state.injected_errors)
        
    final_report = state.draft_report
    state.final_report = final_report
    
    state.node_traces.append(NodeTrace(
        node_name="ParserNode",
        input_summary=f"Script: {script.title}",
        output_summary="Fixed Parser execution",
        retry_count=0
    ))
    state.node_traces.append(NodeTrace(
        node_name="RetrievalNode",
        input_summary=f"Script: {script.title}",
        output_summary="Fixed Retrieval execution",
        retry_count=0
    ))
    state.node_traces.append(NodeTrace(
        node_name="AnalysisNode",
        input_summary=f"Script: {script.title}",
        output_summary="Fixed Analysis execution",
        retry_count=0
    ))
    return final_report, state

def run_hybrid_workflow(script: ScriptInput, injected_errors: List[str] = None) -> Tuple[FinalReport, AgentState]:
    """
    Hybrid Agent 工作流方案：调用完整的协调工作流，但不通过 ToolRouter 基建。
    """
    wf = ScriptEvaluationWorkflow(max_iterations=2, use_tools_via_router=False)
    state = AgentState(script=script)
    state.injected_errors = injected_errors or []
    final_report, state = wf.run_with_state(script)
    return final_report, state

def run_hybrid_workflow_with_tools(script: ScriptInput, injected_errors: List[str] = None) -> Tuple[FinalReport, AgentState]:
    """
    Hybrid Agent 工作流 + ToolRouter 方案：调用完整工作流，且所有操作皆通过 ToolRouter 路由鉴权。
    """
    wf = ScriptEvaluationWorkflow(max_iterations=2, use_tools_via_router=True)
    state = AgentState(script=script)
    state.injected_errors = injected_errors or []
    final_report, state = wf.run_with_state(script)
    return final_report, state

def jaccard_similarity(set_a: set, set_b: set) -> float:
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    intersection = set_a.intersection(set_b)
    union = set_a.union(set_b)
    return len(intersection) / len(union)

def calculate_conflict_accuracy(extracted: str, gold: str) -> float:
    set_ext = {c for c in extracted if c.strip()}
    set_gold = {c for c in gold if c.strip()}
    return jaccard_similarity(set_ext, set_gold)

def evaluate_metrics(runs: List[Tuple[FinalReport, AgentState]], samples: List[Dict[str, Any]]) -> Dict[str, float]:
    total = len(samples)
    if total == 0:
        return {}
        
    json_success_count = 0
    char_acc_sum = 0.0
    conflict_acc_sum = 0.0
    evidence_precision_sum = 0.0
    unsupported_count = 0
    workflow_success_count = 0
    
    total_injected_errors = 0
    detected_injected_errors = 0
    
    total_latency = 0.0
    total_tool_calls = 0
    total_fallback_calls = 0
    
    for idx, (report, state) in enumerate(runs):
        sample = samples[idx]
        
        # 1. json_success_rate
        if report and isinstance(report, FinalReport):
            try:
                json.loads(report.model_dump_json())
                json_success_count += 1
            except Exception:
                pass
                
        # 2. character_extraction_accuracy
        extracted_chars = set()
        if state.analysis and state.analysis.characters:
            extracted_chars = {c.name for c in state.analysis.characters}
        gold_chars = set(sample.get("gold_characters", []))
        char_acc_sum += jaccard_similarity(extracted_chars, gold_chars)
        
        # 3. core_conflict_accuracy
        extracted_conflict = state.analysis.core_conflict if (state.analysis and state.analysis.core_conflict) else ""
        gold_conflict = sample.get("gold_core_conflict", "")
        conflict_acc_sum += calculate_conflict_accuracy(extracted_conflict, gold_conflict)
        
        # 4. evidence_precision
        gold_evidences = sample.get("expected_evidence_keywords", [])
        if not gold_evidences:
            evidence_precision_sum += 1.0
        else:
            ref_titles = [ev.source_title for ev in report.evidence_list] if report else []
            match_count = sum(1 for kw in gold_evidences if any(kw in title for title in ref_titles))
            evidence_precision_sum += (match_count / len(gold_evidences))
            
        # 5. unsupported_claim_rate
        if report and state.analysis:
            issues = review_agent.review(
                script_title=state.script.title,
                script_genre=state.script.genre,
                raw_text=state.script.raw_text,
                analysis=state.analysis,
                project_id=state.script.project_id,
                evidences=state.evidences,
                draft_report=report,
                use_tools_via_router=state.use_tools_via_router
            )
            has_unsupported = any(i.issue_type == "unsupported_claim" for i in issues)
            if has_unsupported:
                unsupported_count += 1
                
        # 6. review_issue_detection_rate
        injected = sample.get("injected_errors", [])
        if injected:
            total_injected_errors += len(injected)
            # Check review issues detected in state or final report
            detected_types = {i.issue_type for i in state.review_issues}
            detected_injected_errors += sum(1 for err in injected if err in detected_types)
            
        # 7. workflow_success_rate
        has_error = any(t.errors is not None for t in state.node_traces)
        if not has_error and len(state.node_traces) > 0:
            workflow_success_count += 1
            
        # 8/9/10. Tool Calls, Latency, Fallback
        if state.trace and "events" in state.trace:
            events = state.trace["events"]
            calls = [e for e in events if e.get("tool_name") is not None and e.get("status") != "START"]
            total_tool_calls += len(calls)
            total_fallback_calls += sum(1 for e in calls if e.get("status") == "FALLBACK")
            
            metrics = state.trace.get("metrics", {})
            total_latency += metrics.get("total_latency_ms", 0.0)
        else:
            # Check metrics key directly if trace metrics are available
            total_latency += state.trace.get("metrics", {}).get("total_latency_ms", 0.0) if state.trace else 0.0
            
    avg_tool_calls = total_tool_calls / total
    fallback_rate = (total_fallback_calls / total_tool_calls) if total_tool_calls > 0 else 0.0
    review_issue_detection_rate = (detected_injected_errors / total_injected_errors) if total_injected_errors > 0 else 1.0
    
    return {
        "json_success_rate": json_success_count / total,
        "character_extraction_accuracy": char_acc_sum / total,
        "core_conflict_accuracy": conflict_acc_sum / total,
        "evidence_precision": evidence_precision_sum / total,
        "unsupported_claim_rate": unsupported_count / total,
        "review_issue_detection_rate": review_issue_detection_rate,
        "workflow_success_rate": workflow_success_count / total,
        "avg_tool_calls": avg_tool_calls,
        "avg_latency_ms": total_latency / total,
        "fallback_rate": fallback_rate
    }

def print_markdown_table(metrics: Dict[str, Dict[str, float]], to_file_path: str = None) -> str:
    lines = []
    lines.append("\n### 剧本评估方案指标对比评估报告\n")
    lines.append("> [!NOTE]\n> 当前系统采用 Mock LLM 进行评估，以下评测结果主要用于流程与结构验证，非模型实际推理能力上限限制。\n")
    lines.append("| 评估指标 | 1. single_prompt_baseline | 2. fixed_workflow | 3. hybrid_workflow | 4. hybrid_workflow_with_tools |")
    lines.append("| :--- | :---: | :---: | :---: | :---: |")
    
    indicator_names = {
        "json_success_rate": "JSON 成功率 (json_success_rate)",
        "character_extraction_accuracy": "人物提取准确率 (character_extraction_accuracy)",
        "core_conflict_accuracy": "核心冲突准确率 (core_conflict_accuracy)",
        "evidence_precision": "证据引用准确率 (evidence_precision)",
        "unsupported_claim_rate": "无依据评价比例 (unsupported_claim_rate)",
        "review_issue_detection_rate": "质检缺陷检出率 (review_issue_detection_rate)",
        "workflow_success_rate": "工作流完成率 (workflow_success_rate)",
        "avg_tool_calls": "平均工具调用次数 (avg_tool_calls)",
        "avg_latency_ms": "平均执行延迟/毫秒 (avg_latency_ms)",
        "fallback_rate": "工具降级率 (fallback_rate)"
    }
    
    for key, name in indicator_names.items():
        val_baseline = f"{metrics['single_prompt'][key]:.2%}" if key != "avg_tool_calls" and key != "avg_latency_ms" else f"{metrics['single_prompt'][key]:.2f}"
        val_fixed = f"{metrics['fixed'][key]:.2%}" if key != "avg_tool_calls" and key != "avg_latency_ms" else f"{metrics['fixed'][key]:.2f}"
        val_hybrid = f"{metrics['hybrid'][key]:.2%}" if key != "avg_tool_calls" and key != "avg_latency_ms" else f"{metrics['hybrid'][key]:.2f}"
        val_hybrid_tools = f"{metrics['hybrid_with_tools'][key]:.2%}" if key != "avg_tool_calls" and key != "avg_latency_ms" else f"{metrics['hybrid_with_tools'][key]:.2f}"
        
        # avg_latency_ms format suffix
        if key == "avg_latency_ms":
            val_baseline += " ms"
            val_fixed += " ms"
            val_hybrid += " ms"
            val_hybrid_tools += " ms"
            
        lines.append(f"| {name} | {val_baseline} | {val_fixed} | {val_hybrid} | {val_hybrid_tools} |")
        
    lines.append("\n说明：所有评估数据指标均由基准测试用例 (`benchmark.json`) 严格计算所得。")
    
    report_content = "\n".join(lines)
    print(report_content)
    
    if to_file_path:
        with open(to_file_path, "w", encoding="utf-8") as f:
            f.write("# 剧本评估离线评测报告\n\n" + report_content)
            
    return report_content

def run_evaluation_for_mode(mode: str, samples: List[Dict[str, Any]]) -> List[Tuple[FinalReport, AgentState]]:
    runs = []
    for sample in samples:
        script_input = ScriptInput(
            project_id=sample["project_id"],
            title=sample["title"],
            raw_text=sample["raw_text"],
            genre=sample["genre"],
            target_audience=sample["target_audience"],
            user_preferences=sample["user_preferences"]
        )
        injected = sample.get("injected_errors", [])
        
        start_time = time.perf_counter()
        
        if mode == "single_prompt":
            report, state = run_single_prompt_baseline(script_input, injected)
        elif mode == "fixed":
            report, state = run_fixed_workflow(script_input, injected)
        elif mode == "hybrid":
            report, state = run_hybrid_workflow(script_input, injected)
        elif mode == "hybrid_with_tools":
            report, state = run_hybrid_workflow_with_tools(script_input, injected)
        else:
            raise ValueError(f"Unknown mode: {mode}")
            
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        
        # Populate latency
        if not state.trace:
            state.trace = {"metrics": {"total_latency_ms": elapsed_ms}}
        else:
            state.trace.setdefault("metrics", {})["total_latency_ms"] = elapsed_ms
            
        runs.append((report, state))
        
    return runs

def main_compare():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    benchmark_path = os.path.join(current_dir, "benchmark.json")
    
    if not os.path.exists(benchmark_path):
        print(f"Error: 找不到评测基准文件 {benchmark_path}")
        return
        
    with open(benchmark_path, "r", encoding="utf-8") as f:
        samples = json.load(f)
        
    print("正在对比各模式性能，请稍候...")
    
    metrics_summary = {}
    
    # Run all 4 modes
    for mode in ["single_prompt", "fixed", "hybrid", "hybrid_with_tools"]:
        runs = run_evaluation_for_mode(mode, samples)
        metrics_summary[mode] = evaluate_metrics(runs, samples)
        
    # Output to eval_results.json
    output_json_path = os.path.join(current_dir, "eval_results.json")
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(metrics_summary, f, ensure_ascii=False, indent=2)
    print(f"\n[评估完毕] 全量指标比对结果已保存至 {output_json_path}")
    
    # Output to eval_report.md
    output_md_path = os.path.join(current_dir, "eval_report.md")
    print_markdown_table(metrics_summary, to_file_path=output_md_path)
    print(f"[评估完毕] 全量指标比对报告已保存至 {output_md_path}")

def main():
    parser = argparse.ArgumentParser(description="面向内容立项决策的剧本评估系统指标评测")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["single_prompt", "fixed", "hybrid", "hybrid_with_tools"],
        default=None,
        help="指定单独运行评估的模式，不传默认运行全量对比并渲染对比报表"
    )
    args = parser.parse_args()
    
    if args.mode is None:
        main_compare()
        return
        
    current_dir = os.path.dirname(os.path.abspath(__file__))
    benchmark_path = os.path.join(current_dir, "benchmark.json")
    
    if not os.path.exists(benchmark_path):
        print(f"Error: 找不到评测基准文件 {benchmark_path}")
        return
        
    with open(benchmark_path, "r", encoding="utf-8") as f:
        samples = json.load(f)
        
    print(f"正在运行模式: {args.mode}")
    runs = run_evaluation_for_mode(args.mode, samples)
    mode_metrics = evaluate_metrics(runs, samples)
    
    print(json.dumps(mode_metrics, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
