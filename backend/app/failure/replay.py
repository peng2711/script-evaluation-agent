import os
import json
from typing import Optional
from ..schemas.report import FinalReport
from ..schemas.script import ScriptInput
from .case_store import global_failure_case_store

def replay_case(case_id: str) -> Optional[FinalReport]:
    """
    重放指定的失败案例：
    1. 加载失败案例；
    2. 加载当时执行的原始 ScriptInput 数据；
    3. 重新配置工作流并运行，返回重新评估后锁定的报告。
    """
    case = global_failure_case_store.load_failure_case(case_id)
    if not case:
        return None

    # 从本地存储中加载对应的原始剧本输入
    current_dir = os.path.dirname(os.path.abspath(__file__))
    script_inputs_path = os.path.normpath(os.path.join(current_dir, "..", "..", "storage", "script_inputs.json"))
    
    if not os.path.exists(script_inputs_path):
        return None
        
    try:
        with open(script_inputs_path, "r", encoding="utf-8") as f:
            inputs = json.load(f)
    except Exception:
        return None

    script_data = inputs.get(case.project_id)
    if not script_data:
        return None

    script_input = ScriptInput.model_validate(script_data)
    
    # 重新实例化对应配置的工作流并重放运行
    # 若失败原因与工具或降级有关，默认开启 use_tools_via_router 以重放该状态
    use_router = any(kw in case.failure_type.upper() for kw in ["TOOL", "FALLBACK", "WITH_TOOLS"])
    
    from ..workflow.graph import ScriptEvaluationWorkflow
    wf = ScriptEvaluationWorkflow(max_iterations=2, use_tools_via_router=use_router)
    report = wf.run(script_input)
    return report
