from ..schemas.script import ScriptSubmission
from ..schemas.agent_state import AgentState
from ..schemas.report import EvaluationReport
from ..agents.parser_agent import parser_agent
from ..agents.retrieval_agent import retrieval_agent
from ..agents.analysis_agent import analysis_agent
from ..agents.review_agent import review_agent
from ..memory.project_memory import global_project_memory
import datetime

class ScriptEvaluationWorkflow:
    """
    剧本评估 Multi-Agent 工作流协调器。
    模拟实现以下拓扑：
    Parser -> Retrieval -> Analysis -> Review -> [未通过：修改循环] -> Final Report
    """
    def __init__(self, max_iterations: int = 2):
        self.max_iterations = max_iterations

    def run(self, script: ScriptSubmission) -> EvaluationReport:
        # 1. 初始化状态
        state = AgentState(script=script)
        state.history_logs.append(f"[{datetime.datetime.now().isoformat()}] 启动剧本评估工作流，标题: '{script.title}'")

        # 2. 节点1：解析角色和剧情事件
        state = parser_agent.execute(state)

        # 3. 节点2：匹配同类作品 (RAG)
        state = retrieval_agent.execute(state)

        # 4. 节点3 & 4：分析报告与审核修正循环 (Analysis <-> Review Loop)
        while state.iterations <= self.max_iterations:
            # 运行分析 Agent
            state = analysis_agent.execute(state)
            # 运行审查 Agent
            state = review_agent.execute(state)
            
            if state.review_result and state.review_result.is_passed:
                break
                
            state.iterations += 1
            state.history_logs.append(
                f"[{datetime.datetime.now().isoformat()}] 报告未通过质检。启动第 {state.iterations} 次优化修正迭代。"
            )

        # 5. 取出最终评估报告（如果达到最大迭代数依然未通过，也强制输出并附加审核提示）
        final_report = state.final_report or state.draft_report
        
        # 6. 将最终决策归档至全局项目记忆中 (Project Memory)
        if final_report:
            global_project_memory.add_evaluation_record(
                project_title=script.title,
                script_id=final_report.script_id,
                conclusion=final_report.conclusion.value,
                summary=final_report.summary
            )

        return final_report

# 实例化全局工作流执行器
evaluation_workflow = ScriptEvaluationWorkflow()
