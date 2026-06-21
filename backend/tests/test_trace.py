import pytest
import time
from app.observability.trace import TraceRecorder, TraceEvent, active_trace_recorder
from app.observability.metrics import calculate_metrics, ObservabilityMetrics
from app.schemas.script import ScriptInput
from app.workflow.graph import evaluation_workflow

def test_trace_id_generation_and_node_recording():
    recorder = TraceRecorder()
    assert recorder.trace_id.startswith("tr-")
    assert len(recorder.trace_id) == 11  # "tr-" + 8 hex chars
    
    # 记录节点开始
    recorder.record_node_start("ParserNode", "ParserAgent", "Input script info", retry_count=0)
    assert len(recorder.events) == 1
    event = recorder.events[0]
    assert event.node_name == "ParserNode"
    assert event.agent_name == "ParserAgent"
    assert event.status == "START"
    assert event.input_summary == "Input script info"
    assert event.retry_count == 0
    
    # 记录节点结束
    recorder.record_node_end("ParserNode", "ParserAgent", "Output parse result", "SUCCESS", latency_ms=12.5)
    assert len(recorder.events) == 2
    end_event = recorder.events[1]
    assert end_event.node_name == "ParserNode"
    assert end_event.status == "SUCCESS"
    assert end_event.output_summary == "Output parse result"
    assert end_event.latency_ms == 12.5

def test_trace_tool_call_recording():
    recorder = TraceRecorder()
    
    recorder.record_tool_call(
        tool_name="similar_work_search_tool",
        agent_name="RetrievalAgent",
        input_summary="query content",
        output_summary="found 2 works",
        status="SUCCESS",
        latency_ms=8.2
    )
    assert len(recorder.events) == 1
    event = recorder.events[0]
    assert event.tool_name == "similar_work_search_tool"
    assert event.agent_name == "RetrievalAgent"
    assert event.status == "SUCCESS"
    assert event.input_summary == "query content"
    assert event.output_summary == "found 2 works"
    assert event.latency_ms == 8.2

def test_trace_error_recording():
    recorder = TraceRecorder()
    recorder.record_node_start("AnalysisNode", "AnalysisAgent", "Input", retry_count=1)
    
    # 延迟一下，模拟耗时
    time.sleep(0.01)
    
    recorder.record_error("AnalysisNode", "AnalysisAgent", "SyntaxError in agent execution")
    assert len(recorder.events) == 2
    err_event = recorder.events[1]
    assert err_event.node_name == "AnalysisNode"
    assert err_event.status == "FAILED"
    assert err_event.error_message == "SyntaxError in agent execution"
    assert err_event.latency_ms > 5.0  # 耗时大于5毫秒

def test_metrics_calculation():
    events = [
        TraceEvent(trace_id="tr-test", node_name="ParserNode", agent_name="ParserAgent", status="START", input_summary="in", output_summary="", retry_count=1, latency_ms=0.0),
        TraceEvent(trace_id="tr-test", node_name="ParserNode", agent_name="ParserAgent", status="SUCCESS", input_summary="", output_summary="out", retry_count=0, latency_ms=10.0),
        
        # 工具调用
        TraceEvent(trace_id="tr-test", agent_name="RetrievalAgent", tool_name="similar_work_search_tool", status="SUCCESS", input_summary="in", output_summary="out", latency_ms=4.0),
        TraceEvent(trace_id="tr-test", agent_name="RetrievalAgent", tool_name="rerank_tool", status="FALLBACK", input_summary="in", output_summary="out", error_message="crash", latency_ms=2.0),
        
        TraceEvent(trace_id="tr-test", node_name="AnalysisNode", agent_name="AnalysisAgent", status="START", input_summary="in", output_summary="", retry_count=2, latency_ms=0.0),
        TraceEvent(trace_id="tr-test", node_name="AnalysisNode", agent_name="AnalysisAgent", status="SUCCESS", input_summary="", output_summary="out", retry_count=0, latency_ms=20.0),
    ]
    
    metrics = calculate_metrics(events, workflow_success=True)
    assert isinstance(metrics, ObservabilityMetrics)
    assert metrics.total_latency_ms == 30.0  # 10.0 + 20.0
    assert metrics.total_tool_calls == 2
    assert metrics.failed_tool_calls == 0
    assert metrics.fallback_used == 1
    assert metrics.retry_count == 2
    assert metrics.workflow_success is True

def test_workflow_observability_integration():
    script_input = ScriptInput(
        project_id="test-observability-id",
        title="破晓猎杀",
        raw_text="特工林啸与反派赵乾在集装箱码头起获账目发生爆炸脱身。",
        genre="动作",
        target_audience="大众"
    )
    
    # 运行工作流，获得报告
    report = evaluation_workflow.run(script_input)
    
    # 验证 FinalReport 含有 trace 字段并有正确内容
    assert report.trace is not None
    assert "events" in report.trace
    assert "metrics" in report.trace
    
    # 事件流应记录各个节点
    events = report.trace["events"]
    assert len(events) > 0
    node_names = {e["node_name"] for e in events if e["node_name"] is not None}
    assert "ParserNode" in node_names
    assert "AnalysisNode" in node_names
    
    # 指标统计应有效
    metrics = report.trace["metrics"]
    assert metrics["total_latency_ms"] >= 0.0
    assert metrics["workflow_success"] is True
