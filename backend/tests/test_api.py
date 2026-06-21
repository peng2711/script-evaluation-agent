from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_evaluate_endpoint_with_valid_payload():
    payload = {
        "project_id": "proj-999",
        "title": "测试剧本之夜",
        "raw_text": "这是一部关于黑客与特工的故事，里面包含林啸和赵乾，背景是一次破晓行动。",
        "genre": "悬疑",
        "target_audience": "男性动作片受众",
        "user_preferences": ["偏好紧凑"]
    }
    
    response = client.post("/evaluate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "project_id" in data
    assert data["project_id"] == "proj-999"
    assert data["title"] == "测试剧本之夜"
    
    # 验证评分字段格式及值在 1-5 之间
    assert "character_score" in data
    assert 1 <= data["character_score"] <= 5
    assert 1 <= data["plot_logic_score"] <= 5
    assert 1 <= data["conflict_density_score"] <= 5
    assert 1 <= data["market_fit_score"] <= 5
    
    # 验证证据列表结构
    assert "evidence_list" in data
    assert len(data["evidence_list"]) > 0
    assert "source_title" in data["evidence_list"][0]
    
    # 验证决策类型
    assert data["decision_suggestion"] in ["PASS", "REVISE", "REJECT"]

def test_evaluate_endpoint_validation_error():
    # 故意提交缺失必填字段 project_id 的载荷
    payload = {
        "title": "无ID的剧本",
        "raw_text": "内容说明"
    }
    
    response = client.post("/evaluate", json=payload)
    assert response.status_code == 422  # Pydantic 校验失败返回 422 Unprocessable Entity
