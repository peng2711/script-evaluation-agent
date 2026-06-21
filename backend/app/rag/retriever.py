import os
import json
import re
import math
from typing import List, Dict, Any, Optional
from ..schemas.report import RetrievalEvidence

class MockRetriever:
    """
    轻量级中文字符级 TF-IDF 本地 RAG 检索器。
    从 reference_works.json 加载素材数据，并支持题材 (genre) / 标签 (tags) / 核心冲突 (core_conflict) 混合匹配检索。
    """
    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            self.db_path = db_path
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.db_path = os.path.normpath(os.path.join(current_dir, "..", "..", "data", "reference_works.json"))
        
        self._data: List[Dict[str, Any]] = []
        self.idf: Dict[str, float] = {}
        self.work_sets: List[set] = []
        
        self._load_data()
        self._build_index()

    def _load_data(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except Exception:
                self._data = []
        else:
            self._data = []

    def _tokenize(self, text: str) -> set:
        """
        中文字符及英文单词分词提取（过滤掉常见标点和多余空白）
        """
        # 保留汉字、英文字母和数字
        clean_text = "".join(re.findall(r"[\u4e00-\u9fa5a-zA-Z0-9]+", text.lower()))
        return set(clean_text)

    def _build_index(self):
        """
        计算语料库中的所有词（字）的逆文档频率 (IDF) 权重
        """
        self.work_sets = []
        if not self._data:
            return

        # 1. 提取每部作品的代表性文本集合 (合并题材、大纲、标签和冲突)
        for work in self._data:
            text_parts = [
                work.get("genre", ""),
                work.get("synopsis", ""),
                " ".join(work.get("tags", [])),
                work.get("character_setup", ""),
                work.get("core_conflict", "")
            ]
            combined_text = " ".join(text_parts)
            self.work_sets.append(self._tokenize(combined_text))

        # 2. 计算 IDF
        total_docs = len(self._data)
        doc_counts: Dict[str, int] = {}
        
        # 统计每个字出现的文档数
        for word_set in self.work_sets:
            for char in word_set:
                doc_counts[char] = doc_counts.get(char, 0) + 1
                
        # 计算 IDF 权重
        for char, count in doc_counts.items():
            self.idf[char] = math.log(total_docs / (count + 0.5)) + 0.5

    def search_similar_works(self, query: str, top_k: int = 2) -> List[RetrievalEvidence]:
        """
        根据 query 混合匹配题材、标签、核心冲突，计算 TF-IDF 字符级余弦相似度 + 题材与标签权重 Boost 奖励分。
        返回包装好的 RetrievalEvidence 列表。
        """
        # 实时重新加载数据与重建索引，防写入新数据后未同步
        self._load_data()
        self._build_index()

        if not self._data:
            return []

        query_set = self._tokenize(query)
        if not query_set:
            # 边界情况：若 query 为空，返回默认前 top_k 部作品，且相似度为 0.0
            return [
                RetrievalEvidence(
                    source_title=work.get("title", "默认对比作品"),
                    source_type="电视剧" if work.get("genre") != "科幻" else "电影",
                    content=work.get("synopsis", "暂无详情"),
                    relevance_reason="空查询默认推荐。",
                    score=0.0
                )
                for work in self._data[:top_k]
            ]

        results = []

        # 计算查询的 TF-IDF 模长
        query_norm = math.sqrt(sum(self.idf.get(char, 1.0)**2 for char in query_set))

        for idx, work in enumerate(self._data):
            work_set = self.work_sets[idx]
            
            # 计算交叉字的余弦相似度分值
            intersection = query_set.intersection(work_set)
            if intersection and query_norm > 0:
                work_norm = math.sqrt(sum(self.idf.get(char, 1.0)**2 for char in work_set))
                dot_product = sum(self.idf.get(char, 1.0)**2 for char in intersection)
                cosine_sim = dot_product / (query_norm * work_norm)
            else:
                cosine_sim = 0.0

            # --- Boost 奖励规则设计 ---
            genre_boost = 0.0
            tag_boost = 0.0
            
            # 题材完美契合奖励
            genre = work.get("genre", "")
            if genre and genre in query:
                genre_boost = 0.4
                
            # 标签重合奖励
            for tag in work.get("tags", []):
                if tag in query:
                    tag_boost += 0.1
            tag_boost = min(tag_boost, 0.3)  # 标签最高奖励 0.3

            # 综合评分，限制在 0.0 ~ 1.0 之间
            final_score = (cosine_sim * 0.3) + genre_boost + tag_boost
            final_score = min(final_score, 1.0)

            # 整理匹配理由（提供证据解释，而非剽窃判定）
            relevance_reason = ""
            matched_aspects = []
            if genre_boost > 0:
                matched_aspects.append(f"题材类型 '{genre}' 一致")
            if tag_boost > 0:
                matched_aspects.append("标签特征存在重合")
            if cosine_sim > 0.05:
                matched_aspects.append("大纲描述存在部分语义重合点")
                
            aspects_desc = "、".join(matched_aspects) if matched_aspects else "匹配度较低"
            relevance_reason = f"经检索辅助匹配，本项目与《{work['title']}》在【{aspects_desc}】。该参考作品核心冲突为: '{work.get('core_conflict', '未知')}'; 人设架构: '{work.get('character_setup', '未知')}'，可作为商业对标和结构参考依据。"

            results.append({
                "work": work,
                "score": final_score,
                "reason": relevance_reason
            })

        # 按照评分倒序排序，截取前 top_k 个
        results.sort(key=lambda x: x["score"], reverse=True)
        
        evidence_list = []
        for item in results[:top_k]:
            w = item["work"]
            evidence_list.append(RetrievalEvidence(
                source_title=w["title"],
                source_type="电影" if w.get("genre") == "科幻" else "电视剧",
                content=w["synopsis"],
                relevance_reason=item["reason"],
                score=round(item["score"], 4)
            ))
            
        return evidence_list

# 全局单例检索器
mock_retriever = MockRetriever()
