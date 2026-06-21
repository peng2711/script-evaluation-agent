import os
import logging
from .base import LLMClient
from .mock_client import MockLLMClient
from .openai_client import OpenAILLMClient
from .gemini_client import GeminiLLMClient

logger = logging.getLogger("agent_observability")

def get_llm_client() -> LLMClient:
    """
    根据环境变量 LLM_PROVIDER 获取并返回 LLM 客户端实例。
    若对应的 API KEY 未配置，则自动回退到 MockLLMClient 并记录警告。
    """
    provider = os.getenv("LLM_PROVIDER", "mock").strip().lower()
    
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            logger.warning("检测到环境变量 LLM_PROVIDER=openai，但 OPENAI_API_KEY 未配置。已自动回退到 MockLLMClient。")
            return MockLLMClient()
        return OpenAILLMClient()
        
    elif provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            logger.warning("检测到环境变量 LLM_PROVIDER=gemini，但 GEMINI_API_KEY 未配置。已自动回退到 MockLLMClient。")
            return MockLLMClient()
        return GeminiLLMClient()
        
    else:
        if provider != "mock":
            logger.warning(f"未知的 LLM_PROVIDER: '{provider}'，已自动回退为 MockLLMClient。")
        return MockLLMClient()
