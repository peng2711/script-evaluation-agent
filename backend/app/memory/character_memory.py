import os
import json
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

class CharacterMemoryStore:
    """
    角色人设记忆管理器：通过本地 JSON 文件持久化存储每个项目的角色设定。
    存储路径：backend/storage/character_memory.json
    """
    def __init__(self, filepath: Optional[str] = None):
        if filepath:
            self.filepath = filepath
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.filepath = os.path.normpath(os.path.join(current_dir, "..", "..", "storage", "character_memory.json"))
        
        # 确保存储目录存在
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)

    def _read_file(self) -> Dict[str, List[Dict[str, Any]]]:
        if not os.path.exists(self.filepath):
            return {}
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _write_file(self, data: Dict[str, List[Dict[str, Any]]]):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save_characters(self, project_id: str, characters: List[Any]):
        """
        保存特定项目抽取出的全部角色人设列表（支持 CharacterProfile 列表）
        """
        data = self._read_file()
        
        serialized_list = []
        for char in characters:
            if isinstance(char, BaseModel):
                serialized_list.append(char.model_dump())
            else:
                serialized_list.append(dict(char))
                
        data[project_id] = serialized_list
        self._write_file(data)

    def load_characters(self, project_id: str) -> List[Dict[str, Any]]:
        """
        加载项目下的角色人设库，不存在则返回空列表 []
        """
        data = self._read_file()
        return data.get(project_id, [])

    def update_character(self, project_id: str, character_name: str, fields: Dict[str, Any]):
        """
        更新特定项目下指定名字角色的属性
        """
        data = self._read_file()
        if project_id in data:
            characters_list = data[project_id]
            found = False
            for char in characters_list:
                if char.get("name") == character_name:
                    char.update(fields)
                    found = True
                    break
            if not found:
                raise KeyError(f"Character '{character_name}' not found in project '{project_id}'.")
            self._write_file(data)
        else:
            raise KeyError(f"Project with ID '{project_id}' does not exist in character memory.")

    def clear(self):
        """
        清空持久化文件中的全部角色记忆
        """
        self._write_file({})

# 全局角色持久化记忆单例
global_character_memory = CharacterMemoryStore()
