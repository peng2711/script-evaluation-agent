from fastapi import APIRouter, HTTPException, status
from ..schemas.script import ScriptInput
from ..schemas.report import FinalReport, ScriptAnalysis
from ..schemas.agent_state import AgentState
from ..agents.parser_agent import parser_agent
from ..workflow.graph import evaluation_workflow
from ..memory.project_memory import global_project_memory
from ..memory.character_memory import global_character_memory
from typing import Dict, Any, List

router = APIRouter()

@router.get("/health", response_model=Dict[str, str])
def health_check():
    """
    服务健康检查端点。
    """
    return {"status": "ok"}

@router.post("/evaluate", response_model=FinalReport)
def evaluate_script(script: ScriptInput):
    """
    接收用户提交的剧本信息，运行 Multi-Agent 评估工作流，返回最终 Pydantic 校验的 FinalReport 结构化报告。
    并同步将其以 project_id 存入内存中。
    """
    try:
        report = evaluation_workflow.run(script)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="最终评估报告生成失败"
            )
        return report
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"内部评估执行错误: {str(e)}"
        )

@router.post("/parse", response_model=ScriptAnalysis)
def parse_script(script: ScriptInput):
    """
    接收剧本信息，单独执行 Parser Agent 推理，解析并抽取角色列表与核心事件。
    """
    try:
        state = AgentState(script=script)
        state = parser_agent.execute(state)
        if not state.analysis:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="剧本核心要素解析提取失败"
            )
        return state.analysis
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"解析过程内部错误: {str(e)}"
        )

@router.get("/projects/{project_id}", response_model=FinalReport)
def get_project_report_by_id(project_id: str):
    """
    根据项目唯一 ID (project_id) 从内存中检索最新的评估报告。若不存在，返回 404 状态码。
    """
    report = global_project_memory.get_project_report(project_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"未找到项目ID为 '{project_id}' 的评估报告"
        )
    return report

@router.get("/memory/project/{title}", response_model=List[Dict[str, Any]])
def get_project_history(title: str):
    """
    查询指定项目的多轮评估决策历史。
    """
    return global_project_memory.get_history(title)

@router.get("/memory/character/{title}", response_model=Dict[str, Any])
def get_character_profiles(title: str):
    """
    查询指定项目在评估中确立的统一角色人设库。
    """
    return global_character_memory.get_all_profiles(title)

@router.post("/memory/clear", response_model=Dict[str, str])
def clear_all_memories():
    """
    清空内存中的项目及人设记忆。
    """
    global_project_memory.clear()
    global_character_memory.clear()
    return {"message": "项目记忆和人设记忆已成功清空"}
