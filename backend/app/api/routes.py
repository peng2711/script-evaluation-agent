from fastapi import APIRouter, HTTPException, status
from ..schemas.script import ScriptInput
from ..schemas.report import FinalReport, ScriptAnalysis
from ..schemas.agent_state import AgentState
from ..agents.parser_agent import parser_agent
from ..workflow.graph import evaluation_workflow
from ..memory.project_memory import global_project_memory
from ..memory.character_memory import global_character_memory
from ..feedback.schemas import FeedbackInput
from ..failure.schemas import FailureCase
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
    根据项目唯一 ID (project_id) 从持久化存储中检索最新的评估报告。若不存在，返回 404 状态码。
    """
    report_dict = global_project_memory.load_project(project_id)
    if not report_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"未找到项目ID为 '{project_id}' 的评估报告"
        )
    return FinalReport.model_validate(report_dict)

@router.get("/memory/project/{title}", response_model=List[Dict[str, Any]])
def get_project_history(title: str):
    """
    查询指定项目的多轮评估决策历史。
    """
    projects = global_project_memory.list_projects()
    matched = []
    for proj in projects:
        if proj.get("title") == title:
            matched.append({
                "project_id": proj.get("project_id"),
                "decision": proj.get("decision_suggestion"),
                "executive_summary": proj.get("executive_summary")
            })
    return matched

@router.get("/memory/character/{title}", response_model=Dict[str, Any])
def get_character_profiles(title: str):
    """
    查询指定项目在评估中确立的统一角色人设库。
    """
    projects = global_project_memory.list_projects()
    project_ids = [proj.get("project_id") for proj in projects if proj.get("title") == title]
    
    profiles_dict = {}
    for pid in project_ids:
        chars = global_character_memory.load_characters(pid)
        for char in chars:
            profiles_dict[char.get("name")] = char
    return profiles_dict

@router.post("/memory/clear", response_model=Dict[str, str])
def clear_all_memories():
    """
    清空内存中的项目及人设记忆。
    """
    global_project_memory.clear()
    global_character_memory.clear()
    return {"message": "项目记忆和人设记忆已成功清空"}

@router.post("/feedback")
def submit_feedback(feedback: FeedbackInput):
    """
    提交用户对剧本评估报告的反馈，自动触发失败案例沉淀逻辑。
    """
    from ..feedback.collector import global_feedback_collector
    try:
        failure_case = global_feedback_collector.collect_feedback(feedback)
        response = {"message": "反馈收集成功"}
        if failure_case:
            response["failure_case_created"] = True
            response["case_id"] = failure_case.case_id
        else:
            response["failure_case_created"] = False
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"收集反馈出错: {str(e)}"
        )

@router.get("/feedback/{project_id}", response_model=List[FeedbackInput])
def get_feedback_by_project_id(project_id: str):
    """
    检索特定项目的历史用户反馈记录。
    """
    from ..feedback.store import global_feedback_store
    return global_feedback_store.load_feedback_by_project(project_id)

@router.get("/failure-cases", response_model=List[FailureCase])
def list_failure_cases():
    """
    列出所有沉淀下来的失败案例。
    """
    from ..failure.case_store import global_failure_case_store
    return global_failure_case_store.list_failure_cases()

@router.get("/failure-cases/{case_id}", response_model=FailureCase)
def get_failure_case_by_id(case_id: str):
    """
    根据唯一 ID 检索指定的失败案例诊断详情。
    """
    from ..failure.case_store import global_failure_case_store
    case = global_failure_case_store.load_failure_case(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到ID为 '{case_id}' 的失败案例"
        )
    return case

