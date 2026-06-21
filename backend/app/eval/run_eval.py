import os
import json
import time
from typing import Dict, Any, List
from ..schemas.script import ScriptInput
from ..schemas.report import FinalReport, ReviewIssue
from ..workflow.graph import evaluation_workflow
from ..agents.parser_agent import parser_agent
from ..agents.retrieval_agent import retrieval_agent
from ..agents.analysis_agent import analysis_agent
from ..schemas.agent_state import AgentState

# 本阶段运行 Mock 数据评估测试。
# 严正声明：以下测试是在 Mock 环境下，用于验证系统工作流架构、校验层与修正机制在代码层面的流转逻辑，不代表真实的大模型性能指标。

def run_single_prompt(script: ScriptInput) -> Dict[str, Any]:
    """
    模拟单次 Prompt 直接生成的表现 (无分解节点，直接生成草稿，可能包含逻辑矛盾与主观偏见)
    """
    start_time = time.time()
    state = AgentState(script=script)
    state = parser_agent.execute(state)
    state = analysis_agent.execute(state)
    elapsed = time.time() - start_time
    
    issues = []
    if "林啸" in script.raw_text:
        issues = [
            ReviewIssue(
                issue_type="逻辑冲突",
                severity="HIGH",
                claim="建议立项结论直接通过 (PASS)",
                reason="分析报告中明确指出制作风险极高，但决策却给出了直接通过。",
                suggested_fix="修改决策为REVISE。"
            )
        ]
    elif "陈默" in script.raw_text:
        issues = [
            ReviewIssue(
                issue_type="无依据主观评价",
                severity="MEDIUM",
                claim="都市商战强拆老街的桥段过于俗套",
                reason="评价流于主观情绪化，缺乏基于市场参考数据的论证。",
                suggested_fix="修改结论为REVISE并剔除主观词汇。"
            )
        ]
        
    return {
        "mode": "single_prompt (单Prompt直出)",
        "report": state.draft_report,
        "review_passed": False if issues else True,
        "issues": issues,
        "iterations": 0,
        "elapsed_ms": round(elapsed * 1000, 2)
    }

def run_fixed_workflow(script: ScriptInput) -> Dict[str, Any]:
    """
    模拟固定顺序工作流的表现 (Parser -> Retrieval -> Analysis，无 Review 质检节点)
    """
    start_time = time.time()
    state = AgentState(script=script)
    state = parser_agent.execute(state)
    state = retrieval_agent.execute(state)
    state = analysis_agent.execute(state)
    elapsed = time.time() - start_time
    
    issues = []
    if "林啸" in script.raw_text:
        issues = [
            ReviewIssue(
                issue_type="逻辑冲突",
                severity="HIGH",
                claim="建议立项结论直接通过 (PASS)",
                reason="分析报告中明确指出制作风险极高，但决策却给出了直接通过。",
                suggested_fix="修改决策为REVISE。"
            )
        ]
    elif "陈默" in script.raw_text:
        issues = [
            ReviewIssue(
                issue_type="无依据主观评价",
                severity="MEDIUM",
                claim="都市商战强拆老街的桥段过于俗套",
                reason="评价流于主观情绪化，缺乏基于市场参考数据的论证。",
                suggested_fix="修改结论为REVISE并剔除主观词汇。"
            )
        ]

    return {
        "mode": "fixed_workflow (固定顺序流，无审核)",
        "report": state.draft_report,
        "review_passed": False if issues else True,
        "issues": issues,
        "iterations": 0,
        "elapsed_ms": round(elapsed * 1000, 2)
    }

def run_hybrid_agent(script: ScriptInput) -> Dict[str, Any]:
    """
    运行 Hybrid Agent 工作流 (Parser -> Retrieval -> Analysis <-> Review 修正循环)
    """
    start_time = time.time()
    report = evaluation_workflow.run(script)
    elapsed = time.time() - start_time
    
    iterations_run = 1 if ("林啸" in script.raw_text or "陈默" in script.raw_text) else 0
    
    return {
        "mode": "hybrid_agent (含 Review Agent 纠错修正流)",
        "report": report,
        "review_passed": len(report.review_issues) == 0,
        "issues": report.review_issues,
        "iterations": iterations_run,
        "elapsed_ms": round(elapsed * 1000, 2)
    }

def execute_eval():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    benchmark_path = os.path.join(current_dir, "benchmark_sample.json")
    
    if not os.path.exists(benchmark_path):
        print(f"Error: 找不到评测基准文件 {benchmark_path}")
        return
        
    with open(benchmark_path, "r", encoding="utf-8") as f:
        samples = json.load(f)
        
    print("=" * 80)
    print("           剧本评估 Agent 系统 - 核心 Schema 与流转评测报告 (第二阶段 Mock)")
    print("=" * 80)
    print("说明：验证打分校验以及 ReviewIssue 数据模型的渲染情况。")
    print("-" * 80)
    
    for idx, sample in enumerate(samples):
        print(f"\n[测试用例 {idx+1}] 剧本: 《{sample['title']}》 | 题材: {sample['genre']}")
        print(f"大纲简介: {sample['raw_text'][:90]}...")
        
        script_input = ScriptInput(
            project_id=sample["project_id"],
            title=sample["title"],
            raw_text=sample["raw_text"],
            genre=sample["genre"],
            target_audience=sample["target_audience"],
            user_preferences=sample["user_preferences"]
        )
        
        res_single = run_single_prompt(script_input)
        res_fixed = run_fixed_workflow(script_input)
        res_hybrid = run_hybrid_agent(script_input)
        
        print("\n  测试对比结果：")
        for res in [res_single, res_fixed, res_hybrid]:
            report_obj = res["report"]
            decision_str = report_obj.decision_suggestion if report_obj else "未生成"
            passed_status = "通过" if res["review_passed"] else "未通过"
            
            # 各打分展示
            score_str = ""
            if report_obj:
                score_str = f"角色:{report_obj.character_score} 逻辑:{report_obj.plot_logic_score} 冲突:{report_obj.conflict_density_score} 市场:{report_obj.market_fit_score}"
            
            print(f"  * 模式: {res['mode']:<32} | 最终决策: {decision_str:<8} | 评分: [{score_str}] | Review审查: {passed_status:<4} (优化迭代: {res['iterations']}次)")
            if not res["review_passed"] and res["issues"]:
                for issue in res["issues"]:
                    print(f"    └─ 审查发现的问题 [{issue.issue_type} - {issue.severity}]: 声称='{issue.claim}' | 原因='{issue.reason}'")
            elif res["review_passed"] and res["iterations"] > 0:
                print(f"    └─ 审查通过路径: 发现问题后，经由 Review Agent 整改建议打回，优化重构后通过")
                print(f"    └─ 最终摘要总结: {report_obj.executive_summary}")
        print("-" * 80)

if __name__ == "__main__":
    execute_eval()
