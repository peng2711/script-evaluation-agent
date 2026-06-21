from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_evaluate_endpoint_with_valid_payload():
    payload = {
        "title": "测试剧本之夜",
        "content": "这是一部关于黑客与特工的故事，里面包含林啸和赵乾，背景是一次破晓行动。",
        "author": "编剧李四",
        "genre": "悬疑"
    }
    
    response = client.post("/evaluate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "script_id" in data
    assert data["title"] == "测试剧本之夜"
    assert data["genre"] == "悬疑"
    
    # 验证是否正确触发了针对林啸、赵乾特工的 mock 抽取
    assert len(data["characters"]) > 0
    names = [char["name"] for char in data["characters"]]
    assert "林啸" in names
    assert "赵乾" in names
    
    # 验证 RAG 检索到的参考作品是否包含
    assert len(data["references"]) > 0
    assert data["references"][0]["title"] == "隐秘的角落"
    
    # 验证最终立项建议结论格式
    assert data["conclusion"] in ["PASS", "REVISE", "REJECT"]
    
    # 验证是否通过了 Review 质检（林啸在第二轮修正中会通过审查变成 True）
    assert data["review"]["is_passed"] is True
    assert len(data["review"]["findings"]) == 0

def test_evaluate_endpoint_validation_error():
    # 故意提交缺失必填字段 content 的载荷
    payload = {
        "title": "无内容的剧本",
        "genre": "科幻"
    }
    
    response = client.post("/evaluate", json=payload)
    assert response.status_code == 422  # Pydantic 校验失败返回 422 Unprocessable Entity
