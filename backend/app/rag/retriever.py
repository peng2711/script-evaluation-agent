import os
import json
from typing import List, Dict, Any
from ..schemas.report import RetrievalEvidence

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

    def retrieve_similar_works(self, genre: str, content_query: str) -> List[RetrievalEvidence]:
        """
        根据题材(genre)进行检索，返回匹配度最高的 1-2 部作品并包装为 RetrievalEvidence。
        """
        self._load_data()

        results = []
        # 1. 优先匹配题材相同或相似的作品
        matched_works = [work for work in self._data if work.get("genre") == genre]
        
        # 2. 如果没有相同题材，返回全部库
        if not matched_works:
            matched_works = self._data

        for idx, work in enumerate(matched_works[:2]):  # 最多返回2个
            # 模拟一个匹配度得分
            score = 0.95 - (idx * 0.1)
            results.append(RetrievalEvidence(
                source_title=work.get("title", "未知作品"),
                source_type="电视剧" if genre != "科幻" else "电影",
                content=work.get("description", "暂无详情描述"),
                relevance_reason=f"匹配题材：{genre}。两者在戏剧冲突 '{work.get('conflicts', ['暂无核心冲突'])[0]}' 的展现方式上具有高度相似度。",
                score=score
            ))
        
        return results

# 全局检索器单例
mock_retriever = MockRetriever()
