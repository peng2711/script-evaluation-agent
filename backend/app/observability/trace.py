from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import datetime
import uuid
import time
from contextvars import ContextVar

class TraceEvent(BaseModel):
    trace_id: str = Field(..., description="链路追踪唯一ID")
    node_name: Optional[str] = Field(None, description="工作流节点名称")
    agent_name: Optional[str] = Field(None, description="执行的 Agent 名称")
    tool_name: Optional[str] = Field(None, description="调用的工具名称")
    status: str = Field(..., description="执行状态 (START/SUCCESS/FAILED/FALLBACK)")
    input_summary: str = Field(..., description="输入数据摘要")
    output_summary: str = Field(..., description="输出数据/结果摘要")
    error_message: Optional[str] = Field(None, description="错误/异常详细说明")
    retry_count: int = Field(default=0, description="重试计数")
    latency_ms: float = Field(default=0.0, description="耗时（毫秒）")
    timestamp: str = Field(
        default_factory=lambda: datetime.datetime.now().isoformat(),
        description="事件发生时间戳"
    )
    review_action: Optional[str] = Field(None, description="审查动作")
    review_reason: Optional[str] = Field(None, description="审查原因")
    target_node: Optional[str] = Field(None, description="目标跳转节点")

# 声明线程/协程安全的 ContextVar 作为上下文追踪器
active_trace_recorder: ContextVar[Optional['TraceRecorder']] = ContextVar("active_trace_recorder", default=None)

class TraceRecorder:
    """
    链路追踪记录器，负责管理单次评估请求中的所有追踪事件。
    """
    def __init__(self, trace_id: Optional[str] = None):
        self.trace_id = trace_id or f"tr-{uuid.uuid4().hex[:8]}"
        self.events: List[TraceEvent] = []
        self._node_start_times: Dict[str, float] = {}

    def start_trace(self, trace_id: str) -> None:
        self.trace_id = trace_id
        self.events.clear()
        self._node_start_times.clear()

    def record_node_start(self, node_name: str, agent_name: str, input_summary: str, retry_count: int) -> None:
        self._node_start_times[node_name] = time.perf_counter()
        event = TraceEvent(
            trace_id=self.trace_id,
            node_name=node_name,
            agent_name=agent_name,
            status="START",
            input_summary=input_summary,
            output_summary="",
            retry_count=retry_count,
            latency_ms=0.0
        )
        self.events.append(event)
        # 记录结构化日志
        from .logger import log_trace_event
        log_trace_event(event)

    def record_tool_call(
        self,
        tool_name: str,
        agent_name: str,
        input_summary: str,
        output_summary: str,
        status: str,
        latency_ms: float,
        error_message: Optional[str] = None
    ) -> None:
        event = TraceEvent(
            trace_id=self.trace_id,
            agent_name=agent_name,
            tool_name=tool_name,
            status=status,
            input_summary=input_summary,
            output_summary=output_summary,
            error_message=error_message,
            latency_ms=latency_ms
        )
        self.events.append(event)
        from .logger import log_trace_event
        log_trace_event(event)

    def record_node_end(
        self,
        node_name: str,
        agent_name: str,
        output_summary: str,
        status: str,
        latency_ms: float,
        retry_count: int = 0,
        review_action: Optional[str] = None,
        review_reason: Optional[str] = None,
        target_node: Optional[str] = None
    ) -> None:
        event = TraceEvent(
            trace_id=self.trace_id,
            node_name=node_name,
            agent_name=agent_name,
            status=status,
            input_summary="",
            output_summary=output_summary,
            latency_ms=latency_ms,
            retry_count=retry_count,
            review_action=review_action,
            review_reason=review_reason,
            target_node=target_node
        )
        self.events.append(event)
        from .logger import log_trace_event
        log_trace_event(event)

    def record_error(self, node_name: str, agent_name: str, error_message: str) -> None:
        latency_ms = 0.0
        if node_name in self._node_start_times:
            latency_ms = (time.perf_counter() - self._node_start_times[node_name]) * 1000.0
            
        event = TraceEvent(
            trace_id=self.trace_id,
            node_name=node_name,
            agent_name=agent_name,
            status="FAILED",
            input_summary="",
            output_summary="",
            error_message=error_message,
            latency_ms=latency_ms
        )
        self.events.append(event)
        from .logger import log_trace_event
        log_trace_event(event)

    def export_trace(self) -> List[TraceEvent]:
        return self.events
