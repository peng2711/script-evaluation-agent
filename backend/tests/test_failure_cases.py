import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.failure.schemas import FailureCase
from app.failure.case_store import global_failure_case_store
from app.feedback.schemas import FeedbackInput
from app.feedback.collector import global_feedback_collector
from app.memory.project_memory import global_project_memory
from app.schemas.script import ScriptInput
from app.workflow.graph import evaluation_workflow

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_stores():
    global_failure_case_store.clear()
    yield
    global_failure_case_store.clear()

def test_failure_case_store_operations():
    case = FailureCase(
        case_id="fc-test-1",
        project_id="proj-test-1",
        trace_id="tr-test-1",
        failure_type="PROCESS_FAILED",
        failed_node="AnalysisNode",
        failed_tool="memory_read_tool",
        review_issues=["[HIGH] character_inconsistency: 人设冲突"],
        bad_output_summary="草稿报告摘要",
        root_cause="工具读取记忆崩溃",
        suggested_fix="修复 memory_read_tool 的 allowed_agents 权限"
    )
    global_failure_case_store.save_failure_case(case)
    
    loaded = global_failure_case_store.load_failure_case("fc-test-1")
    assert loaded is not None
    assert loaded.failure_type == "PROCESS_FAILED"
    assert loaded.failed_node == "AnalysisNode"
    
    cases = global_failure_case_store.list_failure_cases()
    assert len(cases) == 1

def test_feedback_triggers_failure_case_due_to_unhelpful():
    # 模拟项目评估报告已保存到项目记忆库
    report_data = {
        "project_id": "proj-unhelpful",
        "title": "测试剧本",
        "executive_summary": "评估大纲内容",
        "character_score": 3,
        "plot_logic_score": 3,
        "conflict_density_score": 3,
        "market_fit_score": 3,
        "evidence_list": [],
        "review_issues": [],
        "decision_suggestion": "PASS",
        "improvement_suggestions": [],
        "trace": {"events": [], "metrics": {}}
    }
    global_project_memory.save_project("proj-unhelpful", report_data)
    
    fb = FeedbackInput(
        project_id="proj-unhelpful",
        report_id="proj-unhelpful",
        trace_id="tr-unhelpful",
        helpful=False, # 触发判定
        evidence_accurate=True,
        suggestion_actionable=True,
        wrong_claims=[],
        user_comment="不太好"
    )
    
    case = global_feedback_collector.collect_feedback(fb)
    assert case is not None
    assert "USER_UNHELPFUL" in case.failure_type
    assert case.project_id == "proj-unhelpful"
    
    # 验证 API 列表与获取
    response = client.get("/failure-cases")
    assert response.status_code == 200
    assert len(response.json()) == 1
    
    response = client.get(f"/failure-cases/{case.case_id}")
    assert response.status_code == 200
    assert response.json()["project_id"] == "proj-unhelpful"

def test_failure_case_replaying():
    # 1. 运行一次完整的评估工作流，使其保存 ScriptInput 和 FinalReport
    script_input = ScriptInput(
        project_id="proj-replay-test",
        title="林晚复仇记",
        raw_text="女主林晚，男主沈知行，契约婚姻复仇。",
        genre="都市",
        target_audience="大众"
    )
    # 运行 workflow
    report = evaluation_workflow.run(script_input)
    assert report is not None
    
    # 2. 模拟用户提交 unhelpful=False 触发失败案例
    trace_id = "some-trace"
    if report.trace and report.trace.get("events"):
        trace_id = report.trace.get("events")[0].get("trace_id")
        
    fb = FeedbackInput(
        project_id="proj-replay-test",
        report_id="proj-replay-test",
        trace_id=trace_id,
        helpful=False,
        evidence_accurate=True,
        suggestion_actionable=True,
        wrong_claims=[],
        user_comment="重放测试反馈"
    )
    
    case = global_feedback_collector.collect_feedback(fb)
    assert case is not None
    
    # 3. 运行重放，检查是否重跑生成 FinalReport
    replayed_report = global_failure_case_store.replay_failure_case(case.case_id)
    assert replayed_report is not None
    assert replayed_report.title == "林晚复仇记"
    assert replayed_report.character_score >= 1
