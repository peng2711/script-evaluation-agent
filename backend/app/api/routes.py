from fastapi import APIRouter, HTTPException
from ..schemas.script import ScriptSubmission
from ..schemas.report import EvaluationReport
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

@router.post("/evaluate", response_model=EvaluationReport)
def evaluate_script(script: ScriptSubmission):
    """
    接收用户提交的剧本信息，运行 Multi-Agent 评估工作流，返回最终 Pydantic 校验的结构化报告。
    """
    try:
        report = evaluation_workflow.run(script)
        if not report:
            raise HTTPException(status_code=500, detail="评估报告生成失败")
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"内部执行错误: {str(e)}")

@router.get("/memory/project/{title}", response_model=List[Dict[str, Any]])
def get_project_history(title: str):
    """
    查询指定项目的多轮评估决策历史。
    """
    return global_project_memory.get_history(title)

@router.get("/memory/character/{title}", response_model=Dict[str, Dict[str, Any]])
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
