from typing import List
from ..schemas.report import RetrievalEvidence
from .scoring import (
    tokenize,
    calculate_genre_match_score,
    calculate_tag_overlap_score,
    calculate_conflict_similarity_score,
    calculate_character_setup_score,
    calculate_final_rerank_score
)

class Reranker:
    """
    负责对召回的相似作品候选进行二次多维度加权精细重排（Rerank）。
    """
    def rerank(self, evidences: List[RetrievalEvidence], query: str, top_k: int = 5) -> List[RetrievalEvidence]:
        # Collect and sort candidate titles to make cache key unique of candidates list
        candidate_titles = []
        for ev in evidences:
            title = ev.source_title if hasattr(ev, "source_title") else ev.get("source_title")
            candidate_titles.append(title)
        candidate_titles.sort()
        
        import hashlib
        from ..cache.simple_cache import global_cache
        
        candidates_str = ",".join(candidate_titles)
        raw_key = f"rerank:{query}:{candidates_str}"
        cache_key = f"reranker:{hashlib.md5(raw_key.encode('utf-8')).hexdigest()}"
        
        cached_result = global_cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        from .retriever import mock_retriever
        # 建立标题到详情的数据库映射
        works_db = {w["title"]: w for w in mock_retriever._data}

        query_set = tokenize(query)
        
        reranked_evidences = []
        for ev in evidences:
            # 支持 dict 或对象格式以确保兼容性
            title = ev.source_title if hasattr(ev, "source_title") else ev.get("source_title")
            work = works_db.get(title)
            if not work:
                # 找不到详情时，原样退回原证据
                reranked_evidences.append(ev)
                continue
                
            genre_match_score = calculate_genre_match_score(work.get("genre", ""), query)
            tag_overlap_score = calculate_tag_overlap_score(work.get("tags", []), query)
            conflict_similarity_score = calculate_conflict_similarity_score(work.get("core_conflict", ""), query_set)
            character_setup_score = calculate_character_setup_score(work.get("character_setup", ""), query_set)
            
            final_score = calculate_final_rerank_score(
                genre_match_score,
                tag_overlap_score,
                conflict_similarity_score,
                character_setup_score
            )
            
            relevance_reason = (
                f"【精排依据】与《{work['title']}》对标：题材匹配={genre_match_score:.1f}，"
                f"标签重合度={tag_overlap_score:.2f}，核心冲突重合={conflict_similarity_score:.2f}，"
                f"人设重合={character_setup_score:.2f}。综合推荐分={final_score:.2f}。"
            )
            
            source_type = ev.source_type if hasattr(ev, "source_type") else ev.get("source_type")
            content = ev.content if hasattr(ev, "content") else ev.get("content")
            
            updated_ev = RetrievalEvidence(
                source_title=title,
                source_type=source_type,
                content=content,
                relevance_reason=relevance_reason,
                score=round(final_score, 4)
            )
            reranked_evidences.append(updated_ev)
            
        # 按照精排总分降序排序
        reranked_evidences.sort(key=lambda x: x.score, reverse=True)
        final_result = reranked_evidences[:top_k]
        
        # 存入缓存
        global_cache.set(cache_key, final_result)
        return final_result

# 全局单例重排器
mock_reranker = Reranker()
