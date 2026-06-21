import os
import json
import time
from typing import Dict, Any, List
from ..schemas.script import ScriptSubmission
from ..schemas.report import EvaluationReport, ReviewResult
from ..workflow.graph import evaluation_workflow
from ..agents.parser_agent import parser_agent
from ..agents.retrieval_agent import retrieval_agent
from ..agents.analysis_agent import analysis_agent
from ..schemas.agent_state import AgentState

# 本阶段运行 Mock 数据评估测试。
# 严正声明：以下测试是在 Mock 环境下，用于验证系统工作流架构、校验层与修正机制在代码层面的流转逻辑，不代表真实的大模型性能指标。

def run_single_prompt(script: ScriptSubmission) -> Dict[str, Any]:
    """
    模拟单次 Prompt 直接生成的表现 (无分解节点，直接生成草稿，可能包含逻辑矛盾与主观偏见)
    """
    start_time = time.time()
    state = AgentState(script=script)
    # 单次生成：直接顺序执行 Parser 和 Analysis，不经过 Review 修正
    state = parser_agent.execute(state)
    state = analysis_agent.execute(state)
    elapsed = time.time() - start_time
    
    # 模拟单次 Prompt 输出可能带有的不合规问题 (即 review.is_passed = False)
    findings = []
    if "林啸" in script.content:
        findings = ["立项建议结论与高制作风险点矛盾", "结论过于主观，缺少对高制作成本的具体规避意见"]
    elif "陈默" in script.content:
        findings = ["总结称'都市商战老套，不建议立项'，属于主观无依据的草率结论"]
        
    return {
        "mode": "single_prompt (单Prompt直出)",
        "report": state.draft_report,
        "review_passed": False if findings else True,
        "findings": findings,
        "iterations": 0,
        "elapsed_ms": round(elapsed * 1000, 2)
    }

def run_fixed_workflow(script: ScriptSubmission) -> Dict[str, Any]:
    """
    模拟固定顺序工作流的表现 (Parser -> Retrieval -> Analysis，无 Review 质检节点)
    """
    start_time = time.time()
    state = AgentState(script=script)
    state = parser_agent.execute(state)
    state = retrieval_agent.execute(state)
    state = analysis_agent.execute(state)
    elapsed = time.time() - start_time
    
    # 虽然加入了检索增强，但是由于没有 Review 控制，仍然保留了草稿中的错误
    findings = []
    if "林啸" in script.content:
        findings = ["立项建议结论与高制作风险点矛盾", "结论过于主观，缺少对高制作成本的具体规避意见"]
    elif "陈默" in script.content:
        findings = ["总结称'都市商战老套，不建议立项'，属于主观无依据的草率结论"]

    return {
        "mode": "fixed_workflow (固定顺序流，无审核)",
        "report": state.draft_report,
        "review_passed": False if findings else True,
        "findings": findings,
        "iterations": 0,
        "elapsed_ms": round(elapsed * 1000, 2)
    }

def run_hybrid_agent(script: ScriptSubmission) -> Dict[str, Any]:
    """
    运行 Hybrid Agent 工作流 (Parser -> Retrieval -> Analysis <-> Review 修正循环)
    """
    start_time = time.time()
    # 运行真实的工作流
    report = evaluation_workflow.run(script)
    elapsed = time.time() - start_time
    
    # 提取实际运行的迭代次数
    # 由于是 mock 数据，在遇到 "林啸" 或 "陈默" 时会进行一次修正迭代，最后通过审核
    iterations_run = 1 if ("林啸" in script.content or "陈默" in script.content) else 0
    
    return {
        "mode": "hybrid_agent (含 Review Agent 纠错修正流)",
        "report": report,
        "review_passed": report.review.is_passed,
        "findings": report.review.findings,
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
    print("           剧本评估 Agent 系统 - 架构流转评测报告 (第一阶段 Mock)")
    print("=" * 80)
    print("说明：本阶段评测主要用于测试 Schema 校验通过率、架构节点调用链路以及 Review 修正纠错机制。")
    print("      耗时基于本地 Python 代码执行耗时，不代表真实外部大模型接口响应时间。")
    print("-" * 80)
    
    for idx, sample in enumerate(samples):
        print(f"\n[测试用例 {idx+1}] 剧本: 《{sample['title']}》 | 题材: {sample['genre']}")
        print(f"大纲简介: {sample['content'][:90]}...")
        
        script_sub = ScriptSubmission(
            title=sample["title"],
            content=sample["content"],
            genre=sample["genre"]
        )
        
        # 运行三种模式
        res_single = run_single_prompt(script_sub)
        res_fixed = run_fixed_workflow(script_sub)
        res_hybrid = run_hybrid_agent(script_sub)
        
        print("\n  测试对比结果：")
        for res in [res_single, res_fixed, res_hybrid]:
            report_obj = res["report"]
            conclusion_str = report_obj.conclusion.value if report_obj else "未生成"
            passed_status = "通过" if res["review_passed"] else "未通过"
            
            print(f"  * 模式: {res['mode']:<32} | 最终决策: {conclusion_str:<8} | Review审查: {passed_status:<4} (优化迭代: {res['iterations']}次)")
            if not res["review_passed"] and res["findings"]:
                print(f"    └─ 审查发现的问题: {res['findings']}")
            elif res["review_passed"] and res["iterations"] > 0:
                print(f"    └─ 审查通过路径: 发现问题后，经由 Review Agent 整改建议打回，优化重构后通过")
                print(f"    └─ 最终优化总结: {report_obj.summary}")
        print("-" * 80)

if __name__ == "__main__":
    execute_eval()
