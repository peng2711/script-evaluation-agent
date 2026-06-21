from pydantic import BaseModel, Field
from typing import List

class ReportQualityScore(BaseModel):
    """
    剧本评估报告规则化质量评分输出模型。
    """
    evidence_score: float = Field(..., description="证据充分性得分 (0-100)")
    structure_score: float = Field(..., description="报告结构完整度得分 (0-100)")
    actionable_score: float = Field(..., description="建议可执行性得分 (0-100)")
    consistency_score: float = Field(..., description="人物和剧情一致性得分 (0-100)")
    risk_coverage_score: float = Field(..., description="风险覆盖度得分 (0-100)")
    final_score: float = Field(..., description="综合质量得分 (0-100)")
    reasons: List[str] = Field(default_factory=list, description="扣分或评分依据原因说明列表")
