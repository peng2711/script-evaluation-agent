import pytest
from app.tools.registry import ToolRegistry
from app.tools.router import ToolRouter
from app.tools.base import BaseTool
from app.tools.tool_schemas import SimilarWorkSearchInput, SimilarWorkSearchOutput
from pydantic import BaseModel

# Mock Schemas
class MockInput(BaseModel):
    query: str

class MockOutput(BaseModel):
    result: str

class GoodMockTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="good_mock_tool",
            description="Runs perfectly",
            input_schema=MockInput,
            output_schema=MockOutput,
            allowed_agents=["ParserAgent"]
        )
    def run(self, query: str) -> MockOutput:
        return MockOutput(result=f"Success: {query}")

class BadOutputMockTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="bad_output_tool",
            description="Returns invalid output schema",
            input_schema=MockInput,
            output_schema=MockOutput,
            allowed_agents=["ParserAgent"]
        )
    def run(self, query: str) -> dict:
        # 返回不符合 MockOutput schema 的格式
        return {"bad_field": "corrupted_data"}

class CrashingMockTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="similar_work_search_tool",  # 使用已定义fallback的真实名称
            description="Throws error",
            input_schema=SimilarWorkSearchInput,
            output_schema=SimilarWorkSearchOutput,
            allowed_agents=["RetrievalAgent"]
        )
    def run(self, query: str, top_k: int = 2) -> SimilarWorkSearchOutput:
        raise RuntimeError("Simulated backend crash")


def test_router_success_invocation():
    registry = ToolRegistry()
    registry.register_tool(GoodMockTool())
    router = ToolRouter(registry=registry)
    
    # 正常请求，校验输出类型和结果
    res = router.call_tool("ParserAgent", "good_mock_tool", {"query": "hello"})
    assert isinstance(res, MockOutput)
    assert res.result == "Success: hello"

def test_router_unregistered_tool():
    registry = ToolRegistry()
    router = ToolRouter(registry=registry)
    
    # 访问未注册工具，抛出 ValueError
    with pytest.raises(ValueError) as excinfo:
        router.call_tool("ParserAgent", "non_existent_tool", {"query": "test"})
    assert "未注册" in str(excinfo.value)

def test_router_permission_denied():
    registry = ToolRegistry()
    registry.register_tool(GoodMockTool())
    router = ToolRouter(registry=registry)
    
    # RetrievalAgent 无权调用 good_mock_tool，抛出 PermissionError
    with pytest.raises(PermissionError) as excinfo:
        router.call_tool("RetrievalAgent", "good_mock_tool", {"query": "test"})
    assert "越权访问错误" in str(excinfo.value)

def test_router_invalid_input_parameters():
    registry = ToolRegistry()
    registry.register_tool(GoodMockTool())
    router = ToolRouter(registry=registry)
    
    # 传入的参数中缺少必填字段 query
    with pytest.raises(ValueError) as excinfo:
        router.call_tool("ParserAgent", "good_mock_tool", {"wrong_key": "test"})
    assert "输入参数校验失败" in str(excinfo.value)

def test_router_output_schema_mismatch():
    registry = ToolRegistry()
    registry.register_tool(BadOutputMockTool())
    router = ToolRouter(registry=registry)
    
    # 工具输出校验失败，抛出 ValueError
    with pytest.raises(ValueError) as excinfo:
        router.call_tool("ParserAgent", "bad_output_tool", {"query": "test"})
    assert "输出格式校验失败" in str(excinfo.value)

def test_router_fallback_on_tool_error():
    registry = ToolRegistry()
    registry.register_tool(CrashingMockTool())
    router = ToolRouter(registry=registry)
    
    # 调用崩溃工具，应拦截并返回合规的 fallback 降级空对象
    res = router.call_tool("RetrievalAgent", "similar_work_search_tool", {"query": "test"})
    assert isinstance(res, SimilarWorkSearchOutput)
    assert len(res.evidences) == 0
