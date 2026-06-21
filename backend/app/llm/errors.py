class LLMError(Exception):
    """LLM 模块基础异常"""
    pass

class LLMAPIError(LLMError):
    """LLM API 请求或连接异常"""
    pass

class LLMValidationError(LLMError):
    """LLM 返回内容解析或 Pydantic schema 校验异常"""
    pass
