from pydantic import BaseModel, Field
from typing import Optional, List

class FeedbackInput(BaseModel):
    project_id: str = Field(..., description="项目ID")
    report_id: str = Field(..., description="评估报告ID")
    trace_id: str = Field(..., description="追踪链路ID")
    helpful: bool = Field(..., description="报告整体是否有用")
    evidence_accurate: bool = Field(..., description="引用的证据是否准确")
    suggestion_actionable: bool = Field(..., description="修改建议是否可落地")
    wrong_claims: List[str] = Field(default_factory=list, description="报告中不准确的评价或内容声明列表")
    user_comment: Optional[str] = Field(None, description="用户详细评论或备注")
