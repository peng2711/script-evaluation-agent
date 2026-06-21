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

def test_parse_endpoint_success():
    payload = {
        "project_id": "proj-101",
        "title": "破晓行动录",
        "raw_text": "林啸站在废墟中，配合黑客苏晴潜入赵乾的集装箱码头进行破晓行动。",
        "genre": "悬疑",
        "target_audience": "悬疑爱好者",
        "user_preferences": []
    }
    
    response = client.post("/parse", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "characters" in data
    assert "plot_events" in data
    assert "core_conflict" in data
    
    # 验证提取出的角色
    character_names = [char["name"] for char in data["characters"]]
    assert "林啸" in character_names
    assert "苏晴" in character_names
    
    # 验证剧情事件
    assert len(data["plot_events"]) > 0
    assert data["plot_events"][0]["event_id"] == "EVT-001"

def test_get_project_by_id_flow():
    # 1. 产生一个随机的ID提交评估
    project_id = "test-flow-id-123"
    payload = {
        "project_id": project_id,
        "title": "项目-测试茶香",
        "raw_text": "陈默与苏瑶一起反抗李建国强拆茶馆的行为。",
        "genre": "都市",
        "target_audience": "泛大众",
        "user_preferences": []
    }
    
    # 运行评估，这会自动将报告注册进 memory 中
    response_eval = client.post("/evaluate", json=payload)
    assert response_eval.status_code == 200
    
    # 2. 从 GET /projects/{project_id} 中取回它
    response_get = client.get(f"/projects/{project_id}")
    assert response_get.status_code == 200
    
    data = response_get.json()
    assert data["project_id"] == project_id
    assert data["title"] == "项目-测试茶香"
    assert data["decision_suggestion"] == "REVISE"  # 茶香题材在修正后决策为 REVISE

def test_get_project_by_id_404():
    # 请求一个不存在的项目 ID
    response = client.get("/projects/non-existent-project-id-999")
    assert response.status_code == 404
    assert "未找到项目ID" in response.json()["detail"]
