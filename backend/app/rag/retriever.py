import os
import json
from typing import List, Dict, Any
from ..schemas.report import ReferenceWork

class MockRetriever:
    """
    Mock RAG 检索器。从 reference_works.json 加载参考作品，并根据类型和关键词模拟检索。
    """
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.normpath(os.path.join(current_dir, "..", "..", "data", "reference_works.json"))
        self._data: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except Exception:
                self._data = []
        else:
            self._data = []

    def retrieve_similar_works(self, genre: str, content_query: str) -> List[ReferenceWork]:
        """
        根据题材(genre)及内容关键词进行模糊检索，返回匹配度最高的 1-2 部作品。
        """
        # 重新加载数据，防止数据在运行时发生修改而未同步
        self._load_data()

        results = []
        # 1. 优先匹配题材相同或相似的作品
        matched_works = [work for work in self._data if work.get("genre") == genre]
        
        # 2. 如果没有相同题材，返回全部库
        if not matched_works:
            matched_works = self._data

        for work in matched_works[:2]:  # 最多返回2个
            results.append(ReferenceWork(
                title=work.get("title", "未知作品"),
                similarity_reason=f"匹配题材类型：{genre}。该作品在核心冲突 '{work.get('conflicts', ['暂无冲突描述'])[0]}' 上与本项目有较高参考度。",
                benchmark_metric=work.get("benchmark_metric", "暂无参考指标数据")
            ))
        
        return results

# 全局检索器单例
mock_retriever = MockRetriever()
