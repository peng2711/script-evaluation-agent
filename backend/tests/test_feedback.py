import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.feedback.schemas import FeedbackInput
from app.feedback.store import global_feedback_store

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_feedback_store():
    global_feedback_store.clear()
    yield
    global_feedback_store.clear()

def test_feedback_store_save_and_load():
    fb = FeedbackInput(
        project_id="test-proj-1",
        report_id="test-rep-1",
        trace_id="test-tr-1",
        helpful=True,
        evidence_accurate=True,
        suggestion_actionable=True,
        wrong_claims=[],
        user_comment="非常棒的报告"
    )
    global_feedback_store.save_feedback(fb)
    
    loaded = global_feedback_store.load_feedback_by_project("test-proj-1")
    assert len(loaded) == 1
    assert loaded[0].user_comment == "非常棒的报告"
    
    all_fb = global_feedback_store.list_all_feedback()
    assert len(all_fb) == 1

def test_feedback_api():
    # 1. 提交正常反馈 (不触发 failure case)
    payload = {
        "project_id": "test-proj-api",
        "report_id": "test-rep-api",
        "trace_id": "test-tr-api",
        "helpful": True,
        "evidence_accurate": True,
        "suggestion_actionable": True,
        "wrong_claims": [],
        "user_comment": "有用！"
    }
    response = client.post("/feedback", json=payload)
    assert response.status_code == 200
    assert response.json()["failure_case_created"] is False
    
    # 2. 查询项目反馈
    response = client.get("/feedback/test-proj-api")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["user_comment"] == "有用！"
