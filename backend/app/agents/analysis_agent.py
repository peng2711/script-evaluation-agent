from ..schemas.agent_state import AgentState
from ..schemas.report import EvaluationReport, RiskPoint, SeverityType, DecisionType, ReviewResult
import datetime
import uuid

class AnalysisAgent:
    """
    Analysis Agent (Mock 实现)：对解析结果进行多维度评估，并结合检索的同类参考作品，产生初始立项评估报告草稿。
    """
    def execute(self, state: AgentState) -> AgentState:
        state.history_logs.append(f"[{datetime.datetime.now().isoformat()}] AnalysisAgent 开始生成草稿评估报告。")
        
        title = state.script.title
        genre = state.script.genre or "通用"
        content = state.script.content
        
        # 1. 模拟根据题材与内容评估风险点
        risks = []
        conclusion = DecisionType.REVISE
        summary = ""
        
        if "林啸" in content:
            risks = [
                RiskPoint(category="政策审核", description="剧情中主角涉及未成年时的极端创伤行为描写，审查尺度较严，需要合理规避敏感血腥画面。", severity=SeverityType.MEDIUM),
                RiskPoint(category="制作成本", description="动作戏占比高达 45%，包含大量追车与爆破场景，对动作特技导演与现场调度安全要求高。", severity=SeverityType.HIGH)
            ]
            # 如果是第1次生成，故意设计一个不合格的结论，让 ReviewAgent 纠错。如果是第2次（修改后），则调整为合格。
            if state.iterations == 0:
                conclusion = DecisionType.PASS
                summary = "（草稿阶段）该项目人设新颖，节奏明快，极具爆款潜质，建议直接立项推进开发。" # 这是一个故意不写风险的过于主观结论，用来测试 ReviewAgent 的纠错
            else:
                conclusion = DecisionType.REVISE
                summary = "（已根据 Review 修改）本项目特工复仇题材动作张力大，商业看点足。但由于动作戏占比过高及部分敏感画面，建议在二稿中压缩15%的爆破动作戏以控制预算，并对林啸过去的心理创伤描写进行温和化修改后，予以立项通过。"
        elif "陈默" in content:
            risks = [
                RiskPoint(category="市场同质化", description="都市商战题材与非遗文化结合较新颖，但商战核心套路（恶意收购、逆袭）市场较为常见，需做出差异化。", severity=SeverityType.LOW),
                RiskPoint(category="受众画像偏差", description="商战受众偏男性/成熟期，非遗茶文化受众偏佛系/年轻化，两类人群融合有一定壁垒。", severity=SeverityType.MEDIUM)
            ]
            if state.iterations == 0:
                conclusion = DecisionType.REJECT
                summary = "（草稿阶段）都市商战老套，不建议立项。" # 过于主观、无事实根据的负面评价，用于测试 ReviewAgent 纠正
            else:
                conclusion = DecisionType.REVISE
                summary = "（已根据 Review 修改）项目结合了非遗茶文化与现代商战，切入点具独特性。李建国强拆茶馆等戏剧冲突合理，但商战收购逻辑需进一步细化，增强专业性。建议编剧团队引入金融顾问修正商战细节后，再行重新评估。"
        else:
            risks = [
                RiskPoint(category="市场同质化", description="题材属于常见流派，竞争激烈，面临较大的宣发压力。", severity=SeverityType.MEDIUM)
            ]
            conclusion = DecisionType.REVISE
            summary = f"本项目题材属于 {genre}，目前整体结构框架完整，但核心冲突还需进一步打磨。建议对剧本进行一轮修改以增强人物动机，完成后可考虑推进立项。"
            
        state.parsed_risks = risks
        
        # 2. 生成 Draft Report (在被 Review 审核通过之前，Review 状态先设为未通过，待 ReviewAgent 审核)
        draft = EvaluationReport(
            script_id=str(uuid.uuid4())[:8],
            title=title,
            genre=genre,
            characters=state.parsed_characters,
            relations=state.parsed_relations,
            events=state.parsed_events,
            conflicts=state.parsed_conflicts,
            risks=risks,
            references=state.retrieved_references,
            review=ReviewResult(is_passed=False, findings=["草稿生成完成，待审核"], revision_suggestions=[]),
            conclusion=conclusion,
            summary=summary
        )
        
        state.draft_report = draft
        state.history_logs.append(f"[{datetime.datetime.now().isoformat()}] AnalysisAgent 草稿报告已生成，立项建议为: {conclusion.value}。")
        return state

# 全局 AnalysisAgent 单例
analysis_agent = AnalysisAgent()
