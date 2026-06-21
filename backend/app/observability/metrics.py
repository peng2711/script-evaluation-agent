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
    cache_hit_count: int = Field(default=0, description="缓存命中次数")
    cache_miss_count: int = Field(default=0, description="缓存未命中次数")
    cache_hit_rate: float = Field(default=0.0, description="缓存命中率")
    estimated_llm_calls: int = Field(default=0, description="估算的大模型 API 调用次数")
    estimated_tool_cost: float = Field(default=0.0, description="估算的工具调用与大模型服务总成本（美元）")

def calculate_metrics(
    events: List[TraceEvent], 
    workflow_success: bool = True,
    cache_hit_count: int = 0,
    cache_miss_count: int = 0,
    parser_cache_hit_count: int = 0
) -> ObservabilityMetrics:
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

    # 4. 计算缓存效率指标
    total_cache_requests = cache_hit_count + cache_miss_count
    cache_hit_rate = (cache_hit_count / total_cache_requests) if total_cache_requests > 0 else 0.0

    # 5. 估算大模型 API 调用次数
    # 默认情况下，ParserNode (大模型解析), AnalysisNode (大模型评分), ReviewNode (大模型审核) 会调用 LLM。
    # 如果 ParserAgent 命中缓存，则该次 ParserNode 执行不产生实际 LLM 交互。
    parser_runs = sum(
        1 for e in events 
        if e.node_name == "ParserNode" and e.status in ("SUCCESS", "FAILED") and e.tool_name is None
    )
    # 根据具体的 Parser 缓存命中次数扣减 LLM 调用
    parser_llm = max(0, parser_runs - parser_cache_hit_count)

    other_llm_runs = sum(
        1 for e in events 
        if e.node_name in ("AnalysisNode", "ReviewNode") 
        and e.status in ("SUCCESS", "FAILED") 
        and e.tool_name is None
    )
    estimated_llm_calls = parser_llm + other_llm_runs

    # 6. 估算服务成本
    # 成本规则设计：LLM 调用每次约 0.01 美元；工具调用每次 0.001 美元
    estimated_tool_cost = round((estimated_llm_calls * 0.01) + (total_tools * 0.001), 6)

    return ObservabilityMetrics(
        total_latency_ms=round(total_latency, 2),
        total_tool_calls=total_tools,
        failed_tool_calls=failed_tools,
        retry_count=max_retries,
        fallback_used=fallback_count,
        workflow_success=workflow_success,
        cache_hit_count=cache_hit_count,
        cache_miss_count=cache_miss_count,
        cache_hit_rate=cache_hit_rate,
        estimated_llm_calls=estimated_llm_calls,
        estimated_tool_cost=estimated_tool_cost
    )
