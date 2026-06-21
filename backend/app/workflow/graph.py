from ..schemas.script import ScriptInput
from ..schemas.agent_state import AgentState
from ..schemas.report import FinalReport
from ..agents.parser_agent import parser_agent
from ..agents.retrieval_agent import retrieval_agent
from ..agents.analysis_agent import analysis_agent
from ..agents.review_agent import review_agent
from ..memory.project_memory import global_project_memory
import datetime

class ScriptEvaluationWorkflow:
    """
    剧本评估 Multi-Agent 工作流协调器。
    串联：Parser -> Retrieval -> Analysis -> Review (修正自环) -> FinalReport
    """
    def __init__(self, max_iterations: int = 2):
        self.max_iterations = max_iterations

    def run(self, script: ScriptInput) -> FinalReport:
        # 1. 初始化状态
        state = AgentState(script=script)
        state.history_logs.append(f"[{datetime.datetime.now().isoformat()}] 启动剧本评估工作流，标题: '{script.title}'")

        # 2. 节点1：解析角色和剧情事件
        state = parser_agent.execute(state)

        # 3. 节点2：检索同类参考依据 (RAG)
        state = retrieval_agent.execute(state)

        # 4. 节点3 & 4：分析打分与审核修正循环
        while state.iterations <= self.max_iterations:
            # 运行分析打分 Agent
            state = analysis_agent.execute(state)
            # 运行质检 Review Agent
            state = review_agent.execute(state)
            
            # 如果审查通过，或者达到了最大迭代次数，就跳出循环
            if state.final_report is not None:
                break
                
            state.iterations += 1
            state.history_logs.append(
                f"[{datetime.datetime.now().isoformat()}] 报告未通过质检。启动第 {state.iterations} 次优化修正迭代。"
            )

        # 5. 提取最终评估报告
        final_report = state.final_report or state.draft_report
        
        # 6. 将最终决策归档至全局项目记忆中 (Project Memory)
        if final_report:
            global_project_memory.add_evaluation_record(
                project_title=script.title,
                project_id=final_report.project_id,
                decision=final_report.decision_suggestion,
                executive_summary=final_report.executive_summary
            )
            # 新增：按 project_id 进行整个 FinalReport 对象的归档保存
            global_project_memory.add_project_report(
                project_id=final_report.project_id,
                report=final_report
            )

        return final_report

# 全局工作流执行器
evaluation_workflow = ScriptEvaluationWorkflow()
