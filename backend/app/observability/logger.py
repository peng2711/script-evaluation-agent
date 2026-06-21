import logging
import json
from .trace import TraceEvent

# 获取或创建结构化日志记录器
logger = logging.getLogger("agent_observability")
logger.setLevel(logging.INFO)

# 防止重复添加 Handler
if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

def log_trace_event(event: TraceEvent) -> None:
    """
    将链路 TraceEvent 以结构化 JSON 格式输出至日志系统，便于日志采集分析（如 ELK / Grafana Loki）。
    """
    try:
        log_data = event.model_dump()
        logger.info(f"[TraceEvent] {json.dumps(log_data, ensure_ascii=False)}")
    except Exception as e:
        logger.error(f"Failed to log TraceEvent: {str(e)}")
