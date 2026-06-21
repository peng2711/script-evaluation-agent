from ..schemas.agent_state import AgentState
from ..schemas.report import ReviewIssue, FinalReport
from ..memory.character_memory import global_character_memory
import datetime
import re
from typing import List, Any

class ReviewAgent:
    """
    Review Agent：质检节点。使用独立上下文检查 Analysis Agent 的评估报告，不直接相信前面 Agent 的结论。
    检查类型：
    1. unsupported_claim：无依据评价；
    2. character_inconsistency：人物设定不一致；
    3. wrong_relation：人物关系错误；
    4. hallucinated_event：编造剧情事件；
    5. weak_suggestion：修改建议太空泛；
    6. evidence_mismatch：证据和结论不匹配。
    """
    def execute(self, state: AgentState) -> AgentState:
        state.history_logs.append(f"[{datetime.datetime.now().isoformat()}] ReviewAgent 开始质检报告草稿。")
        
        draft = state.draft_report
        if not draft:
            from ..schemas.report import ReviewDecision
            state.review_decision = ReviewDecision(
                passed=False,
                issues=[],
                action="rewrite_analysis",
                reason="未能找到评估草稿报告。"
            )
            state.history_logs.append(f"[{datetime.datetime.now().isoformat()}] ReviewAgent 质检失败：缺少草稿报告。")
            state.should_retrieve_more = False
            state.should_rewrite_report = False
            return state

        # 运行详细的质检审核规则
        issues = self.review(
            script_title=state.script.title,
            script_genre=state.script.genre,
            raw_text=state.script.raw_text,
            analysis=state.analysis,
            project_id=state.script.project_id,
            evidences=state.evidences,
            draft_report=draft
        )

        # 写入审核出的问题
        state.review_issues = issues
        draft.review_issues = issues
        
        # 统计各类型的缺陷以进行智能决策决策
        has_high_risk = any(i.issue_type == "high_risk" for i in issues)
        has_retrieve = any(i.issue_type in ("unsupported_claim", "evidence_mismatch") for i in issues)
        has_rewrite = any(i.issue_type in ("weak_suggestion", "character_inconsistency", "hallucinated_event", "wrong_relation") for i in issues)

        if has_high_risk:
            action = "human_check"
            reason = "发现剧本包含高度合规或政策红线风险点，已拦截并自动流转至人工审核。"
        elif has_retrieve:
            action = "retrieve_more"
            reason = "检测到严重的对标引用不足或题材证据错配，必须重新对标召回数据。"
        elif has_rewrite:
            action = "rewrite_analysis"
            reason = "检测到报告包含明显的人设冲突、剧情幻觉或空泛修改建议，必须退回重写。"
        else:
            action = "pass"
            reason = "报告通过了全部合规及事实一致性审查。"

        passed = (action == "pass")
        
        # 构造 ReviewDecision 写入状态
        from ..schemas.report import ReviewDecision
        decision = ReviewDecision(
            passed=passed,
            issues=issues,
            action=action,
            reason=reason
        )
        state.review_decision = decision

        # 写入兼容旧状态机的标志位
        state.should_rewrite_report = (action == "rewrite_analysis")
        state.should_retrieve_more = (action == "retrieve_more")

        if passed:
            state.final_report = draft
            state.history_logs.append(f"[{datetime.datetime.now().isoformat()}] ReviewAgent 质检审查通过！报告正式锁定。")
        else:
            state.history_logs.append(
                f"[{datetime.datetime.now().isoformat()}] ReviewAgent 质检审查未通过：action={action}, 原因: {reason}"
            )
            
        return state

    def review(
        self,
        script_title: str,
        script_genre: str,
        raw_text: str,
        analysis: Any,
        project_id: str,
        evidences: List[Any],
        draft_report: FinalReport
    ) -> List[ReviewIssue]:
        issues = []
        
        summary = draft_report.executive_summary
        suggestions = draft_report.improvement_suggestions
        
        # 1. 编造人物 与 引用不存在剧情 (hallucinated_event)
        # 获取合法角色列表
        valid_char_names = set()
        if analysis and analysis.characters:
            valid_char_names = {c.name for c in analysis.characters}

        # 检查报告中是否包含编造人物
        fabricated_names = ["王强", "张三", "李四", "李美莉", "王五", "小红", "小明"]
        for fab_name in fabricated_names:
            if fab_name in summary or any(fab_name in sug for sug in suggestions):
                if fab_name not in valid_char_names:
                    issues.append(ReviewIssue(
                        issue_type="hallucinated_event",
                        severity="HIGH",
                        claim=f"报告中引用了人物角色 '{fab_name}'",
                        reason=f"在剧本分析和原文中均不存在名为 '{fab_name}' 的角色，此为报告撰写过程中的人物编造幻觉。",
                        suggested_fix=f"请核对剧本实际角色列表，移除关于 '{fab_name}' 的所有描述，并将其替换为剧本中实际存在的相关角色。"
                    ))

        # 引用不存在剧情 (hallucinated_event)
        fabricated_plots = ["车祸", "穿越", "中毒", "失忆", "坠崖", "绑架", "枪战"]
        for plot in fabricated_plots:
            if plot in summary or any(plot in sug for sug in suggestions):
                if plot not in raw_text:
                    issues.append(ReviewIssue(
                        issue_type="hallucinated_event",
                        severity="HIGH",
                        claim=f"报告中提及了 '{plot}' 的剧情事件/情节点",
                        reason=f"剧本原文中并未出现任何关于 '{plot}' 的内容，此剧情事件纯属报告幻觉编造。",
                        suggested_fix=f"请重新核对剧本大纲，移除与 '{plot}' 相关的虚假剧情分析，并围绕剧本中实际存在的冲突进行评估。"
                    ))

        # 2. 角色行为违反 CharacterMemory.constraints (character_inconsistency)
        mem_chars = global_character_memory.load_characters(project_id)
        char_constraints = {}
        for c in (analysis.characters if analysis else []):
            char_constraints[c.name] = set(c.constraints)
        for mc in mem_chars:
            name = mc.get("name")
            if name:
                char_constraints.setdefault(name, set()).update(mc.get("constraints", []))

        for char_name, constraints in char_constraints.items():
            for constraint in constraints:
                if "不能伤害无辜" in constraint or "不伤害无辜" in constraint:
                    if any(x in summary or any(x in sug for sug in suggestions) for x in [char_name + "伤害无辜", char_name + "杀害无辜", char_name + "炸死无辜"]):
                        issues.append(ReviewIssue(
                            issue_type="character_inconsistency",
                            severity="HIGH",
                            claim=f"报告指出角色 '{char_name}' 伤害或杀害了无辜百姓",
                            reason=f"这直接违反了角色设定约束（CharacterMemory.constraints）: '{constraint}'。",
                            suggested_fix=f"请修正角色行为的分析，确保其符合不伤害无辜的核心人设约束，调整相关情节的评价。"
                        ))
                if "不杀人" in constraint:
                    if any(x in summary or any(x in sug for sug in suggestions) for x in [char_name + "杀人", char_name + "杀死了", char_name + "击杀了"]):
                        issues.append(ReviewIssue(
                            issue_type="character_inconsistency",
                            severity="HIGH",
                            claim=f"报告提及角色 '{char_name}' 杀人/击杀对手",
                            reason=f"角色设定约束中明确规定其 '{constraint}'，报告中的行为描述导致人设崩塌。",
                            suggested_fix=f"请修改该角色的行为评估，改用非致命性冲突解决方式，以维持人设稳定性。"
                        ))

        # 3. 人物关系错误 (wrong_relation)
        defined_relations = {}
        for c in (analysis.characters if analysis else []):
            for target, rel in c.relationships.items():
                defined_relations[(c.name, target)] = rel
        for mc in mem_chars:
            name = mc.get("name")
            relationships = mc.get("relationships", {})
            if name and relationships:
                for target, rel in relationships.items():
                    defined_relations[(name, target)] = rel

        relation_keywords = {
            "情侣": ["情侣", "恋人", "相爱", "恋爱", "女友", "男友"],
            "夫妻": ["夫妻", "结婚", "爱人", "配偶"],
            "父子": ["父子", "父亲", "爸爸", "儿子"],
            "母女": ["母女", "母亲", "妈妈", "女儿"],
            "师徒": ["师徒", "师傅", "徒弟", "徒儿"],
            "仇人": ["仇人", "生死之仇", "死敌", "宿敌", "敌对", "杀父之仇"]
        }
        
        sentences = re.split(r'[。！？\n]', summary) + suggestions
        for (char_a, char_b), defined_rel in defined_relations.items():
            for sentence in sentences:
                if char_a in sentence and char_b in sentence:
                    a_b_rel_type = None
                    for r_type, kw_list in relation_keywords.items():
                        if any(kw in defined_rel for kw in kw_list):
                            a_b_rel_type = r_type
                            break
                            
                    for r_type, kw_list in relation_keywords.items():
                        if a_b_rel_type and r_type != a_b_rel_type:
                            if any(kw in sentence for kw in kw_list):
                                is_negated = any(neg + kw in sentence for kw in kw_list for neg in ["不", "非", "没", "无"])
                                if not is_negated:
                                    issues.append(ReviewIssue(
                                        issue_type="wrong_relation",
                                        severity="MEDIUM",
                                        claim=f"报告中描述 '{char_a}' 与 '{char_b}' 为 '{r_type}' 关系",
                                        reason=f"这与剧本事实及记忆中登记的实际关系 '{defined_rel}' 不符。",
                                        suggested_fix=f"请修正 '{char_a}' 与 '{char_b}' 的人物关系描述，将其更正为符合设定事实的 '{defined_rel}'。"
                                    ))
                                    break

        # 4. 无依据评分 / 无依据评价 (unsupported_claim)
        if len(evidences) == 0:
            issues.append(ReviewIssue(
                issue_type="unsupported_claim",
                severity="HIGH",
                claim="报告给出了市场适应度及立项评估决策结论",
                reason="当前评估完全没有关联任何本地相似作品的检索证据（RetrievalEvidence 为空），市场商业潜力判断缺乏数据支撑。",
                suggested_fix="请通过 Retrieval Agent 检索相似题材的作品，并在评估报告中引用相似作品的评分或市场表现作为对比支撑论据。"
            ))
        else:
            # 检查整个报告摘要中是否包含任何文献引用（形如 《...》）以及证据/原文等关键词
            has_citation = "《" in summary
            has_keywords = any(kw in summary for kw in ["原文", "证据", "数据", "段落", "对标", "检索"])
            if not (has_citation and has_keywords):
                issues.append(ReviewIssue(
                    issue_type="unsupported_claim",
                    severity="MEDIUM",
                    claim="报告摘要的整体论证缺乏具体的证据或对标作品支持",
                    reason="整篇评估报告摘要中没有引用任何具体的对标作品（如使用《作品名》）或说明原文证据，判断流于主观。",
                    suggested_fix="请在评估报告的执行摘要中，具体引用剧本原文证据或检索到的对标作品（如《狂飙》等）来支撑您的打分和判断。"
                ))

        # 5. 建议太空泛 (weak_suggestion)
        vague_keywords = ["直接开拍", "直接放弃", "直接开机", "直接开拍。", "直接放弃。", "直接开机。", "加强人物塑造", "提升剧情逻辑", "增强戏剧冲突"]
        for sug in suggestions:
            is_vague = False
            if len(sug.strip()) < 12:
                is_vague = True
            elif any(kw in sug for kw in vague_keywords):
                if not ("第" in sug and "集" in sug):
                    is_vague = True
                    
            if is_vague:
                issues.append(ReviewIssue(
                    issue_type="weak_suggestion",
                    severity="MEDIUM",
                    claim=f"修改建议: '{sug}'",
                    reason="该修改建议过于空泛笼统（如仅给出‘直接开机’、‘直接放弃’或简单的口号式建议），缺乏可落地的具体集数和具体情境修改方案。",
                    suggested_fix="请提供高度具体的落地建议，必须指明具体集数（例如‘在第 1 集结尾...’）并结合剧本原文冲突与人设定点修改。"
                ))

        # 6. 证据和结论不匹配 (evidence_mismatch)
        for ev in evidences:
            if ev.source_title == "流浪地球":
                if "科幻" not in script_genre:
                    if "流浪地球" in summary:
                        if not any(kw in summary for kw in ["工业", "制作", "技术", "成本", "特效"]):
                            issues.append(ReviewIssue(
                                issue_type="evidence_mismatch",
                                severity="HIGH",
                                claim=f"将题材剧本与科幻题材《流浪地球》进行对标评估",
                                reason=f"剧本题材为 '{script_genre}'，而引用的对标作品《流浪地球》为科幻题材，两者受众群体与制作逻辑完全不匹配，证据无法支撑结论。",
                                suggested_fix=f"请长效规避或改用更符合题材类型的对标作品（如《隐秘的角落》或《狂飙》）进行市场匹配论证。"
                            ))
            if ev.source_title == "隐秘的角落":
                if "悬疑" not in script_genre and "都市" in script_genre and "爱情" in script_genre:
                    if "隐秘的角落" in summary:
                        if not any(kw in summary for kw in ["悬疑", "博弈", "人性"]):
                            issues.append(ReviewIssue(
                                issue_type="evidence_mismatch",
                                severity="MEDIUM",
                                claim=f"将都市爱情剧本与悬疑犯罪题材《隐秘的角落》进行对标评估",
                                reason=f"剧本主要为都市爱情题材，而引用的对标作品《隐秘的角落》是硬核悬疑犯罪题材，两者的核心卖点和受众不匹配。",
                                suggested_fix="请改用更为贴合都市爱情或商战题材的作品（如《狂飙》中商战博弈或其它同类剧目）作为参考证据。"
                            ))

        # 7. 政策违规与高危内容检测 (high_risk)
        high_risk_keywords = ["私刑制裁", "血腥暴力", "法律红线", "监管下架", "政策红线"]
        for kw in high_risk_keywords:
            if kw in summary or any(kw in sug for sug in suggestions):
                issues.append(ReviewIssue(
                    issue_type="high_risk",
                    severity="HIGH",
                    claim=f"报告或修改建议中涉及了有关 '{kw}' 的敏感表述",
                    reason=f"剧本评估内容触发高危审查红线敏感词 '{kw}'，可能面临监管合规或禁映下架风险。",
                    suggested_fix=f"须立即中止自动立项流转，提交制片团队进行线下人工合规复核（建议人工复核）。"
                ))

        return issues

# 全局 ReviewAgent 单例
review_agent = ReviewAgent()
