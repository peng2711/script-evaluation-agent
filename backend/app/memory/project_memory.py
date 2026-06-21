from typing import Dict, List, Any, Optional

class ProjectMemory:
    """
    项目级别记忆管理器 (在内存中运行，为多轮立项评估提供历史上下文与决策演变记录)
    """
    def __init__(self):
        # 键为 project_title, 值为该项目历史多次评估报告的简要摘要和立项建议
        self._storage: Dict[str, List[Dict[str, Any]]] = {}

    def add_evaluation_record(self, project_title: str, script_id: str, conclusion: str, summary: str):
        """
        向项目记忆中添加一条评估快照记录
        """
        if project_title not in self._storage:
            self._storage[project_title] = []
        
        self._storage[project_title].append({
            "script_id": script_id,
            "conclusion": conclusion,
            "summary": summary
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

# 全局内存单例，保证在多轮请求中保留项目评估轨迹
global_project_memory = ProjectMemory()
