from typing import List, Type, Any, Dict
from pydantic import BaseModel, ValidationError

class BaseTool:
    """
    系统工具基类。
    约束工具名称、描述、输入/输出 Pydantic 校验 Schema，以及有权调用该工具的 Agent 白名单。
    """
    def __init__(
        self,
        name: str,
        description: str,
        input_schema: Type[BaseModel],
        output_schema: Type[BaseModel],
        allowed_agents: List[str]
    ):
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.output_schema = output_schema
        self.allowed_agents = allowed_agents

    def validate_input(self, data: Any) -> BaseModel:
        """
        验证输入数据是否符合 input_schema 规范。
        支持 Pydantic 模型对象或字典参数。
        """
        if isinstance(data, self.input_schema):
            return data
        if isinstance(data, dict):
            try:
                return self.input_schema.model_validate(data)
            except ValidationError as e:
                raise ValueError(f"工具 '{self.name}' 输入参数校验失败: {str(e)}")
        raise ValueError(f"工具 '{self.name}' 需要的输入为字典或 {self.input_schema.__name__}，但实际为 {type(data).__name__}")

    def validate_output(self, data: Any) -> BaseModel:
        """
        验证工具输出是否符合 output_schema 规范。
        """
        if isinstance(data, self.output_schema):
            return data
        if isinstance(data, dict):
            try:
                return self.output_schema.model_validate(data)
            except ValidationError as e:
                raise ValueError(f"工具 '{self.name}' 输出参数校验失败: {str(e)}")
        raise ValueError(f"工具 '{self.name}' 生成的输出为字典或 {self.output_schema.__name__}，但实际为 {type(data).__name__}")

    def run(self, *args, **kwargs) -> Any:
        """
        工具核心执行逻辑。由具体子类实现。
        """
        raise NotImplementedError("工具子类必须实现 run 方法。")
