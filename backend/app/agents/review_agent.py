from ..schemas.agent_state import AgentState
from ..schemas.report import ReviewResult, EvaluationReport
import datetime

class ReviewAgent:
    """
    Review Agent (Mock 实现)：质检节点。审查分析报告草稿是否包含逻辑矛盾、无事实根据的主观评语，
    并确认角色设定的一致性。如果审查未通过，会给出具体整改建议并打回重改。
    """
    def execute(self, state: AgentState) -> AgentState:
        state.history_logs.append(f"[{datetime.datetime.now().isoformat()}] ReviewAgent 开始对评估报告进行质检审查。")
        
        draft = state.draft_report
        if not draft:
            # 异常处理：没有草稿，直接报错返回
            review_res = ReviewResult(
                is_passed=False,
                findings=["未检测到生成的草稿报告"],
                revision_suggestions=["请先启动 AnalysisAgent 生成草稿报告"]
            )
            state.review_result = review_res
            return state
            
        content = state.script.content
        
        # 1. 模拟质检审核规则
        # 第一轮 (iterations == 0) 会故意找出问题并退回修改
        if state.iterations == 0:
            if "林啸" in content:
                is_passed = False
                findings = [
                    "立项建议结论与风险点矛盾：报告中评估制作风险为 HIGH，但结论却为 PASS（直接通过），逻辑不合理。",
                    "结论过于主观，缺少针对高制作成本和敏感画面规避的可行性调整意见。"
                ]
                revision_suggestions = [
                    "请将立项建议修改为 REVISE（建议修改），并在总结中补充关于规避敏感创伤画面、减少15%特效动作戏的整改指导建议。"
                ]
            elif "陈默" in content:
                is_passed = False
                findings = [
                    "评价带有偏见且缺少论证：总结称'都市商战老套，不建议立项'，属于主观无依据的草率结论。",
                    "未结合检索作品《狂飙》（同样涉及人物博弈）进行同题材的市场化深度对比。"
                ]
                revision_suggestions = [
                    "请将立项建议调整为 REVISE，并在总结中结合茶馆与非遗文化的独特性，以及《狂飙》等强博弈题材的市场表现，提出引入专业金融顾问打磨商战细节的建议。"
                ]
            else:
                # 默认通用通过，不循环
                is_passed = True
                findings = []
                revision_suggestions = []
        else:
            # 第二轮或之后，通过审核
            is_passed = True
            findings = []
            revision_suggestions = []
            
        review_res = ReviewResult(
            is_passed=is_passed,
            findings=findings,
            revision_suggestions=revision_suggestions
        )
        
        # 2. 更新 draft_report 里的 review 结果
        draft.review = review_res
        state.review_result = review_res
        
        if is_passed:
            state.final_report = draft
            state.history_logs.append(f"[{datetime.datetime.now().isoformat()}] ReviewAgent 质检审查通过！报告已锁定。")
        else:
            state.history_logs.append(f"[{datetime.datetime.now().isoformat()}] ReviewAgent 质检审查未通过。驳回原因: {'; '.join(findings)}")
            
        return state

# 全局 ReviewAgent 单例
review_agent = ReviewAgent()
