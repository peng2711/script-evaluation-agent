from typing import List, Type, Any, Dict, Optional
from .base import BaseTool
from .tool_schemas import (
    ScriptParseInput, ScriptParseOutput,
    SimilarWorkSearchInput, SimilarWorkSearchOutput,
    RerankInput, RerankOutput,
    MemoryReadInput, MemoryReadOutput,
    MemoryWriteInput, MemoryWriteOutput,
    ReviewCheckInput, ReviewCheckOutput
)
from ..schemas.report import CharacterProfile, FinalReport, RetrievalEvidence, ScriptAnalysis

class ScriptParseTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="script_parse_tool",
            description="从剧本正文或大纲文本中提取客观要素结构（角色、关系、冲突和主要事件段落）。",
            input_schema=ScriptParseInput,
            output_schema=ScriptParseOutput,
            allowed_agents=["ParserAgent"]
        )

    def run(self, raw_text: str) -> ScriptParseOutput:
        from ..agents.parser_agent import parser_agent
        analysis = parser_agent.extract(raw_text)
        return ScriptParseOutput(analysis=analysis)

class SimilarWorkSearchTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="similar_work_search_tool",
            description="在本地知识库中基于题材和受众特征检索出相似的对比作品。",
            input_schema=SimilarWorkSearchInput,
            output_schema=SimilarWorkSearchOutput,
            allowed_agents=["RetrievalAgent"]
        )

    def run(self, query: str, top_k: int = 2) -> SimilarWorkSearchOutput:
        from ..rag.retriever import mock_retriever
        evidences = mock_retriever.search_similar_works(query, top_k=top_k)
        return SimilarWorkSearchOutput(evidences=evidences)

class RerankTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="rerank_tool",
            description="对召回的对标作品依据冲突和角色匹配度等特征进行精细重排。",
            input_schema=RerankInput,
            output_schema=RerankOutput,
            allowed_agents=["RetrievalAgent"]
        )

    def run(self, evidences: List[RetrievalEvidence], query: str, top_k: int = 5) -> RerankOutput:
        from ..rag.retriever import mock_reranker
        reranked = mock_reranker.rerank(evidences, query, top_k=top_k)
        return RerankOutput(evidences=reranked)

class MemoryReadTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="memory_read_tool",
            description="读取持久化项目评估历史报告或角色配置表信息。",
            input_schema=MemoryReadInput,
            output_schema=MemoryReadOutput,
            allowed_agents=["AnalysisAgent", "ReviewAgent"]
        )

    def run(self, project_id: str, memory_type: str) -> MemoryReadOutput:
        from ..memory.project_memory import global_project_memory
        from ..memory.character_memory import global_character_memory
        
        if memory_type == "project":
            report_dict = global_project_memory.load_project(project_id)
            if report_dict:
                report = FinalReport.model_validate(report_dict)
                return MemoryReadOutput(project_report=report)
            return MemoryReadOutput(project_report=None)
            
        elif memory_type == "character":
            chars_dict = global_character_memory.load_characters(project_id)
            chars = [CharacterProfile.model_validate(c) for c in chars_dict]
            return MemoryReadOutput(characters=chars)
            
        else:
            raise ValueError(f"不合法的 memory_type: '{memory_type}'，期望为 'project' 或 'character'。")

class MemoryWriteTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="memory_write_tool",
            description="将最终报告或角色提取配置写入持久化记忆库。",
            input_schema=MemoryWriteInput,
            output_schema=MemoryWriteOutput,
            allowed_agents=["Workflow", "ParserAgent"]
        )

    def run(
        self,
        project_id: str,
        memory_type: str,
        project_report: Optional[FinalReport] = None,
        characters: Optional[List[CharacterProfile]] = None
    ) -> MemoryWriteOutput:
        from ..memory.project_memory import global_project_memory
        from ..memory.character_memory import global_character_memory
        
        if memory_type == "project":
            if not project_report:
                return MemoryWriteOutput(success=False, message="写入失败：缺少 project_report 参数")
            global_project_memory.save_project(project_id, project_report)
            return MemoryWriteOutput(success=True, message="项目最终报告成功存档。")
            
        elif memory_type == "character":
            if not characters:
                return MemoryWriteOutput(success=False, message="写入失败：缺少 characters 参数")
            global_character_memory.save_characters(project_id, characters)
            return MemoryWriteOutput(success=True, message="项目角色人设统一配置成功存档。")
            
        else:
            raise ValueError(f"不合法的 memory_type: '{memory_type}'，期望为 'project' 或 'character'。")

class ReviewCheckTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="review_check_tool",
            description="独立复核评估报告，发现幻觉和不合规质量问题并打回重整。",
            input_schema=ReviewCheckInput,
            output_schema=ReviewCheckOutput,
            allowed_agents=["ReviewAgent"]
        )

    def run(
        self,
        script_title: str,
        script_genre: str,
        raw_text: str,
        analysis: ScriptAnalysis,
        project_id: str,
        evidences: List[RetrievalEvidence],
        draft_report: FinalReport
    ) -> ReviewCheckOutput:
        from ..agents.review_agent import review_agent
        issues = review_agent.review(
            script_title=script_title,
            script_genre=script_genre,
            raw_text=raw_text,
            analysis=analysis,
            project_id=project_id,
            evidences=evidences,
            draft_report=draft_report,
            use_tools_via_router=True
        )
        return ReviewCheckOutput(issues=issues)


class ToolRegistry:
    """
    系统工具注册表管理器。
    """
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register_tool(self, tool: BaseTool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"工具 '{tool.name}' 已注册，不得重复注册。")
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> BaseTool:
        if name not in self._tools:
            raise KeyError(f"未找到名称为 '{name}' 的已注册工具。")
        return self._tools[name]

    def list_tools(self) -> List[BaseTool]:
        return list(self._tools.values())

    def list_tools_for_agent(self, agent_name: str) -> List[BaseTool]:
        """
        列出指定 Agent 拥有调用权限的工具。
        注意：Workflow 拥有全局最高权限，允许调用所有工具。
        """
        if agent_name == "Workflow":
            return self.list_tools()
        return [t for t in self._tools.values() if agent_name in t.allowed_agents]

# 全局工具注册中心单例
global_tool_registry = ToolRegistry()
global_tool_registry.register_tool(ScriptParseTool())
global_tool_registry.register_tool(SimilarWorkSearchTool())
global_tool_registry.register_tool(RerankTool())
global_tool_registry.register_tool(MemoryReadTool())
global_tool_registry.register_tool(MemoryWriteTool())
global_tool_registry.register_tool(ReviewCheckTool())
