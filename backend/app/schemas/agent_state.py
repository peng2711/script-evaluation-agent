from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from .script import ScriptSubmission
from .report import EvaluationReport, Character, CharacterRelation, PlotEvent, Conflict, RiskPoint, ReferenceWork, ReviewResult

class AgentState(BaseModel):
    script: ScriptSubmission = Field(..., description="输入的剧本/大纲信息")
    parsed_characters: List[Character] = Field(default_factory=list, description="Parser Agent 提取的角色")
    parsed_relations: List[CharacterRelation] = Field(default_factory=list, description="Parser Agent 提取的关系")
    parsed_events: List[PlotEvent] = Field(default_factory=list, description="Parser Agent 提取的剧情事件")
    parsed_conflicts: List[Conflict] = Field(default_factory=list, description="Parser Agent 提取的核心冲突")
    parsed_risks: List[RiskPoint] = Field(default_factory=list, description="Analysis Agent 提取的风险点")
    retrieved_references: List[ReferenceWork] = Field(default_factory=list, description="Retrieval Agent 匹配的相似作品")
    draft_report: Optional[EvaluationReport] = Field(None, description="Analysis Agent 渲染的草稿报告")
    final_report: Optional[EvaluationReport] = Field(None, description="通过审核的最终报告")
    review_result: Optional[ReviewResult] = Field(None, description="Review Agent 审核结论")
    iterations: int = Field(default=0, description="迭代次数")
    history_logs: List[str] = Field(default_factory=list, description="记录各个 Agent 执行步骤和时间戳的日志")
