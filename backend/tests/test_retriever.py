import pytest
from app.rag.retriever import MockRetriever
from app.schemas.report import RetrievalEvidence

def test_retriever_suspense_match():
    retriever = MockRetriever()
    query = "一部关于悬疑、犯罪和未成年人心理犯罪的电视剧，讲述张东升杀人案"
    
    evidences = retriever.search_similar_works(query, top_k=2)
    
    assert len(evidences) == 2
    # 评分最高的第一位应该必须是《隐秘的角落》
    best_match = evidences[0]
    assert best_match.source_title == "隐秘的角落"
    assert best_match.source_type == "电视剧"
    # 得分应该由于题材和标签匹配而很高
    assert best_match.score > 0.5
    assert "张东升" in best_match.relevance_reason

def test_retriever_scifi_match():
    retriever = MockRetriever()
    query = "太阳即将毁灭，人类启动流浪计划，遭遇木星引力生死危机的科幻太空电影"
    
    evidences = retriever.search_similar_works(query, top_k=2)
    
    assert len(evidences) == 2
    best_match = evidences[0]
    assert best_match.source_title == "流浪地球"
    assert best_match.source_type == "电影"
    assert best_match.score > 0.5
    assert "流浪地球" in best_match.relevance_reason or "木星" in best_match.relevance_reason

def test_retriever_boundary_empty_query():
    retriever = MockRetriever()
    # 边界测试：空查询或仅包含标点的无意义查询
    query = "，。？！  "
    
    evidences = retriever.search_similar_works(query, top_k=2)
    
    # 不应当崩溃，而是降级返回默认高频对比作品列表，且分数设为 0.0
    assert len(evidences) == 2
    for ev in evidences:
        assert ev.score == 0.0
        assert "空查询" in ev.relevance_reason

def test_retriever_scores_bound():
    retriever = MockRetriever()
    query = "都市商战，安欣和高启强的双雄博弈，扫黑除恶大戏"
    
    evidences = retriever.search_similar_works(query, top_k=3)
    
    # 确认所有检索出的分数都在合法区间 0.0 ~ 1.0 之间
    for ev in evidences:
        assert 0.0 <= ev.score <= 1.0
        assert isinstance(ev, RetrievalEvidence)
