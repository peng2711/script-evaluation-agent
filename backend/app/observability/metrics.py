from pydantic import BaseModel, Field
from typing import List
from .trace import TraceEvent

class ObservabilityMetrics(BaseModel):
    total_latency_ms: float = Field(default=0.0, description="整个评估流程总响应时延（毫秒）")
    total_tool_calls: int = Field(default=0, description="工具总计调用次数")
    failed_tool_calls: int = Field(default=0, description="工具执行失败次数")
    retry_count: int = Field(default=0, description="反思打回重试总次数")
    fallback_used: int = Field(default=0, description="触发工具降级 Fallback 调用的次数")
    workflow_success: bool = Field(default=True, description="最终工作流是否成功执行")

def calculate_metrics(events: List[TraceEvent], workflow_success: bool = True) -> ObservabilityMetrics:
    """
    根据执行过程中累积的链路 TraceEvent 列表，计算统计各项指标。
    """
    total_latency = 0.0
    total_tools = 0
    failed_tools = 0
    max_retries = 0
    fallback_count = 0

    # 1. 累加所有 node 执行完毕的耗时 (SUCCESS 或 FAILED 且不是 tool_name 调用)
    node_ends = [
        e for e in events 
        if e.node_name is not None and e.status in ("SUCCESS", "FAILED") and e.tool_name is None
    ]
    total_latency = sum(e.latency_ms for e in node_ends)

    # 2. 统计工具调用相关数据
    tool_events = [e for e in events if e.tool_name is not None]
    
    # 所有的调用行为（包含 START, SUCCESS, FAILED, FALLBACK，我们以最终状态事件为准，比如除 START 外的状态数）
    tool_ends = [e for e in tool_events if e.status in ("SUCCESS", "FAILED", "FALLBACK")]
    total_tools = len(tool_ends)
    
    # 失败指的是那些状态为 FAILED 的工具调用 (不含降级，若是彻底失败跑出异常且无fallback或fallback也失败算FAILED)
    failed_tools = sum(1 for e in tool_ends if e.status == "FAILED")
    
    # 降级调用
    fallback_count = sum(1 for e in tool_ends if e.status == "FALLBACK")

    # 3. 反思最大重试数
    node_starts = [e for e in events if e.node_name is not None and e.status == "START"]
    if node_starts:
        max_retries = max(e.retry_count for e in node_starts)

    return ObservabilityMetrics(
        total_latency_ms=round(total_latency, 2),
        total_tool_calls=total_tools,
        failed_tool_calls=failed_tools,
        retry_count=max_retries,
        fallback_used=fallback_count,
        workflow_success=workflow_success
    )
