import os
import json
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

class ProjectMemoryStore:
    """
    项目级别记忆管理器：通过本地 JSON 文件持久化存储每个项目的评估报告。
    存储路径：backend/storage/project_memory.json
    """
    def __init__(self, filepath: Optional[str] = None):
        if filepath:
            self.filepath = filepath
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.filepath = os.path.normpath(os.path.join(current_dir, "..", "..", "storage", "project_memory.json"))
        
        # 确保存储目录存在
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)

    def _read_file(self) -> Dict[str, Dict[str, Any]]:
        if not os.path.exists(self.filepath):
            return {}
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _write_file(self, data: Dict[str, Dict[str, Any]]):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save_project(self, project_id: str, project_summary: Any):
        """
        保存整个项目评估报告（支持 dict 或 Pydantic 结构模型）
        """
        data = self._read_file()
        
        # 兼容 Pydantic 模型
        if isinstance(project_summary, BaseModel):
            summary_dict = project_summary.model_dump()
        else:
            summary_dict = dict(project_summary)
            
        data[project_id] = summary_dict
        self._write_file(data)

    def load_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        读取项目，如果不存在则返回 None
        """
        data = self._read_file()
        return data.get(project_id)

    def update_project(self, project_id: str, fields: Dict[str, Any]):
        """
        局部更新项目报告的特定字段
        """
        data = self._read_file()
        if project_id in data:
            data[project_id].update(fields)
            self._write_file(data)
        else:
            # 如果不存在，抛出异常或静默忽略？单元测试需要测试“更新”，我们通常抛出 KeyError
            raise KeyError(f"Project with ID '{project_id}' does not exist.")

    def list_projects(self) -> List[Dict[str, Any]]:
        """
        列出所有已评估的项目总结报告
        """
        data = self._read_file()
        return list(data.values())

    def clear(self):
        """
        清空持久化文件中的全部项目记忆
        """
        self._write_file({})

# 全局项目持久化记忆单例
global_project_memory = ProjectMemoryStore()
