from pydantic import BaseModel, Field
from typing import Optional, List

class FailureCase(BaseModel):
    case_id: str = Field(..., description="失败案例唯一ID")
    project_id: str = Field(..., description="项目ID")
    trace_id: str = Field(..., description="链路追踪ID")
    failure_type: str = Field(..., description="失败类别")
    failed_node: Optional[str] = Field(None, description="发生失败的 Workflow 节点名称")
    failed_tool: Optional[str] = Field(None, description="发生失败或触发降级的工具名称")
    review_issues: List[str] = Field(default_factory=list, description="相关质检检出的错误详情")
    bad_output_summary: str = Field(..., description="问题输出数据的简短摘要")
    root_cause: str = Field(..., description="失败根本原因分析")
    suggested_fix: str = Field(..., description="建议的迭代修复方案")
