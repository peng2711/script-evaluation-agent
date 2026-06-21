from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from ..schemas.report import ScriptAnalysis, RetrievalEvidence, CharacterProfile, FinalReport, ReviewIssue

# 1. Script Parse Tool Schemas
class ScriptParseInput(BaseModel):
    raw_text: str = Field(..., description="剧本正文或大纲文本")

class ScriptParseOutput(BaseModel):
    analysis: ScriptAnalysis = Field(..., description="客观提取出的要素分析")

# 2. Similar Work Search Tool Schemas
class SimilarWorkSearchInput(BaseModel):
    query: str = Field(..., description="检索查询文本（例如剧本大纲、题材及受众描述）")
    top_k: int = Field(default=2, description="返回的相似参考作品数量限制")

class SimilarWorkSearchOutput(BaseModel):
    evidences: List[RetrievalEvidence] = Field(default_factory=list, description="检索到的相似作品证据列表")

# 3. Rerank Tool Schemas
class RerankInput(BaseModel):
    evidences: List[RetrievalEvidence] = Field(..., description="待重排的初筛相似作品证据列表")
    query: str = Field(..., description="用于重排比对的查询文本")
    top_k: int = Field(default=5, description="精排返回的数量上限")

class RerankOutput(BaseModel):
    evidences: List[RetrievalEvidence] = Field(..., description="经过精细重排后的前 Top-k 证据列表")

# 4. Memory Read Tool Schemas
class MemoryReadInput(BaseModel):
    project_id: str = Field(..., description="项目唯一ID")
    memory_type: str = Field(..., description="记忆库类别，可选值：'project' 或 'character'")

class MemoryReadOutput(BaseModel):
    project_report: Optional[FinalReport] = Field(None, description="读取出的最终项目评估报告")
    characters: Optional[List[CharacterProfile]] = Field(None, description="读取出的项目角色人设配置列表")

# 5. Memory Write Tool Schemas
class MemoryWriteInput(BaseModel):
    project_id: str = Field(..., description="项目唯一ID")
    memory_type: str = Field(..., description="记忆库类别，可选值：'project' 或 'character'")
    project_report: Optional[FinalReport] = Field(None, description="需要写入的项目评估报告")
    characters: Optional[List[CharacterProfile]] = Field(None, description="需要写入的项目角色人设配置列表")

class MemoryWriteOutput(BaseModel):
    success: bool = Field(..., description="写入操作是否成功")
    message: str = Field(..., description="写入操作结果说明")

# 6. Review Check Tool Schemas
class ReviewCheckInput(BaseModel):
    script_title: str = Field(..., description="剧本/项目标题")
    script_genre: str = Field(..., description="剧本题材分类")
    raw_text: str = Field(..., description="剧本正文或大纲文本")
    analysis: ScriptAnalysis = Field(..., description="Parser 提取的客观要素")
    project_id: str = Field(..., description="项目唯一ID")
    evidences: List[RetrievalEvidence] = Field(default_factory=list, description="检索出的参考作品证据")
    draft_report: FinalReport = Field(..., description="待质检的草稿报告")

class ReviewCheckOutput(BaseModel):
    issues: List[ReviewIssue] = Field(default_factory=list, description="审查发现的合规/质量缺陷列表")
