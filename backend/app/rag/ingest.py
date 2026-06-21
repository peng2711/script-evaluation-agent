import os
import json
from typing import Dict, Any, List

def ingest_work(work: Dict[str, Any]):
    """
    向 mock reference_works.json 注册/导入一部新的对比参考作品。
    支持字段：title, genre, synopsis, tags, character_setup, core_conflict
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.normpath(os.path.join(current_dir, "..", "..", "data", "reference_works.json"))
    
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    data: List[Dict[str, Any]] = []
    if os.path.exists(db_path):
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = []

    # 检查是否重复
    exists = False
    for item in data:
        if item.get("title") == work.get("title"):
            item.update(work)
            exists = True
            break
            
    if not exists:
        data.append(work)
        
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    sample_work = {
        "title": "回响",
        "genre": "悬疑",
        "synopsis": "女警冉咚咚在侦破凶案的过程中，面临对自己婚姻和情感忠诚度的拷问与救赎。",
        "tags": ["悬疑", "心理", "情感折磨"],
        "character_setup": "对案件侦破具有极端偏执追求的女警冉咚咚，和其涉嫌情感出轨的文学教授丈夫。",
        "core_conflict": "冉咚咚对杀人命案真相的侦破执念，与其面临的情感猜疑与信任危机之间的重重冲突。"
    }
    ingest_work(sample_work)
    print(f"成功将作品 '{sample_work['title']}' 导入知识库。")
