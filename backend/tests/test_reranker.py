import pytest
from app.rag.retriever import mock_reranker
from app.schemas.report import RetrievalEvidence

def test_reranker_match_logic():
    # 模拟从初筛召回的 evidences (TF-IDF 分数均为 0.5)
    evidences = [
        RetrievalEvidence(source_title="流浪地球", source_type="电影", content="科幻大纲", relevance_reason="", score=0.5),
        RetrievalEvidence(source_title="隐秘的角落", source_type="电视剧", content="悬疑大纲", relevance_reason="", score=0.5),
        RetrievalEvidence(source_title="狂飙", source_type="电视剧", content="都市扫黑大纲", relevance_reason="", score=0.5),
    ]
    
    # 1. 题材匹配测试：如果查询包含 "科幻"，流浪地球应排在最前
    query_sci_fi = "科幻 太空 重工业 末日拯救"
    res1 = mock_reranker.rerank(evidences, query=query_sci_fi, top_k=3)
    assert len(res1) == 3
    assert res1[0].source_title == "流浪地球"
    assert "题材匹配=1.0" in res1[0].relevance_reason
    assert res1[0].score > res1[1].score

    # 2. 标签与题材匹配测试：如果查询为悬疑题材并包含 "心理拉扯" 标签
    query_suspense = "悬疑 谋杀 人性 心理拉扯"
    res2 = mock_reranker.rerank(evidences, query=query_suspense, top_k=3)
    assert len(res2) == 3
    assert res2[0].source_title == "隐秘的角落"
    # 隐秘的角落 tags 匹配多，且题材为悬疑
    assert "题材匹配=1.0" in res2[0].relevance_reason
    assert res2[0].score > res2[1].score

def test_rerank_top_k_limiting():
    evidences = [
        RetrievalEvidence(source_title="流浪地球", source_type="电影", content="科幻大纲", relevance_reason="", score=0.5),
        RetrievalEvidence(source_title="隐秘的角落", source_type="电视剧", content="悬疑大纲", relevance_reason="", score=0.5),
        RetrievalEvidence(source_title="狂飙", source_type="电视剧", content="都市扫黑大纲", relevance_reason="", score=0.5),
    ]
    
    # 限制返回数量为 2
    res = mock_reranker.rerank(evidences, query="随便什么题材", top_k=2)
    assert len(res) == 2

def test_rerank_evidence_fields_completeness():
    evidences = [
        RetrievalEvidence(source_title="狂飙", source_type="电视剧", content="都市扫黑大纲", relevance_reason="", score=0.5),
    ]
    
    res = mock_reranker.rerank(evidences, query="狂飙都市双雄博弈", top_k=1)
    assert len(res) == 1
    evidence = res[0]
    
    assert evidence.source_title == "狂飙"
    assert evidence.source_type == "电视剧"
    assert len(evidence.content) > 0
    assert "精排依据" in evidence.relevance_reason
    assert 0.0 <= evidence.score <= 1.0
