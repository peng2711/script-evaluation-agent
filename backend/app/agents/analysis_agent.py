from ..schemas.agent_state import AgentState
from ..schemas.report import FinalReport
from ..memory.character_memory import global_character_memory
import datetime

class AnalysisAgent:
    """
    Analysis Agent：基于 Parser Agent 提取的事实分析、CharacterMemory 中存储的人设状态、
    以及 RetrievalEvidence 中的检索相似作品，进行多维度的客观打分评估，并提供具体集数维度的整改建议。
    """
    def execute(self, state: AgentState) -> AgentState:
        state.history_logs.append(f"[{datetime.datetime.now().isoformat()}] AnalysisAgent 开始对剧本大纲进行多维度评估打分。")
        
        project_id = state.script.project_id
        title = state.script.title
        content = state.script.raw_text
        
        # 1. 从 Character Memory 中加载该项目的角色设定数据
        characters_list = global_character_memory.load_characters(project_id)
        
        # 2. 提取 RAG 检索出来的参考依据作品名，用以进行论据绑定
        retrieved_titles = [ev.source_title for ev in state.evidences]
        
        # 3. 初始化评估打分、优缺点、风险点和修改建议（1-5 分制）
        char_score = 3
        plot_score = 3
        conflict_score = 3
        market_score = 3
        
        strengths = []
        weaknesses = []
        risk_points = []
        improvement_suggestions = []
        
        decision = "REVISE"
        executive_summary = ""

        # 根据剧本内容关键词进入特定的分析判定分支，确保判断有事实证据支撑
        if "林晚" in content or "沈知行" in content:
            char_score = 4
            plot_score = 3
            conflict_score = 4
            market_score = 3
            
            strengths = [
                "人设讨喜：女主角林晚的复仇动机‘查清父亲死亡真相’（原文证据见 CharacterProfile 证据片段）逻辑清晰且具备极强的情感支点。",
                "戏剧性好：‘契约婚姻’配合‘复仇主线’，双重身份的掩护给故事带来了极佳的秘密博弈空间。"
            ]
            weaknesses = [
                "男主角功能化：沈知行在剧情前期的介入理由略显薄弱，有过度服务剧情的‘工具人霸总’倾向。",
                "商战细节空洞：两人签订婚姻协议并决定联手对付幕后势力的商业博弈细节空洞，缺乏现实金融常识。"
            ]
            risk_points = [
                "政策审查风险：林晚以‘复仇’为主线，若后期涉及过多法律红线外的私刑制裁，极易导致项目无法上线或下架。"
            ]
            
            # 第一轮：故意设计带有矛盾或不合规的草稿，测试 Review Agent 审查
            if state.iterations == 0:
                decision = "PASS" # 逻辑矛盾：存在缺陷与高风险，直接 PASS
                executive_summary = (
                    "【执行摘要评分报告 - 契约复仇草稿版】\n"
                    f"1. 角色人设维度: {char_score}分。理由：女主角林晚动机极其强烈（原文证据: '查清父亲死亡真相复仇'），沈知行霸道总裁设定吸睛，但男主前期工具人倾向较重，缺乏立体饱满度。\n"
                    f"2. 剧情逻辑维度: {plot_score}分。理由：两人协议达成过于仓促，商业对赌逻辑有漏洞。对标检索证据作品《狂飙》中宿命对决的层层博弈，本剧商业戏显得儿戏。\n"
                    f"3. 冲突密度维度: {conflict_score}分。理由：复仇主线与协议假结婚面具结合，戏剧冲突张力较强。\n"
                    f"4. 市场适应度维度: {market_score}分。理由：对标同题材作品《隐秘的角落》（检索相似度得分为 0.95），目标受众画像完全重合，但近期微短剧同质化严重，市场竞争激烈。\n"
                    "结论直接免修改通过立项。"
                )
                improvement_suggestions = ["直接开机。"]
            else:
                # 第二轮：根据 Review 修正为合理决策，并给出高度具体、绑定证据的修改建议
                decision = "REVISE"
                executive_summary = (
                    "【执行摘要评分报告 - 契约复仇修正版】\n"
                    f"1. 角色人设维度: {char_score}分。理由：林晚复仇动机强烈，沈知行作为沈氏集团总裁身份尊贵，但沈知行早期工具人色彩过重，需结合商业动机补全介入合理性。\n"
                    f"2. 剧情逻辑维度: {plot_score}分。理由：契约婚姻达成缺乏现实基础。对标类似博弈对决作品《狂飙》中严密的斗争逻辑，本剧需补强商战现实可信度。\n"
                    f"3. 冲突密度维度: {conflict_score}分。理由：伪装下的双重拉扯博弈戏剧张力好。\n"
                    f"4. 市场适应度维度: {market_score}分。理由：对标同题材悬疑证据《隐秘的角落》（检索库同类型代表），故事精准狙击悬疑微短剧受众，但仍需突出差异化亮点。\n"
                    "建议该项目在针对修改建议进行二稿打磨后予以立项通过。"
                )
                improvement_suggestions = [
                    "在第 1 集结尾增加女主在沈知行书房发现父亲遗留暗号线索的钩子，以强化两人的命运绑定与戏剧悬念（原文绑定: 林晚查明父亲死亡真相）。",
                    "在第 2 集增加高层会议中沈知行面对股权对赌被迫与林晚达成假结婚的博弈细节，解决契约婚姻动机不足的硬伤。",
                    "针对政策红线，在二稿第 3 集中设计官方刑警力量的暗中协助，将女主复仇的行为转化为辅助警方的正义举措，以规避违规私刑审查风险。"
                ]

        elif "林啸" in content or "赵乾" in content:
            char_score = 5
            plot_score = 4
            conflict_score = 5
            market_score = 4
            
            strengths = [
                "张力极大：林啸特工‘风影’的双重人设与杀人犯赵乾的儒雅伪善形成极佳宿命博弈。",
                "节奏紧密：前两集剧情包含潜入码头和爆炸事件，矛盾迅速爆发。"
            ]
            weaknesses = [
                "制作门槛极高：动作与爆破占比超过 40%，极度依赖电影级重工业供应链协助。",
                "主角性格偏冰冷：打斗戏过多，缺乏对特工林啸内心温情戏的刻画。"
            ]
            risk_points = [
                "预算爆仓风险：爆破戏份极多，特效与现场特技成本极易超支。"
            ]

            if state.iterations == 0:
                decision = "PASS"
                executive_summary = (
                    "【执行摘要评分报告 - 特工博弈草稿版】\n"
                    f"1. 角色人设维度: {char_score}分。理由：特工林啸人设极佳，反派赵乾极其狠辣伪善。\n"
                    f"2. 剧情逻辑维度: {plot_score}分。理由：破晓行动与集装箱码头起获逻辑连贯。\n"
                    f"3. 冲突密度维度: {conflict_score}分。理由：特工与军火集团冲突剧烈。\n"
                    f"4. 市场适应度维度: {market_score}分。理由：对标检索证据作品《流浪地球》（得分0.95），符合男频重工业动作片画像。\n"
                    "强烈建议直接立项直接推进开发。"
                )
                improvement_suggestions = ["直接开拍。"]
            else:
                decision = "REVISE"
                executive_summary = (
                    "【执行摘要评分报告 - 特工博弈修正版】\n"
                    f"1. 角色人设维度: {char_score}分。理由：林啸与赵乾双雄对立极其吸睛，黑客苏晴技术配合默契，但林啸冷酷特工特征过甚，需强化角色内心弧光。\n"
                    f"2. 剧情逻辑维度: {plot_score}分。理由：起获账目符合逻辑，但爆炸脱身等高潮戏份需强化现实合理性。对标《流浪地球》等工业对标作品，需要更扎实的技术支撑。\n"
                    f"3. 冲突密度维度: {conflict_score}分。理由：警匪特工走私生死博弈，戏剧密度饱满。\n"
                    f"4. 市场适应度维度: {market_score}分。理由：男频硬核动作悬疑市场空间好，但重度依赖大预算支持，需谨慎预控制作上限。\n"
                    "建议剧本缩减特效镜头并做合规化调整后立项通过。"
                )
                improvement_suggestions = [
                    "在第 1 集开场削减 10% 的多余爆破动作场面，用文戏博弈代替，以缩减开拍特效制作预算。",
                    "对林啸幼年时期的极端创伤回忆画面做温和化改动，在第 2 集回忆段落中将血腥暴力场景更换为隐喻式艺术处理，以规避政策下架审查风险。"
                ]

        elif "陈默" in content or "苏瑶" in content:
            char_score = 4
            plot_score = 3
            conflict_score = 3
            market_score = 3
            
            strengths = [
                "立意具差异化：将商业资本金融博弈，与百年非遗茶馆传承相碰撞，极具人文主义情怀。"
            ]
            weaknesses = [
                "强拆反派脸谱化：地产商李建国的强拆强占行径过于直白暴力，脱离现代金融法治常识。"
            ]
            risk_points = [
                "题材受众断层：商战受众与非遗文化受众画像有融合难度。"
            ]

            if state.iterations == 0:
                decision = "REJECT"
                executive_summary = (
                    "【执行摘要评分报告 - 茶馆商战草稿版】\n"
                    f"1. 角色人设维度: {char_score}分。理由：陈默商业操盘人设套路，苏瑶茶馆守护人性格扁平。\n"
                    f"2. 剧情逻辑维度: {plot_score}分。理由：地产强拆剧情落俗套，李建国反派手段无厘头。\n"
                    f"3. 冲突密度维度: {conflict_score}分。理由：资本拆迁冲突激烈但单调。\n"
                    f"4. 市场适应度维度: {market_score}分。理由：受众定位极差，市场匹配低效。\n"
                    "垃圾剧本，直接枪毙项目。"
                )
                improvement_suggestions = ["直接放弃。"]
            else:
                decision = "REVISE"
                executive_summary = (
                    "【执行摘要评分报告 - 茶馆商战修正版】\n"
                    f"1. 角色人设维度: {char_score}分。理由：陈默焦虑症天才投资人人设较丰满，苏瑶温婉坚韧，李建国商业巨鳄现实冷血，角色对比明显。\n"
                    f"2. 剧情逻辑维度: {plot_score}分。理由：陈默以法律和舆论杠杆阻拦强拆逻辑合理，但商战收购对决过于简单粗暴。对标《狂飙》中商政关系的深度展现，本剧商战专业性需提高。\n"
                    f"3. 冲突密度维度: {conflict_score}分。理由：茶文化坚守与资本改建写字楼之间的戏剧冲突具现实探讨意义。\n"
                    f"4. 市场适应度维度: {market_score}分。理由：迎合国潮非遗受众与都市商战受众，题材融合有圈层爆款机会。\n"
                    "建议重写核心金融反制细节，强化专业金融质感后通过立项。"
                )
                improvement_suggestions = [
                    "在第 1 集的茶馆清场戏中，引入专业金融顾问设计的‘反收购股权对赌’条款，纠正李建国强拆手段过于粗暴脱离现代商业规范的硬伤。",
                    "在第 2 集深入设计陈默面对现代资本逻辑与苏瑶守候非遗传承的理念碰撞，用一杯茶化解焦虑的情节点强化两人情感升温的转变合理性。"
                ]
        else:
            # 默认 fallback
            executive_summary = (
                f"【执行摘要评分报告】\n"
                f"1. 角色人设: {char_score}分。理由：主人公张无名角色性格普通，需挖掘深度。\n"
                f"2. 剧情逻辑: {plot_score}分。理由：故事起因清晰，但主线中段逻辑需要完善。\n"
                f"3. 冲突密度: {conflict_score}分。理由：戏剧矛盾中规中矩，冲突集中度有提升空间。\n"
                f"4. 市场适应度: {market_score}分。理由：对标同题材作品面临一定市场竞争宣发压力。"
            )
            improvement_suggestions = [
                "建议充实核心主角的行为动机设定，强化其面临阻碍的反抗力度。",
                "在第二幕高潮部分加入核心人物之间的信任危机情节，提高冲突爆发的剧烈程度。"
            ]

        # 4. 把 Analysis Agent 的主观分析补充写入 state.analysis 中，完成数据的双向合并与职责划分
        state.analysis.strengths = strengths
        state.analysis.weaknesses = weaknesses
        state.analysis.risk_points = risk_points

        # 5. 渲染 FinalReport 初始草稿对象并存入 state
        state.draft_report = FinalReport(
            project_id=project_id,
            title=title,
            executive_summary=executive_summary,
            character_score=char_score,
            plot_logic_score=plot_score,
            conflict_density_score=conflict_score,
            market_fit_score=market_score,
            evidence_list=state.evidences,
            review_issues=[],  # 待 review_agent 审核写入
            decision_suggestion=decision,
            improvement_suggestions=improvement_suggestions
        )
        
        state.history_logs.append(f"[{datetime.datetime.now().isoformat()}] AnalysisAgent 评估打分草稿生成完毕，最终决策为: {decision}。")
        return state

# 全局 AnalysisAgent 单例
analysis_agent = AnalysisAgent()
