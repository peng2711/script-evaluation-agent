from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from .script import ScriptInput
from .report import ScriptAnalysis, RetrievalEvidence, ReviewIssue, FinalReport, NodeTrace

class AgentState(BaseModel):
    script: ScriptInput = Field(..., description="输入的剧本大纲与属性配置信息")
    analysis: Optional[ScriptAnalysis] = Field(None, description="Parser Agent 与 Analysis Agent 产出的静态要素分析")
    evidences: List[RetrievalEvidence] = Field(default_factory=list, description="Retrieval Agent 匹配到的对比参照依据列表")
    review_issues: List[ReviewIssue] = Field(default_factory=list, description="Review Agent 审核指出的潜在逻辑/幻觉问题列表")
    draft_report: Optional[FinalReport] = Field(None, description="已生成的初始评估报告草稿")
    final_report: Optional[FinalReport] = Field(None, description="经过审核最终固化的评估报告")
    iterations: int = Field(default=0, description="迭代审核整改次数计数器")
    history_logs: List[str] = Field(default_factory=list, description="记录各个 Agent 执行轨迹的步骤与时间戳日志")
    should_retrieve_more: bool = Field(default=False, description="审查决定：是否需要获取更多参考证据")
    should_rewrite_report: bool = Field(default=False, description="审查决定：是否需要重新撰写/修正评估报告")
    node_traces: List[NodeTrace] = Field(default_factory=list, description="节点执行 Trace 记录")
    trace: Optional[Dict[str, Any]] = Field(None, description="可观测性 Trace 和 Metrics 数据")
