import pytest
from app.agents.parser_agent import ParserAgent
from app.schemas.report import ScriptAnalysis

def test_parser_agent_contract_marriage_case():
    agent = ParserAgent()
    text = (
        "女主林晚是林家的后代。\n"
        "男主沈知行是沈氏集团的总裁。\n"
        "因为林晚和沈知行达成协议，两人契约婚姻，掩人耳目。\n"
        "女主林晚为了查清父亲死亡真相复仇，开始利用沈氏集团的资源收集当年的证据。"
    )
    
    # 提取事实
    analysis: ScriptAnalysis = agent.extract(text)
    
    # 验证抽取出的角色
    character_names = [char.name for char in analysis.characters]
    assert "林晚" in character_names
    assert "沈知行" in character_names
    
    # 验证女主角属性
    lin_wan = next(char for char in analysis.characters if char.name == "林晚")
    assert lin_wan.role == "女主角"
    assert "复仇" in lin_wan.motivation
    assert lin_wan.relationships.get("沈知行") == "契约婚姻"
    
    # 验证关系列表
    assert any("契约婚姻" in rel for rel in analysis.character_relations)
    
    # 验证冲突抽取
    assert "复仇" in analysis.core_conflict
    assert "父亲死亡真相" in analysis.core_conflict

def test_parser_agent_paragraph_chunking():
    agent = ParserAgent()
    text = "第一段文字。\n\n第二段文字，有较多空格。    \n第三段文字包含林晚。"
    
    paragraphs = agent._split_into_paragraphs(text)
    assert len(paragraphs) == 3
    assert paragraphs[0] == "第一段文字。"
    assert paragraphs[1] == "第二段文字，有较多空格。"
    assert paragraphs[2] == "第三段文字包含林晚。"
    
    # 验证抽取时的原文证据匹配
    analysis = agent.extract(text)
    lin_wan_char = next(char for char in analysis.characters if char.name == "林晚")
    assert lin_wan_char.evidence_spans == ["第三段文字包含林晚。"]

def test_parser_agent_no_subjective_evaluations():
    agent = ParserAgent()
    # 无论输入多么带主观评价性，ParserAgent都应将主观字段保持为空，只抽取事实
    text = "女主林晚为了查清父亲死亡真相复仇。这部剧具有极高市场潜力，但后续剧情节奏拖沓，立意有些老套。"
    
    analysis = agent.extract(text)
    
    # 1. 验证主观分析属性全部为空列表
    assert analysis.risk_points == []
    assert analysis.strengths == []
    assert analysis.weaknesses == []
    
    # 2. 检查抽取出的事实人设中，性格和动机不含有主观审判的词汇
    lin_wan = analysis.characters[0]
    subjective_words = ["市场潜力", "商业潜力", "节奏拖沓", "老套", "无脑"]
    
    for word in subjective_words:
        # 确保性格中不含主观评价
        for trait in lin_wan.personality:
            assert word not in trait
        # 确保动机中不含主观评价
        if lin_wan.motivation:
            assert word not in lin_wan.motivation
