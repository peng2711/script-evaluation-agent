from ..schemas.script import ScriptInput
from ..schemas.agent_state import AgentState, NodeTrace
from ..schemas.report import FinalReport
from ..agents.parser_agent import parser_agent
from ..agents.retrieval_agent import retrieval_agent
from ..agents.analysis_agent import analysis_agent
from ..agents.review_agent import review_agent
from ..memory.project_memory import global_project_memory
from ..memory.character_memory import global_character_memory
import datetime
from typing import Tuple

class ScriptEvaluationWorkflow:
    """
    剧本评估 Hybrid Agent 工作流协调器。
    外层使用确定性 workflow，内层在 Retrieval 和 Review 阶段进行局部自环纠错，
    并在全流程自动收集可观测性 Trace 和 Metrics。
    """
    def __init__(self, max_iterations: int = 2):
        self.max_iterations = max_iterations

    def run(self, script: ScriptInput) -> FinalReport:
        report, state = self.run_with_state(script)
        if report:
            report.node_traces = state.node_traces
            if state.analysis:
                report.risk_points = state.analysis.risk_points
                report.strengths = state.analysis.strengths
                report.weaknesses = state.analysis.weaknesses
                report.characters = state.analysis.characters
                report.character_relations = state.analysis.character_relations
                report.core_conflict = state.analysis.core_conflict
            # 注入可观测性链路数据
            report.trace = state.trace
        return report

    def run_with_state(self, script: ScriptInput) -> Tuple[FinalReport, AgentState]:
        import uuid
        from ..observability.trace import TraceRecorder, active_trace_recorder
        from ..observability.metrics import calculate_metrics

        # 1. 启动全局可观测性链路记录器
        trace_id = f"tr-{uuid.uuid4().hex[:8]}"
        recorder = TraceRecorder(trace_id=trace_id)
        token = active_trace_recorder.set(recorder)

        # 2. 初始化状态
        state = AgentState(script=script)
        state.history_logs.append(f"[{datetime.datetime.now().isoformat()}] 启动剧本评估工作流，标题: '{script.title}'")

        current_node = "ParserNode"
        retry_count = 0
        workflow_success = True

        while current_node != "End":
            try:
                state, err_msg = self._execute_node(current_node, state, retry_count)
                if err_msg:
                    workflow_success = False
            except Exception as e:
                workflow_success = False
                state.history_logs.append(f"[{datetime.datetime.now().isoformat()}] 节点 {current_node} 执行时抛出异常: {str(e)}")
            
            # 路由到下一个节点
            next_node, next_retry = self._get_next_node(current_node, state, retry_count)
            current_node = next_node
            retry_count = next_retry

        # 3. 最终归档到项目记忆中
        final_report = state.final_report or state.draft_report
        if final_report:
            global_project_memory.save_project(script.project_id, final_report)

        # 4. 统计并导出可观测性指标，存入 state.trace
        exported_events = recorder.export_trace()
        metrics = calculate_metrics(exported_events, workflow_success=workflow_success)
        state.trace = {
            "events": [event.model_dump() for event in exported_events],
            "metrics": metrics.model_dump()
        }

        # 5. 销毁上下文
        active_trace_recorder.reset(token)

        return final_report, state

    def _execute_node(self, node_name: str, state: AgentState, retry_count: int) -> Tuple[AgentState, str]:
        import time
        from ..observability.trace import active_trace_recorder
        
        state.iterations = retry_count
        err_msg = None
        input_summary = ""
        output_summary = ""

        # 获取当前节点的 Agent 映射名称
        agent_mapping = {
            "ParserNode": "ParserAgent",
            "MemoryNode": "Workflow",
            "AnalysisNode": "AnalysisAgent",
            "RetrievalNode": "RetrievalAgent",
            "ReviewNode": "ReviewAgent",
            "ReportNode": "Workflow"
        }
        agent_name = agent_mapping.get(node_name, "Workflow")

        # 1. 整理简短输入摘要（不超过 150 字符）
        if node_name == "ParserNode":
            input_summary = f"Title: '{state.script.title}', Raw Text Length: {len(state.script.raw_text)}"
        elif node_name == "MemoryNode":
            input_summary = f"Project ID: '{state.script.project_id}'"
        elif node_name == "AnalysisNode":
            input_summary = f"Script Title: '{state.script.title}', evidences count: {len(state.evidences)}"
        elif node_name == "RetrievalNode":
            input_summary = f"Script Title: '{state.script.title}', Genre: '{state.script.genre}'"
        elif node_name == "ReviewNode":
            input_summary = f"Draft report decision: {state.draft_report.decision_suggestion if state.draft_report else 'N/A'}"
        elif node_name == "ReportNode":
            input_summary = f"Draft report decision: {state.draft_report.decision_suggestion if state.draft_report else 'N/A'}"

        recorder = active_trace_recorder.get()
        if recorder:
            recorder.record_node_start(node_name, agent_name, input_summary, retry_count)

        start_t = time.perf_counter()

        try:
            if node_name == "ParserNode":
                state = parser_agent.execute(state)
                output_summary = f"Parsed characters: {[c.name for c in state.analysis.characters] if state.analysis else []}"
                
            elif node_name == "MemoryNode":
                if state.analysis and state.analysis.characters:
                    global_character_memory.save_characters(state.script.project_id, state.analysis.characters)
                output_summary = f"Saved characters in memory for project '{state.script.project_id}'"
                
            elif node_name == "AnalysisNode":
                state = analysis_agent.execute(state)
                output_summary = (
                    f"Draft report score: char={state.draft_report.character_score if state.draft_report else 'N/A'}, "
                    f"plot={state.draft_report.plot_logic_score if state.draft_report else 'N/A'}, "
                    f"decision={state.draft_report.decision_suggestion if state.draft_report else 'N/A'}"
                )
                
            elif node_name == "RetrievalNode":
                state = retrieval_agent.execute(state)
                output_summary = f"Retrieved {len(state.evidences)} evidences: {[ev.source_title for ev in state.evidences]}"
                
            elif node_name == "ReviewNode":
                state = review_agent.execute(state)
                output_summary = (
                    f"Found {len(state.review_issues)} review issues. "
                    f"should_retrieve_more={state.should_retrieve_more}, "
                    f"should_rewrite_report={state.should_rewrite_report}"
                )
                
            elif node_name == "ReportNode":
                state.final_report = state.draft_report
                output_summary = f"Locked final report with decision: {state.final_report.decision_suggestion if state.final_report else 'N/A'}"

            duration = (time.perf_counter() - start_t) * 1000.0
            if recorder:
                recorder.record_node_end(node_name, agent_name, output_summary, "SUCCESS", duration)
                
        except Exception as e:
            err_msg = str(e)
            if recorder:
                recorder.record_error(node_name, agent_name, err_msg)
            raise e
        finally:
            trace = NodeTrace(
                node_name=node_name,
                input_summary=input_summary,
                output_summary=output_summary,
                errors=err_msg,
                retry_count=retry_count
            )
            state.node_traces.append(trace)
            
        return state, err_msg

    def _get_next_node(self, current_node: str, state: AgentState, retry_count: int) -> Tuple[str, int]:
        if current_node == "ParserNode":
            return "MemoryNode", retry_count
        elif current_node == "MemoryNode":
            return "AnalysisNode", retry_count
        elif current_node == "AnalysisNode":
            # 首次运行或者未运行过检索时，接下来运行检索以遵循固定流程
            has_retrieval = any(trace.node_name == "RetrievalNode" for trace in state.node_traces)
            if not has_retrieval:
                return "RetrievalNode", retry_count
            else:
                # 重新修正后直接返回质检节点检查
                return "ReviewNode", retry_count
        elif current_node == "RetrievalNode":
            # 首次运行或者未运行过质检时，接下来按照外层流程直接运行质检
            has_review = any(trace.node_name == "ReviewNode" for trace in state.node_traces)
            if not has_review:
                return "ReviewNode", retry_count
            else:
                # 打回补充检索证据后，需回到分析节点重新打分写草稿
                return "AnalysisNode", retry_count
        elif current_node == "ReviewNode":
            # 存在质检项，且重试未达最大次数
            if (state.should_rewrite_report or state.should_retrieve_more) and retry_count < self.max_iterations:
                next_retry = retry_count + 1
                if state.should_retrieve_more:
                    state.history_logs.append(
                        f"[{datetime.datetime.now().isoformat()}] 质检第 {next_retry} 次未通过：需要补充获取证据。回滚至 RetrievalNode。"
                    )
                    return "RetrievalNode", next_retry
                else:
                    state.history_logs.append(
                        f"[{datetime.datetime.now().isoformat()}] 质检第 {next_retry} 次未通过：需要重新分析报告。回滚至 AnalysisNode。"
                    )
                    return "AnalysisNode", next_retry
            else:
                # 无问题，或已达最大重试限制
                return "ReportNode", retry_count
        elif current_node == "ReportNode":
            return "End", retry_count
            
        return "End", retry_count

# 全局工作流执行器
evaluation_workflow = ScriptEvaluationWorkflow()
