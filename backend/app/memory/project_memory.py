from typing import Dict, List, Any, Optional
from ..schemas.report import FinalReport

class ProjectMemory:
    """
    项目级别记忆管理器 (在内存中运行，记录各个项目在多轮评估中的决策演变，并支持通过 project_id 查询)
    """
    def __init__(self):
        # 键为 project_title, 值为该项目历史多次评估报告的简要摘要和立项建议
        self._history_storage: Dict[str, List[Dict[str, Any]]] = {}
        # 键为 project_id, 值为最新评估出的 FinalReport 对象
        self._reports_storage: Dict[str, FinalReport] = {}

    def add_evaluation_record(self, project_title: str, project_id: str, decision: str, executive_summary: str):
        """
        向项目历史记忆中添加一条评估快照记录
        """
        if project_title not in self._history_storage:
            self._history_storage[project_title] = []
        
        self._history_storage[project_title].append({
            "project_id": project_id,
            "decision": decision,
            "executive_summary": executive_summary
        })

    def get_history(self, project_title: str) -> List[Dict[str, Any]]:
        """
        获取项目的评估历史纪录
        """
        return self._history_storage.get(project_title, [])

    def add_project_report(self, project_id: str, report: FinalReport):
        """
        以 project_id 为键归档保存最新的评估报告到内存中
        """
        self._reports_storage[project_id] = report

    def get_project_report(self, project_id: str) -> Optional[FinalReport]:
        """
        根据 project_id 在内存中查询项目的最新报告
        """
        return self._reports_storage.get(project_id)

    def clear(self):
        """
        清空内存中的所有项目记忆
        """
        self._history_storage.clear()
        self._reports_storage.clear()

# 全局内存单例
global_project_memory = ProjectMemory()
