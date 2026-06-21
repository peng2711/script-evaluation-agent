from abc import ABC, abstractmethod

class LLMClient(ABC):
    """
    LLM 客户端抽象基类，定义生成文本与生成 JSON 结构体两个标准接口。
    """
    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> str:
        """
        生成纯文本内容。
        """
        pass

    @abstractmethod
    def generate_json(self, prompt: str, schema: dict, **kwargs) -> dict:
        """
        根据指定的 JSON schema 生成结构化字典。
        """
        pass
