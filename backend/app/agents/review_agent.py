from ..schemas.agent_state import AgentState
from ..schemas.report import ReviewIssue
import datetime

class ReviewAgent:
    """
    Review Agent (Mock 实现)：质检节点。审查分析报告草稿是否包含逻辑矛盾与主观偏见，
    并把审核项 ReviewIssue 写入 FinalReport 的 review_issues 字段中。
    """
    def execute(self, state: AgentState) -> AgentState:
        state.history_logs.append(f"[{datetime.datetime.now().isoformat()}] ReviewAgent 开始质检报告草稿。")
        
        draft = state.draft_report
        if not draft:
            state.history_logs.append(f"[{datetime.datetime.now().isoformat()}] ReviewAgent 质检失败：缺少草稿报告。")
            return state
            
        content = state.script.raw_text
        issues = []
        
        # 1. 模拟质检审核规则
        # 第一轮 (iterations == 0) 会故意找出问题并记录到 review_issues
        if state.iterations == 0:
            if "林啸" in content:
                issues = [
                    ReviewIssue(
                        issue_type="逻辑冲突",
                        severity="HIGH",
                        claim="建议立项结论直接通过 (PASS)",
                        reason="分析报告中明确指出制作风险极高、存在超支隐患，但决策建议却给出了免修改直接立项通过，结论自相矛盾。",
                        suggested_fix="请将 decision_suggestion 修改为 REVISE，并在建议列表中加入压缩动作戏预算和规避敏感创伤画面的方案。"
                    )
                ]
            elif "陈默" in content:
                issues = [
                    ReviewIssue(
                        issue_type="无依据主观评价",
                        severity="MEDIUM",
                        claim="都市商战强拆老街的桥段过于俗套，陈默和苏瑶的感情线也莫名其妙",
                        reason="评价流于主观情绪化宣泄，缺乏基于市场参考数据（如《狂飙》等强博弈受众表现）的对比论证。",
                        suggested_fix="请将决策结论修改为 REVISE，剔除贬义性主观词汇，并给出聘请专业金融顾问优化商战细节的具体建议。"
                    )
                ]

        # 2. 将审核出的问题更新写入报告中
        draft.review_issues = issues
        state.review_issues = issues
        
        if not issues:
            state.final_report = draft
            state.history_logs.append(f"[{datetime.datetime.now().isoformat()}] ReviewAgent 质检审查通过！报告正式锁定。")
        else:
            state.history_logs.append(f"[{datetime.datetime.now().isoformat()}] ReviewAgent 质检审查未通过。共发现 {len(issues)} 个整改项。")
            
        return state

# 全局 ReviewAgent 单例
review_agent = ReviewAgent()
