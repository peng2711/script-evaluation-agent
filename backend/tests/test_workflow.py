import pytest
from unittest.mock import MagicMock
from app.workflow.graph import ScriptEvaluationWorkflow, evaluation_workflow
import app.workflow.graph as graph_module
from app.schemas.script import ScriptInput
from app.schemas.report import ReviewIssue, FinalReport
from app.schemas.agent_state import AgentState

def create_test_script():
    return ScriptInput(
        project_id="test-wf-project",
        title="测试工作流剧本",
        raw_text="林晚和沈知行的契约婚姻，女主林晚为了查清父亲死亡真相复仇。",
        genre="都市",
        target_audience="都市剧观众",
        user_preferences=[]
    )

def test_workflow_deterministic_flow_sequence():
    """
    1. 验证外层确定性执行流程：
       首个生命周期严格按照 ParserNode -> MemoryNode -> AnalysisNode -> RetrievalNode -> ReviewNode 的顺序走完。
    """
    script = create_test_script()
    
    # 运行工作流并收集状态
    _, state = evaluation_workflow.run_with_state(script)
    
    traces = state.node_traces
    assert len(traces) >= 5
    
    # 检查前五个节点名，必须严格对应外层流程顺序
    expected_sequence = ["ParserNode", "MemoryNode", "AnalysisNode", "RetrievalNode", "ReviewNode"]
    actual_sequence = [t.node_name for t in traces[:5]]
    assert actual_sequence == expected_sequence

def test_workflow_inner_correction_loop():
    """
    2. 验证当 ReviewNode 发现问题时能够打回到 RetrievalNode 或 AnalysisNode
    """
    script = create_test_script()
    
    # 我们知道 "林晚和沈知行" 题材在 iterations == 0 时，由 AnalysisAgent 故意产生未修正版（立项决策为 PASS，但有漏洞和空泛建议 "直接开机"），
    # 这会触发 ReviewAgent 检出问题并设置 should_rewrite_report = True，从而回滚。
    _, state = evaluation_workflow.run_with_state(script)
    
    traces = state.node_traces
    node_names = [t.node_name for t in traces]
    
    # 验证轨迹中存在自环行为
    # 首次执行：Parser -> Memory -> Analysis -> Retrieval -> Review
    # 由于 ReviewNode 发现问题（未通过），接下来应打回 AnalysisNode
    # 打回后：Analysis -> Review -> Report
    assert "ReviewNode" in node_names
    # 检查 ReviewNode 执行后，后面是否跟着 AnalysisNode 或 RetrievalNode 进行了修正
    review_indices = [i for i, name in enumerate(node_names) if name == "ReviewNode"]
    assert len(review_indices) > 0
    
    # 只要有一次未通过，下一次执行的节点应该是 RetrievalNode 或 AnalysisNode
    first_review_idx = review_indices[0]
    assert first_review_idx + 1 < len(node_names)
    assert node_names[first_review_idx + 1] in ["RetrievalNode", "AnalysisNode"]

def test_workflow_retry_limit():
    """
    3. 验证最大重试次数为 2 限制，防止无限循环
    """
    script = create_test_script()
    
    # 模拟一个总是认为报告有问题的 ReviewAgent，强制 should_rewrite_report = True
    original_review_agent = graph_module.review_agent
    
    mock_review_agent = MagicMock()
    def mock_execute(state: AgentState) -> AgentState:
        # 始终反馈有严重问题需要重写
        state.should_rewrite_report = True
        state.should_retrieve_more = False
        state.review_issues = [
            ReviewIssue(
                issue_type="unsupported_claim",
                severity="HIGH",
                claim="始终有问题",
                reason="Mock 强力拦截",
                suggested_fix="无法修复"
            )
        ]
        if state.draft_report:
            state.draft_report.review_issues = state.review_issues
        return state

    mock_review_agent.execute = MagicMock(side_effect=mock_execute)
    
    try:
        # 猴子补丁替换全局 review_agent
        graph_module.review_agent = mock_review_agent
        
        # 实例化一个限制 max_iterations = 2 的工作流
        wf = ScriptEvaluationWorkflow(max_iterations=2)
        _, state = wf.run_with_state(script)
        
        traces = state.node_traces
        review_traces = [t for t in traces if t.node_name == "ReviewNode"]
        
        # 第一次主线 ReviewNode (retry=0)
        # 第二次重试 ReviewNode (retry=1)
        # 第三次重试 ReviewNode (retry=2)
        # 然后退出，执行 ReportNode，所以 ReviewNode 最多被执行 3 次
        assert len(review_traces) <= 3
        
        # 验证最后一个 ReviewNode 的 retry_count 是 2
        assert review_traces[-1].retry_count == 2
        
        # 确认最终到达了 ReportNode 并没有无限循环
        assert traces[-1].node_name in ["ReportNode", "End"]
        
    finally:
        # 恢复现场
        graph_module.review_agent = original_review_agent

def test_workflow_trace_contents():
    """
    4. 验证各个节点记录的 Trace 内容完整性
    """
    script = create_test_script()
    _, state = evaluation_workflow.run_with_state(script)
    
    traces = state.node_traces
    assert len(traces) > 0
    
    for trace in traces:
        assert trace.node_name in ["ParserNode", "MemoryNode", "AnalysisNode", "RetrievalNode", "ReviewNode", "ReportNode"]
        assert isinstance(trace.input_summary, str)
        assert isinstance(trace.output_summary, str)
        # 检查重试计数合法性
        assert 0 <= trace.retry_count <= 2
        # input_summary 和 output_summary 在正常执行下应有记录
        assert len(trace.input_summary) > 0
        assert len(trace.output_summary) > 0
