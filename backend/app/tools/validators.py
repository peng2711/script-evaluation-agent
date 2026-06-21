from typing import List

def validate_agent_permission(agent_name: str, allowed_agents: List[str], tool_name: str) -> None:
    """
    核验 Agent 动作的工具调用白名单权限。
    注：Workflow 本身拥有全局最高权限，允许调用所有工具。
    """
    if agent_name == "Workflow":
        return
    if agent_name not in allowed_agents:
        raise PermissionError(
            f"越权访问错误: Agent '{agent_name}' 无权调用工具 '{tool_name}'。允许的调用方为: {allowed_agents}"
        )

def validate_non_empty_string(value: str, name: str) -> None:
    """
    核验字符串字段非空。
    """
    if not value or not value.strip():
        raise ValueError(f"参数校验失败: '{name}' 不能为空值。")
