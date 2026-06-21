from typing import Dict, List, Any, Optional

class CharacterMemory:
    """
    角色/人设设定记忆管理器 (在内存中运行，保证多轮评估中角色性格、身份以及核心人设设定的一致性)
    """
    def __init__(self):
        # 键为 project_title, 值为该项目目前确立的人物人设设定库 Dict[character_name, character_profile]
        self._storage: Dict[str, Dict[str, Dict[str, Any]]] = {}

    def update_character_profile(self, project_title: str, name: str, role: str, description: str):
        """
        更新或确立特定项目下的某个角色设定快照
        """
        if project_title not in self._storage:
            self._storage[project_title] = {}
        
        self._storage[project_title][name] = {
            "name": name,
            "role": role,
            "description": description
        }

    def get_character_profile(self, project_title: str, name: str) -> Optional[Dict[str, Any]]:
        """
        根据角色名字获取对应人设背景信息
        """
        return self._storage.get(project_title, {}).get(name)

    def get_all_profiles(self, project_title: str) -> Dict[str, Dict[str, Any]]:
        """
        获取该项目下的所有设定好的人设
        """
        return self._storage.get(project_title, {})

    def clear(self):
        """
        清空角色库内存
        """
        self._storage.clear()

# 全局内存单例，保证多轮评估或多节点评估中的人设一致性校验
global_character_memory = CharacterMemory()
