from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class CharacterProfile(BaseModel):
    name: str = Field(..., description="人物角色姓名")
    role: str = Field(..., description="角色定位/身份设定")
    personality: List[str] = Field(default_factory=list, description="性格标签列表")
    motivation: Optional[str] = Field(None, description="核心行为动机")
    relationships: Dict[str, str] = Field(default_factory=dict, description="与其他角色的关系，键为对方角色名，值为关系类型说明")
    constraints: List[str] = Field(default_factory=list, description="角色所受的设定约束（防止人设崩塌）")
    evidence_spans: List[str] = Field(default_factory=list, description="剧本原文中支撑人设描写的证据文本片段")

class PlotEvent(BaseModel):
    event_id: str = Field(..., description="核心事件唯一编码")
    summary: str = Field(..., description="剧情事件概要")
    characters: List[str] = Field(default_factory=list, description="参与该事件的人物姓名列表")
    conflict_type: Optional[str] = Field(None, description="冲突类型说明（如家庭伦理冲突、外部追击冲突等）")
    evidence_span: Optional[str] = Field(None, description="支撑该事件发生的原文段落引用")

class ScriptAnalysis(BaseModel):
    characters: List[CharacterProfile] = Field(default_factory=list, description="提取出的角色配置文件列表")
    character_relations: List[str] = Field(default_factory=list, description="人物关系概览描述列表")
    core_conflict: str = Field(..., description="剧本的核心戏剧冲突描述")
    plot_events: List[PlotEvent] = Field(default_factory=list, description="关键剧情事件序列")
    risk_points: List[str] = Field(default_factory=list, description="识别出的立项潜在风险点说明")
    strengths: List[str] = Field(default_factory=list, description="剧本核心亮点/优势维度说明")
    weaknesses: List[str] = Field(default_factory=list, description="剧本的劣势/薄弱环节说明")

class RetrievalEvidence(BaseModel):
    source_title: str = Field(..., description="参考来源作品标题")
    source_type: str = Field(..., description="参考来源类别（如电影、电视剧、网文大纲等）")
    content: str = Field(..., description="参考素材的相关内容/相似事件")
    relevance_reason: str = Field(..., description="被选作证据的相似关联理由说明")
    score: float = Field(..., description="相似关联度分数（0.0 至 1.0 之间）")

class ReviewIssue(BaseModel):
    issue_type: str = Field(..., description="问题类型（如：剧情幻觉、无依据主观评价、人设不一致等）")
    severity: str = Field(..., description="严重级别（如：LOW、MEDIUM、HIGH）")
    claim: str = Field(..., description="报告中的有争议声称/断言")
    reason: str = Field(..., description="被判定为问题的审查原因/反驳证据")
    suggested_fix: str = Field(..., description="推荐的具体整改方案建议")

class NodeTrace(BaseModel):
    node_name: str = Field(..., description="节点名称")
    input_summary: str = Field(..., description="输入数据摘要")
    output_summary: str = Field(..., description="输出数据或状态摘要")
    errors: Optional[str] = Field(None, description="节点执行中的错误说明")
    retry_count: int = Field(default=0, description="当前重试计数")

class FinalReport(BaseModel):
    project_id: str = Field(..., description="项目唯一ID")
    title: str = Field(..., description="项目/剧本标题")
    executive_summary: str = Field(..., description="项目立项辅助评估执行摘要")
    
    # 评分限制在 1-5 分之间
    character_score: int = Field(..., ge=1, le=5, description="人物人设维度评分 (1-5)")
    plot_logic_score: int = Field(..., ge=1, le=5, description="剧情逻辑维度评分 (1-5)")
    conflict_density_score: int = Field(..., ge=1, le=5, description="戏剧冲突密度评分 (1-5)")
    market_fit_score: int = Field(..., ge=1, le=5, description="市场商业潜力维度评分 (1-5)")
    
    evidence_list: List[RetrievalEvidence] = Field(default_factory=list, description="支持评估结论的历史作品/素材库检索证据列表")
    review_issues: List[ReviewIssue] = Field(default_factory=list, description="Review Agent 审查提出的质量整改项")
    decision_suggestion: str = Field(..., description="最终立项辅助建议结论（如 PASS/REVISE/REJECT 等）")
    improvement_suggestions: List[str] = Field(default_factory=list, description="具体的可落地内容优化与修改建议列表")
    node_traces: List[NodeTrace] = Field(default_factory=list, description="执行 Trace 链路记录")
    risk_points: List[str] = Field(default_factory=list, description="识别出的立项潜在风险点说明")
    strengths: List[str] = Field(default_factory=list, description="剧本核心亮点/优势维度说明")
    weaknesses: List[str] = Field(default_factory=list, description="剧本的劣势/薄弱环节说明")
    characters: List[CharacterProfile] = Field(default_factory=list, description="提取出的角色配置文件列表")
    character_relations: List[str] = Field(default_factory=list, description="人物关系概览描述列表")
    core_conflict: str = Field(default="", description="核心戏剧冲突描述")
    trace: Optional[Dict[str, Any]] = Field(None, description="可观测性 Trace 和 Metrics 数据")
