from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class RoleType(str, Enum):
    PROTAGONIST = "主角"
    ANTAGONIST = "反派"
    SUPPORTING = "配角"
    OTHER = "其他"

class SeverityType(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class DecisionType(str, Enum):
    PASS = "PASS"
    REVISE = "REVISE"
    REJECT = "REJECT"

class Character(BaseModel):
    name: str = Field(..., description="角色姓名")
    role: RoleType = Field(default=RoleType.OTHER, description="角色定位")
    description: str = Field(..., description="人设描述与主要背景")

class CharacterRelation(BaseModel):
    source_character: str = Field(..., description="源角色姓名")
    target_character: str = Field(..., description="目标角色姓名")
    relation_type: str = Field(..., description="关系类型，例如：夫妻、师徒、敌对、盟友")
    description: str = Field(..., description="关系背景的详细说明")

class PlotEvent(BaseModel):
    title: str = Field(..., description="核心事件标题")
    description: str = Field(..., description="事件详情描述")
    significance: str = Field(..., description="该事件在整体剧情/结构中的关键作用")

class Conflict(BaseModel):
    description: str = Field(..., description="核心冲突/矛盾的描述")
    characters_involved: List[str] = Field(default_factory=list, description="涉及的主要人物")

class RiskPoint(BaseModel):
    category: str = Field(..., description="风险类别，如：政策审核、市场同质化、制作成本超支等")
    description: str = Field(..., description="风险点具体表现形式")
    severity: SeverityType = Field(default=SeverityType.LOW, description="严重程度，分为 LOW、MEDIUM、HIGH")

class ReferenceWork(BaseModel):
    title: str = Field(..., description="相似作品名称")
    similarity_reason: str = Field(..., description="被选为参考的相似原因/对比维度")
    benchmark_metric: str = Field(..., description="参考指标（如：票房表现、口碑评分、制作投入对比等）")

class ReviewResult(BaseModel):
    is_passed: bool = Field(..., description="报告是否通过 Review 校验")
    findings: List[str] = Field(default_factory=list, description="不合规发现（若有），如剧情幻觉、无证据评价等")
    revision_suggestions: List[str] = Field(default_factory=list, description="给 Analysis Agent 的具体修改建议")

class EvaluationReport(BaseModel):
    script_id: str = Field(..., description="系统生成的剧本评估ID")
    title: str = Field(..., description="剧本名称")
    genre: Optional[str] = Field(None, description="题材类别")
    characters: List[Character] = Field(default_factory=list, description="抽取出的核心人物列表")
    relations: List[CharacterRelation] = Field(default_factory=list, description="人物关系网络")
    events: List[PlotEvent] = Field(default_factory=list, description="关键剧情事件")
    conflicts: List[Conflict] = Field(default_factory=list, description="核心戏剧冲突")
    risks: List[RiskPoint] = Field(default_factory=list, description="立项潜在风险点")
    references: List[ReferenceWork] = Field(default_factory=list, description="同类参考作品")
    review: ReviewResult = Field(..., description="Review Agent 审核结论")
    conclusion: DecisionType = Field(..., description="最终立项建议建议结论")
    summary: str = Field(..., description="立项辅助评估综合总结")
