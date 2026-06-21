import pytest
from app.tools.registry import global_tool_registry, ToolRegistry
from app.tools.base import BaseTool
from pydantic import BaseModel

# 简单的 Mock Schema
class MockInput(BaseModel):
    query: str

class MockOutput(BaseModel):
    result: str

class MockTestTool(BaseTool):
    def __init__(self, name="mock_test_tool", allowed_agents=None):
        if allowed_agents is None:
            allowed_agents = ["ParserAgent"]
        super().__init__(
            name=name,
            description="Mock tool for registry tests",
            input_schema=MockInput,
            output_schema=MockOutput,
            allowed_agents=allowed_agents
        )
    def run(self, query: str) -> MockOutput:
        return MockOutput(result=f"Success: {query}")

def test_registry_registration_and_list():
    registry = ToolRegistry()
    
    # 注册前，工具列表为空
    assert len(registry.list_tools()) == 0
    
    # 注册一个新工具
    tool = MockTestTool()
    registry.register_tool(tool)
    
    # 注册后，工具列表中包含该工具
    assert len(registry.list_tools()) == 1
    assert registry.get_tool("mock_test_tool") == tool

def test_registry_duplicate_registration_error():
    registry = ToolRegistry()
    tool = MockTestTool()
    registry.register_tool(tool)
    
    # 重复注册抛出 ValueError
    with pytest.raises(ValueError) as excinfo:
        registry.register_tool(tool)
    assert "已注册" in str(excinfo.value)

def test_registry_key_error_for_missing_tool():
    registry = ToolRegistry()
    
    # 获取未注册工具抛出 KeyError
    with pytest.raises(KeyError):
        registry.get_tool("non_existent_tool")

def test_registry_list_tools_for_agent():
    registry = ToolRegistry()
    tool1 = MockTestTool(name="tool1", allowed_agents=["ParserAgent"])
    tool2 = MockTestTool(name="tool2", allowed_agents=["RetrievalAgent"])
    
    registry.register_tool(tool1)
    registry.register_tool(tool2)
    
    # 校验不同 Agent 权限筛选
    parser_tools = registry.list_tools_for_agent("ParserAgent")
    assert len(parser_tools) == 1
    assert parser_tools[0].name == "tool1"
    
    retrieval_tools = registry.list_tools_for_agent("RetrievalAgent")
    assert len(retrieval_tools) == 1
    assert retrieval_tools[0].name == "tool2"
    
    # Workflow 拥有超级管理员权限，可以获取所有工具
    workflow_tools = registry.list_tools_for_agent("Workflow")
    assert len(workflow_tools) == 2

def test_global_registry_contains_all_tools():
    # 全局工具注册表单例中，应该包含了全部 6 个内置工具
    registered_names = [t.name for t in global_tool_registry.list_tools()]
    expected_names = [
        "script_parse_tool",
        "similar_work_search_tool",
        "rerank_tool",
        "memory_read_tool",
        "memory_write_tool",
        "review_check_tool"
    ]
    for name in expected_names:
        assert name in registered_names
