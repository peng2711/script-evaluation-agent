import os
import json
from typing import Dict, Any, List

def ingest_work(work: Dict[str, Any]):
    """
    向 mock reference_works.json 注册/导入一部新的对比参考作品
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.normpath(os.path.join(current_dir, "..", "..", "data", "reference_works.json"))
    
    # 确保目录存在
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
    # 简单测试导入
    sample_work = {
        "title": "回响",
        "genre": "悬疑",
        "description": "女警冉咚咚在侦破凶案的过程中，同时面临着对自己婚姻与丈夫忠诚度的审查。",
        "conflicts": [
            "冉咚咚对案件真相的执着追求与案情重重迷雾的冲突",
            "冉咚咚内心的信任危机与情感猜疑"
        ],
        "key_risks": [
            "心理独白较多，影视化视觉呈现难度高",
            "悬疑探案与情感双线交织，处理不好容易导致节奏拖沓"
        ],
        "benchmark_metric": "冯小刚导演网剧，探讨人性深度，获得了一定圈层的高热度讨论"
    }
    ingest_work(sample_work)
    print(f"成功将作品 '{sample_work['title']}' 导入知识库。")
