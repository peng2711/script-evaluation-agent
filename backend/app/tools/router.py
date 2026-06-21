from typing import Dict, Any, Optional
from pydantic import BaseModel
from .registry import global_tool_registry, ToolRegistry
from .validators import validate_agent_permission
from .fallback import get_tool_fallback

class ToolRouter:
    """
    工具路由器。
    为系统提供标准的工具选择与调用网关，内置白名单鉴权、输入参数核验、异常降级拦截以及输出合规性校验。
    """
    def __init__(self, registry: ToolRegistry = global_tool_registry):
        self.registry = registry

    def call_tool(self, agent_name: str, tool_name: str, arguments: Dict[str, Any]) -> BaseModel:
        """
        调用指定的工具。
        
        参数:
        - agent_name: 调用该工具的 Agent 名称（用于白名单核查）
        - tool_name: 要调用的工具名称
        - arguments: 输入参数字典
        
        返回:
        - 合规的 Pydantic BaseModel 输出对象
        """
        # 1. 查找并获取工具
        try:
            tool = self.registry.get_tool(tool_name)
        except KeyError:
            raise ValueError(f"未注册的工具: '{tool_name}'。")

        # 2. 核验 Agent 调用权限
        validate_agent_permission(agent_name, tool.allowed_agents, tool_name)

        # 3. 校验输入参数合法性
        # 如果输入不符合 input_schema，直接抛出异常（对应“工具输入参数非法时报错”）
        validated_input = tool.validate_input(arguments)

        # 4. 执行工具逻辑，拦截执行报错进行降级
        try:
            result = tool.run(**validated_input.model_dump())
        except Exception as run_error:
            # 运行报错，正常返回 Fallback 降级数据结构
            return get_tool_fallback(tool_name, str(run_error), arguments)

        # 5. 校验工具输出规范
        # 如果输出不符合 output_schema，直接抛出异常（对应“工具输出不符合 schema 时报错”）
        try:
            validated_output = tool.validate_output(result)
            return validated_output
        except Exception as val_error:
            raise ValueError(f"工具 '{tool_name}' 的输出格式校验失败: {str(val_error)}")

# 全局工具路由器单例
global_tool_router = ToolRouter()
