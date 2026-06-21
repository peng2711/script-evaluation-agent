import pytest
from unittest.mock import MagicMock
from app.workflow.graph import ScriptEvaluationWorkflow
import app.workflow.graph as graph_module
from app.schemas.script import ScriptInput
from app.schemas.report import ReviewIssue, ReviewDecision, FinalReport
from app.schemas.agent_state import AgentState

def create_test_script():
    return ScriptInput(
        project_id="test-reflection-wf-project",
        title="测试反射工作流剧本",
        raw_text="林晚和沈知行的契约婚姻，女主林晚为了查清父亲死亡真相复仇。",
        genre="都市",
        target_audience="都市剧观众",
        user_preferences=[]
    )

def test_workflow_reflection_retrieve_more_routing():
    """
    测试 retrieve_more 路由：ReviewNode -> RetrievalNode，并增加重试次数
    """
    script = create_test_script()
    original_review_agent = graph_module.review_agent
    
    mock_review_agent = MagicMock()
    first_call = True
    
    def mock_execute(state: AgentState) -> AgentState:
        nonlocal first_call
        if first_call:
            state.review_decision = ReviewDecision(
                passed=False,
                issues=[ReviewIssue(
                    issue_type="unsupported_claim",
                    severity="HIGH",
                    claim="缺少论据",
                    reason="无对标作品",
                    suggested_fix="请补充对标作品"
                )],
                action="retrieve_more",
                reason="故意触发 retrieve_more"
            )
            first_call = False
        else:
            state.review_decision = ReviewDecision(
                passed=True,
                issues=[],
                action="pass",
                reason="第二轮通过"
            )
            state.final_report = state.draft_report
        return state

    mock_review_agent.execute = MagicMock(side_effect=mock_execute)
    
    try:
        graph_module.review_agent = mock_review_agent
        wf = ScriptEvaluationWorkflow(max_iterations=2)
        _, state = wf.run_with_state(script)
        
        # 验证轨迹中的节点顺序，第一轮 ReviewNode 后应当回到 RetrievalNode
        traces = state.node_traces
        node_names = [t.node_name for t in traces]
        
        # 找出 ReviewNode 在轨迹中的索引
        review_indices = [i for i, name in enumerate(node_names) if name == "ReviewNode"]
        assert len(review_indices) == 2
        
        # 第一次 ReviewNode (retry=0) 后面应该是 RetrievalNode (retry=1)
        assert node_names[review_indices[0] + 1] == "RetrievalNode"
        assert traces[review_indices[0] + 1].retry_count == 1
        
        # 验证 Trace 中记录了正确的 review_action, review_reason, target_node
        review_trace = traces[review_indices[0]]
        assert review_trace.review_action == "retrieve_more"
        assert review_trace.review_reason == "故意触发 retrieve_more"
        assert review_trace.target_node == "RetrievalNode"
        assert review_trace.retry_count == 0
        
    finally:
        graph_module.review_agent = original_review_agent

def test_workflow_reflection_human_check_routing():
    """
    测试 human_check 路由：ReviewNode -> ReportNode，并且报告中包含“建议人工复核”
    """
    script = create_test_script()
    original_review_agent = graph_module.review_agent
    
    mock_review_agent = MagicMock()
    
    def mock_execute(state: AgentState) -> AgentState:
        state.review_decision = ReviewDecision(
            passed=False,
            issues=[ReviewIssue(
                issue_type="high_risk",
                severity="HIGH",
                claim="敏感题材",
                reason="包含敏感词",
                suggested_fix="转交人工"
            )],
            action="human_check",
            reason="故意触发 human_check"
        )
        return state

    mock_review_agent.execute = MagicMock(side_effect=mock_execute)
    
    try:
        graph_module.review_agent = mock_review_agent
        wf = ScriptEvaluationWorkflow(max_iterations=2)
        report, state = wf.run_with_state(script)
        
        # ReviewNode 后面直接是 ReportNode
        traces = state.node_traces
        node_names = [t.node_name for t in traces]
        review_idx = node_names.index("ReviewNode")
        assert node_names[review_idx + 1] == "ReportNode"
        
        # 报告应标记 "建议人工复核" 且 decision_suggestion = "HUMAN_CHECK"
        assert report is not None
        assert report.decision_suggestion == "HUMAN_CHECK"
        assert report.executive_summary.startswith("【建议人工复核】")
        
        # 验证 Trace
        review_trace = traces[review_idx]
        assert review_trace.review_action == "human_check"
        assert review_trace.review_reason == "故意触发 human_check"
        assert review_trace.target_node == "ReportNode"
        
    finally:
        graph_module.review_agent = original_review_agent

def test_workflow_reflection_max_iterations():
    """
    测试当多次打回超过最大重试次数时，不会无限循环，而是强制进入 ReportNode
    """
    script = create_test_script()
    original_review_agent = graph_module.review_agent
    
    mock_review_agent = MagicMock()
    
    def mock_execute(state: AgentState) -> AgentState:
        # 始终返回 rewrite_analysis，故意制造死循环
        state.review_decision = ReviewDecision(
            passed=False,
            issues=[ReviewIssue(
                issue_type="weak_suggestion",
                severity="MEDIUM",
                claim="建议太空泛",
                reason="没有具体行动指南",
                suggested_fix="补充细节"
            )],
            action="rewrite_analysis",
            reason="故意制造死循环"
        )
        return state

    mock_review_agent.execute = MagicMock(side_effect=mock_execute)
    
    try:
        graph_module.review_agent = mock_review_agent
        # 限制最大重试次数为 2
        wf = ScriptEvaluationWorkflow(max_iterations=2)
        _, state = wf.run_with_state(script)
        
        traces = state.node_traces
        node_names = [t.node_name for t in traces]
        
        review_traces = [t for t in traces if t.node_name == "ReviewNode"]
        
        # 第一次主线：ReviewNode (retry=0)
        # 第二次重试：ReviewNode (retry=1)
        # 第三次重试：ReviewNode (retry=2)
        # 达到最大次数 2，强制转入 ReportNode
        assert len(review_traces) == 3
        assert review_traces[-1].retry_count == 2
        
        # 最后一个节点应该是 ReportNode
        assert node_names[-1] == "ReportNode"
        
    finally:
        graph_module.review_agent = original_review_agent
