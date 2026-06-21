import os
import pytest
from pydantic import BaseModel, Field
from app.llm.factory import get_llm_client
from app.llm.mock_client import MockLLMClient
from app.llm.openai_client import OpenAILLMClient
from app.llm.errors import LLMValidationError, LLMAPIError

class SimpleMockModel(BaseModel):
    name: str = Field(..., description="测试名字")
    count: int = Field(..., description="测试数量")
    flag: bool = Field(default=False, description="测试标志位")

def test_default_provider_is_mock(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    client = get_llm_client()
    assert isinstance(client, MockLLMClient)

def test_missing_key_fallback(monkeypatch):
    # 1. 模拟 openai 且 KEY 为空时 fallback
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    client_oa = get_llm_client()
    assert isinstance(client_oa, MockLLMClient)

    # 2. 模拟 gemini 且 KEY 为空时 fallback
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    client_gem = get_llm_client()
    assert isinstance(client_gem, MockLLMClient)

    # 3. 模拟未知 provider fallback 到 mock
    monkeypatch.setenv("LLM_PROVIDER", "unknown_provider")
    client_unk = get_llm_client()
    assert isinstance(client_unk, MockLLMClient)

def test_mock_client_generate_json_returns_dict():
    client = MockLLMClient()
    schema = SimpleMockModel.model_json_schema()
    
    result = client.generate_json("请生成一些测试数据", schema)
    assert isinstance(result, dict)
    
    # 校验字段是否存在以及类型是否满足 Schema 定义
    assert "name" in result
    assert "count" in result
    assert "flag" in result
    
    # 验证能成功反序列化为 Pydantic 结构体
    obj = SimpleMockModel.model_validate(result)
    assert isinstance(obj.name, str)
    assert isinstance(obj.count, int)
    assert isinstance(obj.flag, bool)

def test_schema_validation_failures():
    client = OpenAILLMClient()
    schema = SimpleMockModel.model_json_schema()

    # 1. 缺失必选字段
    bad_data_missing = {"name": "Test"}
    with pytest.raises(LLMValidationError) as exc1:
        client._validate_schema(bad_data_missing, schema)
    assert "缺失必选字段: 'count'" in str(exc1.value)

    # 2. 类型不匹配: 期望 integer 得到 string
    bad_data_type1 = {"name": "Test", "count": "not_an_int"}
    with pytest.raises(LLMValidationError) as exc2:
        client._validate_schema(bad_data_type1, schema)
    assert "期望为 integer" in str(exc2.value)

    # 3. 类型不匹配: 期望 integer 得到 boolean (Python 中 bool 是 int 的子类，必须特别校验)
    bad_data_type2 = {"name": "Test", "count": True}
    with pytest.raises(LLMValidationError) as exc3:
        client._validate_schema(bad_data_type2, schema)
    assert "期望为 integer，但实际类型为: bool" in str(exc3.value)

    # 4. 期待 dict 对象传入
    with pytest.raises(LLMValidationError) as exc4:
        client._validate_schema(["not", "a", "dict"], schema)
    assert "期望 JSON 对象" in str(exc4.value)
