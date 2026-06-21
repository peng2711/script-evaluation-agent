from typing import Dict, List, Any, Optional

class ProjectMemory:
    """
    项目级别记忆管理器 (在内存中运行，记录各个项目在多轮评估中的决策演变)
    """
    def __init__(self):
        # 键为 project_title, 值为该项目历史多次评估报告的简要摘要和立项建议
        self._storage: Dict[str, List[Dict[str, Any]]] = {}

    def add_evaluation_record(self, project_title: str, project_id: str, decision: str, executive_summary: str):
        """
        向项目记忆中添加一条评估快照记录
        """
        if project_title not in self._storage:
            self._storage[project_title] = []
        
        self._storage[project_title].append({
            "project_id": project_id,
            "decision": decision,
            "executive_summary": executive_summary
        })

    def get_history(self, project_title: str) -> List[Dict[str, Any]]:
        """
        获取项目的评估历史纪录
        """
        return self._storage.get(project_title, [])

    def get_latest_decision(self, project_title: str) -> Optional[Dict[str, Any]]:
        """
        获取项目最新的评估结论
        """
        history = self.get_history(project_title)
        if history:
            return history[-1]
        return None

    def clear(self):
        """
        清空内存中的所有项目记忆
        """
        self._storage.clear()

# 全局内存单例
global_project_memory = ProjectMemory()
