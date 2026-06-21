import os
import pytest
from app.memory.project_memory import ProjectMemoryStore
from app.memory.character_memory import CharacterMemoryStore
from app.schemas.report import CharacterProfile

# 测试专用的临时文件路径
TEST_PROJECT_FILE = "storage/test_project_memory.json"
TEST_CHARACTER_FILE = "storage/test_character_memory.json"

@pytest.fixture(autouse=True)
def cleanup_test_files():
    # 测试前清理
    for filepath in [TEST_PROJECT_FILE, TEST_CHARACTER_FILE]:
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass
    yield
    # 测试后清理
    for filepath in [TEST_PROJECT_FILE, TEST_CHARACTER_FILE]:
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass

def test_project_memory_store():
    # 实例化测试用的 Store
    store = ProjectMemoryStore(filepath=TEST_PROJECT_FILE)
    
    project_id = "test-proj-001"
    summary = {
        "project_id": project_id,
        "title": "测试悬疑短剧",
        "executive_summary": "测试内容大纲总结",
        "character_score": 4,
        "plot_logic_score": 3,
        "conflict_density_score": 4,
        "market_fit_score": 3,
        "decision_suggestion": "REVISE"
    }
    
    # 1. 测试读取不存在的项目，应返回 None
    assert store.load_project(project_id) is None
    
    # 2. 测试保存项目
    store.save_project(project_id, summary)
    assert os.path.exists(TEST_PROJECT_FILE) is True
    
    # 3. 测试读取已保存的项目
    loaded = store.load_project(project_id)
    assert loaded is not None
    assert loaded["title"] == "测试悬疑短剧"
    assert loaded["decision_suggestion"] == "REVISE"
    
    # 4. 测试局部更新项目字段
    store.update_project(project_id, {"decision_suggestion": "PASS", "market_fit_score": 5})
    updated = store.load_project(project_id)
    assert updated["decision_suggestion"] == "PASS"
    assert updated["market_fit_score"] == 5
    assert updated["title"] == "测试悬疑短剧"  # 其他字段保持不变
    
    # 5. 测试更新不存在的项目，应抛出 KeyError
    with pytest.raises(KeyError):
        store.update_project("non-existent-id", {"title": "报错"})
        
    # 6. 测试列表项目
    projects_list = store.list_projects()
    assert len(projects_list) == 1
    assert projects_list[0]["project_id"] == project_id

def test_character_memory_store():
    store = CharacterMemoryStore(filepath=TEST_CHARACTER_FILE)
    project_id = "test-proj-002"
    
    char1 = CharacterProfile(
        name="林晚",
        role="女主角",
        personality=["坚韧"],
        motivation="复仇",
        relationships={},
        constraints=[],
        evidence_spans=["林晚出场"]
    )
    char2 = CharacterProfile(
        name="沈知行",
        role="男主角",
        personality=["高冷"],
        motivation="相助",
        relationships={},
        constraints=[],
        evidence_spans=["沈知行出场"]
    )
    
    # 1. 读取不存在项目的角色人设，应返回空列表 []
    assert store.load_characters(project_id) == []
    
    # 2. 保存角色人设列表
    store.save_characters(project_id, [char1, char2])
    assert os.path.exists(TEST_CHARACTER_FILE) is True
    
    # 3. 加载角色列表
    loaded = store.load_characters(project_id)
    assert len(loaded) == 2
    names = [c["name"] for c in loaded]
    assert "林晚" in names
    assert "沈知行" in names
    
    # 4. 局部更新特定角色的人设属性
    store.update_character(project_id, "林晚", {"personality": ["坚韧", "聪颖"], "motivation": "查明父亲死亡的真相"})
    loaded_updated = store.load_characters(project_id)
    lin_wan_updated = next(c for c in loaded_updated if c["name"] == "林晚")
    assert lin_wan_updated["personality"] == ["坚韧", "聪颖"]
    assert lin_wan_updated["motivation"] == "查明父亲死亡的真相"
    
    # 5. 测试更新不存在的角色，应抛出 KeyError
    with pytest.raises(KeyError):
        store.update_character(project_id, "不存在的角色", {"role": "反派"})
        
    # 6. 测试更新不存在项目的角色，应抛出 KeyError
    with pytest.raises(KeyError):
        store.update_character("incorrect-project-id", "林晚", {"role": "反派"})
