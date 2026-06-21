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
        调用指定的工具，并在执行时同步将链路详情记录到追踪器。
        """
        import time
        from ..observability.trace import active_trace_recorder
        
        recorder = active_trace_recorder.get()
        start_t = time.perf_counter()
        
        # 限制输入摘要长度，防止日志过长
        input_sum = str(arguments)[:150]

        # 1. 查找并获取工具
        try:
            tool = self.registry.get_tool(tool_name)
        except KeyError:
            err_msg = f"未注册的工具: '{tool_name}'。"
            if recorder:
                recorder.record_tool_call(tool_name, agent_name, input_sum, "", "FAILED", 0.0, err_msg)
            raise ValueError(err_msg)

        # 2. 核验 Agent 调用权限
        try:
            validate_agent_permission(agent_name, tool.allowed_agents, tool_name)
        except Exception as perm_err:
            err_msg = str(perm_err)
            if recorder:
                recorder.record_tool_call(tool_name, agent_name, input_sum, "", "FAILED", 0.0, err_msg)
            raise perm_err

        # 3. 校验输入参数合法性
        try:
            validated_input = tool.validate_input(arguments)
        except Exception as input_err:
            err_msg = str(input_err)
            if recorder:
                recorder.record_tool_call(tool_name, agent_name, input_sum, "", "FAILED", 0.0, err_msg)
            raise input_err

        # 4. 执行工具逻辑，拦截执行报错进行降级
        try:
            kwargs = {f: getattr(validated_input, f) for f in validated_input.__class__.model_fields}
            result = tool.run(**kwargs)
            duration = (time.perf_counter() - start_t) * 1000.0
        except Exception as run_error:
            duration = (time.perf_counter() - start_t) * 1000.0
            fallback_res = get_tool_fallback(tool_name, str(run_error), arguments)
            fallback_sum = str(fallback_res)[:150]
            if recorder:
                recorder.record_tool_call(tool_name, agent_name, input_sum, fallback_sum, "FALLBACK", duration, str(run_error))
            return fallback_res

        # 5. 校验工具输出规范
        try:
            validated_output = tool.validate_output(result)
            output_sum = str(validated_output)[:150]
            if recorder:
                recorder.record_tool_call(tool_name, agent_name, input_sum, output_sum, "SUCCESS", duration)
            return validated_output
        except Exception as val_error:
            err_msg = str(val_error)
            if recorder:
                recorder.record_tool_call(tool_name, agent_name, input_sum, "", "FAILED", duration, err_msg)
            raise ValueError(f"工具 '{tool_name}' 的输出格式校验失败: {err_msg}")

# 全局工具路由器单例
global_tool_router = ToolRouter()
