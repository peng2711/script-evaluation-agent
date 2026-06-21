from typing import Dict, List, Any, Optional
from ..schemas.report import CharacterProfile

class CharacterMemory:
    """
    角色/人设设定记忆管理器 (在内存中运行，保证多轮评估中角色人设的连贯性)
    """
    def __init__(self):
        # 键为 project_title, 值为该项目目前确立的人物人设设定库 Dict[character_name, CharacterProfile]
        self._storage: Dict[str, Dict[str, CharacterProfile]] = {}

    def update_character_profile(self, project_title: str, profile: CharacterProfile):
        """
        更新或确立特定项目下的某个角色设定快照
        """
        if project_title not in self._storage:
            self._storage[project_title] = {}
        
        self._storage[project_title][profile.name] = profile

    def get_character_profile(self, project_title: str, name: str) -> Optional[CharacterProfile]:
        """
        根据角色名字获取对应人设背景信息
        """
        return self._storage.get(project_title, {}).get(name)

    def get_all_profiles(self, project_title: str) -> Dict[str, CharacterProfile]:
        """
        获取该项目下的所有设定好的人设
        """
        return self._storage.get(project_title, {})

    def clear(self):
        """
        清空角色库内存
        """
        self._storage.clear()

# 全局内存单例
global_character_memory = CharacterMemory()
