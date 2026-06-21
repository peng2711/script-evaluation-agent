import re

def tokenize(text: str) -> set:
    """
    中文字符及英文单词分词提取（过滤掉常见标点和多余空白）
    """
    clean_text = "".join(re.findall(r"[\u4e00-\u9fa5a-zA-Z0-9]+", text.lower()))
    return set(clean_text)

def jaccard_similarity(set_a: set, set_b: set) -> float:
    """
    计算两个集合的 Jaccard 相似度。
    """
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    return len(set_a.intersection(set_b)) / len(set_a.union(set_b))

def calculate_genre_match_score(work_genre: str, query: str) -> float:
    return 1.0 if work_genre.lower() in query.lower() else 0.0

def calculate_tag_overlap_score(work_tags: list, query: str) -> float:
    if not work_tags:
        return 0.0
    matched_tags = sum(1 for t in work_tags if t.lower() in query.lower())
    return matched_tags / len(work_tags)

def calculate_conflict_similarity_score(work_conflict: str, query_set: set) -> float:
    conflict_set = tokenize(work_conflict)
    return jaccard_similarity(conflict_set, query_set)

def calculate_character_setup_score(work_char_setup: str, query_set: set) -> float:
    char_set = tokenize(work_char_setup)
    return jaccard_similarity(char_set, query_set)

def calculate_final_rerank_score(
    genre_match_score: float,
    tag_overlap_score: float,
    conflict_similarity_score: float,
    character_setup_score: float
) -> float:
    score = (
        0.3 * genre_match_score +
        0.3 * tag_overlap_score +
        0.3 * conflict_similarity_score +
        0.1 * character_setup_score
    )
    return max(0.0, min(1.0, score))
