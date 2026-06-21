from typing import Any, Dict, List
from .tool_schemas import (
    ScriptParseOutput,
    SimilarWorkSearchOutput,
    RerankOutput,
    MemoryReadOutput,
    MemoryWriteOutput,
    ReviewCheckOutput
)
from ..schemas.report import ScriptAnalysis, CharacterProfile, PlotEvent

def get_tool_fallback(tool_name: str, error_msg: str, original_args: Dict[str, Any]) -> Any:
    """
    当工具执行抛出异常时，根据工具类型拦截并返回合规的 Pydantic Fallback 降级输出对象。
    """
    if tool_name == "script_parse_tool":
        # 返回默认的主人公张无名的解析结构
        default_analysis = ScriptAnalysis(
            characters=[
                CharacterProfile(
                    name="张无名",
                    role="故事主人公",
                    personality=["隐隐"],
                    motivation="生存与寻找真相",
                    relationships={},
                    constraints=[],
                    evidence_spans=["解析服务降级，自动注入默认角色。"]
                )
            ],
            character_relations=[],
            core_conflict="故事发生的基本起因与寻找真相的过程。",
            plot_events=[
                PlotEvent(
                    event_id="EVT-GEN-999",
                    summary="降级启动事件。",
                    characters=["张无名"],
                    conflict_type="客观环境阻碍",
                    evidence_span="降级默认段落描述"
                )
            ],
            risk_points=[],
            strengths=[],
            weaknesses=[]
        )
        return ScriptParseOutput(analysis=default_analysis)

    elif tool_name == "similar_work_search_tool":
        return SimilarWorkSearchOutput(evidences=[])

    elif tool_name == "rerank_tool":
        # 重排失败，直接将原 evidences 列表原样返还，保证链条不断开
        input_evidences = original_args.get("evidences", [])
        return RerankOutput(evidences=input_evidences)

    elif tool_name == "memory_read_tool":
        return MemoryReadOutput(project_report=None, characters=None)

    elif tool_name == "memory_write_tool":
        return MemoryWriteOutput(success=False, message=f"操作降级，执行失败: {error_msg}")

    elif tool_name == "review_check_tool":
        return ReviewCheckOutput(issues=[])

    raise ValueError(f"未知的工具名称: '{tool_name}'，无法调用降级逻辑。")
