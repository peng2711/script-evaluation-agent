from ..schemas.agent_state import AgentState
from ..schemas.report import FinalReport
import datetime

class AnalysisAgent:
    """
    Analysis Agent (Mock 实现)：结合元素解析与检索的类似作品证据，评估多维度指标（打分 1-5），产出初始评估报告草稿。
    """
    def execute(self, state: AgentState) -> AgentState:
        state.history_logs.append(f"[{datetime.datetime.now().isoformat()}] AnalysisAgent 开始评估打分并编写草稿。")
        
        project_id = state.script.project_id
        title = state.script.title
        content = state.script.raw_text
        
        # 默认分值（1-5 范围）
        char_score = 4
        plot_score = 3
        conflict_score = 4
        market_score = 3
        
        decision = "REVISE"
        summary = ""
        improvement_suggestions = []
        
        if "林啸" in content:
            char_score = 5
            plot_score = 4
            conflict_score = 5
            market_score = 4
            
            # 第一轮：故意制造逻辑矛盾（分值极高，有高风险，但写直接通过）
            if state.iterations == 0:
                decision = "PASS"
                summary = "林啸的特工复仇设定极富视觉张力与心理深度，虽然爆破特效制作难度大且预算风险极高，但故事极佳，强烈建议直接立项推进开发。"
                improvement_suggestions = ["直接开机。"]
            else:
                # 接收到 ReviewAgent 修改建议后的修正版
                decision = "REVISE"
                summary = "该项目特工动作悬疑题材商业看点足。但由于动作戏占比过高及部分主角童年创伤情节过于血腥敏感，建议将立项等级调整为修改后通过。"
                improvement_suggestions = [
                    "建议二稿中压缩15%的爆破动作场面，控制特效制作预算。",
                    "温和化处理林啸早期的创伤回忆场景，确保符合国内相关政策审查标准。"
                ]
                
        elif "陈默" in content:
            char_score = 4
            plot_score = 3
            conflict_score = 3
            market_score = 3
            
            # 第一轮：故意制造主观偏见评价
            if state.iterations == 0:
                decision = "REJECT"
                summary = "都市商战强拆老街的桥段过于俗套，陈默和苏瑶的感情线也莫名其妙，不建议立项开发。"
                improvement_suggestions = ["建议放弃。"]
            else:
                # 修正版
                decision = "REVISE"
                summary = "项目将非遗茶文化与现代金融商战相结合，切入点较为新颖。虽李建国强拆茶馆等外部冲突戏剧张力强，但商战细节过于简单粗暴，不符合专业逻辑。建议充实商战技术细节后予以通过。"
                improvement_suggestions = [
                    "编剧团队应引入专业金融顾问，重新设计陈默阻拦恶意收购的金融反制细节。",
                    "深化陈默与苏瑶关于现代资本理念与传统文化传承之间的情感碰撞，使感情升温更显自然。"
                ]
        else:
            char_score = 3
            plot_score = 3
            conflict_score = 3
            market_score = 3
            decision = "REVISE"
            summary = "本项目故事结构完整，但整体戏剧矛盾较为平淡，题材市场同质化严重。建议对剧本冲突点进行一轮充实优化后再行评估。"
            improvement_suggestions = ["增加核心冲突的爆发力度", "提炼配角的存在感"]

        # 构建 FinalReport 模型（注意：此为 draft 阶段，review 字段在 review_agent 中会更新）
        draft = FinalReport(
            project_id=project_id,
            title=title,
            executive_summary=summary,
            character_score=char_score,
            plot_logic_score=plot_score,
            conflict_density_score=conflict_score,
            market_fit_score=market_score,
            evidence_list=state.evidences,
            review_issues=[],  # 初始为空，待 ReviewAgent 审核写入
            decision_suggestion=decision,
            improvement_suggestions=improvement_suggestions
        )
        
        state.draft_report = draft
        state.history_logs.append(f"[{datetime.datetime.now().isoformat()}] AnalysisAgent 草稿已生成，决策建议为: {decision}。")
        return state

# 全局 AnalysisAgent 单例
analysis_agent = AnalysisAgent()
