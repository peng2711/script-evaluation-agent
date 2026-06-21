from ..schemas.agent_state import AgentState
from ..schemas.report import CharacterProfile, PlotEvent, ScriptAnalysis
from ..memory.character_memory import global_character_memory
import datetime

class ParserAgent:
    """
    Parser Agent (Mock 实现)：解析剧本大纲，提取出 CharacterProfile 和 PlotEvent，并组装为 ScriptAnalysis。
    """
    def execute(self, state: AgentState) -> AgentState:
        state.history_logs.append(f"[{datetime.datetime.now().isoformat()}] ParserAgent 开始解析剧本数据结构。")
        
        title = state.script.title
        content = state.script.raw_text
        
        characters = []
        plot_events = []
        core_conflict = ""
        character_relations = []
        risk_points = []
        strengths = []
        weaknesses = []
        
        if "林啸" in content or "赵乾" in content:
            characters = [
                CharacterProfile(
                    name="林啸",
                    role="特工 (代号'风影')",
                    personality=["冷静", "机警", "背负旧创"],
                    motivation="查明灭门真相，彻底铲除赵乾的跨国走私势力",
                    relationships={"赵乾": "敌对（杀父之仇）", "苏晴": "绝对信任的盟友"},
                    constraints=["不能伤害无辜百姓", "必须服从上级组织的安全边界红线"],
                    evidence_spans=["林啸站在废墟中，握紧了拳头...", "林啸冷静地计算着对手的枪法节奏。"]
                ),
                CharacterProfile(
                    name="赵乾",
                    role="跨国黑道商人",
                    personality=["残忍", "伪善", "老谋深算"],
                    motivation="扩大走私帝国，并在黑道中树立绝对权威",
                    relationships={"林啸": "欲除之而后快的眼中钉", "苏晴": "追缉的黑客目标"},
                    constraints=["不能直接触怒官方底线，以免引火烧身"],
                    evidence_spans=["赵乾端起红酒杯，微笑着对手下说：'让他消失。'", "表面上他是市里的杰出慈善家。"]
                ),
                CharacterProfile(
                    name="苏晴",
                    role="天才女黑客",
                    personality=["活泼", "正义", "技术高超"],
                    motivation="用黑客技术行侠仗义，帮助林啸脱离险境",
                    relationships={"林啸": "并肩作战的技术后盾", "赵乾": "敌对/抹除目标"},
                    constraints=["体能极差，无法进行近身格斗防御"],
                    evidence_spans=["苏晴咬着棒棒糖，双手在键盘上飞速敲击...", "网络防御网络在三秒内被苏晴撕裂。"]
                )
            ]
            
            character_relations = [
                "林啸与赵乾为生死之仇的敌对博弈关系",
                "苏晴是林啸强力的外部网络战友与精神支持"
            ]
            
            core_conflict = "林啸作为正义化身，在层层危机中搜集证据，击溃由赵乾掌控的拥有极高资本与地方渗透力的走私集团。"
            
            plot_events = [
                PlotEvent(
                    event_id="EVT-001",
                    summary="破晓行动：林啸夜潜赵乾的集装箱码头，利用苏晴的远程掩护获取了核心账目。",
                    characters=["林啸", "苏晴"],
                    conflict_type="潜入与反潜入对抗",
                    evidence_span="林啸避开探照灯，从侧墙翻入..."
                ),
                PlotEvent(
                    event_id="EVT-002",
                    summary="走私船大爆炸：赵乾设下陷阱，假意与林啸对决却引爆了炸药，林啸险死还生。",
                    characters=["林啸", "赵乾"],
                    conflict_type="热兵器交火与生死谋杀",
                    evidence_span="火光瞬间吞噬了整个码头船舱..."
                )
            ]
            
            risk_points = [
                "政策风险：主角经历包含大量未成年人极端创伤细节描写，易引发负面价值导向审查。",
                "制作风险：爆破戏与飞车动作占比极高，制作成本预算容易超支且安全控制难度大。"
            ]
            strengths = [
                "人设极佳：主角的双面特工性格层次丰富，反派赵乾的儒雅伪善具备强烈的张力。",
                "情节连贯：前三集破晓行动节奏紧凑，能够快速抓住动作悬疑受众的眼球。"
            ]
            weaknesses = [
                "感情线干瘪：林啸与苏晴的战友情缺乏情感支点，容易被评价为冰冷的打斗机器。"
            ]
            
        elif "陈默" in content or "苏瑶" in content:
            characters = [
                CharacterProfile(
                    name="陈默",
                    role="天才青年投资人",
                    personality=["骄傲", "焦虑", "理想主义"],
                    motivation="在并购惨败后寻回自我，挫败李建国的强取豪夺",
                    relationships={"苏瑶": "茶友/情感慰藉/商业搭档", "李建国": "昔日反目的商业盟友"},
                    constraints=["内心有重度焦虑症，在极端压力下需要吃药"],
                    evidence_spans=["陈默盯着大盘指数，手微微有些发抖...", "他第一次在苏瑶茶馆里睡了一个好觉。"]
                ),
                CharacterProfile(
                    name="苏瑶",
                    role="百年老茶馆继承人",
                    personality=["温婉", "坚韧", "不向资本妥协"],
                    motivation="继承祖父遗志，将茶馆作为非物质文化遗产传承下去",
                    relationships={"陈默": "彼此治愈的红颜知己", "李建国": "侵略性的拆迁强买者"},
                    constraints=["宁死也不肯卖掉老茶馆的地契和招牌"],
                    evidence_spans=["苏瑶倒了一杯茶，动作轻柔却无比坚定地说：'这块招牌不卖。'"]
                ),
                CharacterProfile(
                    name="李建国",
                    role="冷血地产巨鳄",
                    personality=["现实", "唯利是图", "不择手段"],
                    motivation="强拆老街改建高端写字楼，获取暴利",
                    relationships={"陈默": "昔日的提携者，现在的商业对手", "苏瑶": "打压强征的对象"},
                    constraints=["不能在媒体上曝光自己的非法手段，极其注重集团上市前的公众形象"],
                    evidence_spans=["李建国冷笑一声：'在这个世界上，情怀是不值一分钱的。'"]
                )
            ]
            
            character_relations = [
                "陈默与李建国之间是现代投资理念决裂下的商业博弈",
                "陈默与苏瑶互相吸引，商业资本与非遗情怀发生和谐碰撞"
            ]
            
            core_conflict = "陈默用高超的资本防御技巧协助苏瑶，对抗地产商李建国强拆百年茶馆招牌的强权行径。"
            
            plot_events = [
                PlotEvent(
                    event_id="EVT-101",
                    summary="茶馆危机：李建国派人上门拉横幅强行清场，陈默利用舆论和法律程序紧急叫停。",
                    characters=["陈默", "苏瑶", "李建国"],
                    conflict_type="资本侵略与民生非遗抗争",
                    evidence_span="几个黑衣人强行搬动桌椅，苏瑶拦在门前..."
                )
            ]
            
            risk_points = [
                "同质化风险：商战套路略显单一，容易流于普通爽文套路，降低作品的品质感。"
            ]
            strengths = [
                "立意高远：将现代冰冷商战与传统温润的非遗茶文化深度交织，极具新意与情怀价值。"
            ]
            weaknesses = [
                "商战技术细节偏空洞，强拆手段过于粗暴，脱离现代金融市场运作真实规律。"
            ]
            
        else:
            # 默认 fallback mock 数据
            characters = [
                CharacterProfile(
                    name="张无名",
                    role="故事主人公",
                    personality=["普通", "隐忍"],
                    motivation="生存与寻找真相",
                    relationships={"对手李": "敌对竞争"},
                    constraints=["没有任何外挂，必须靠自己"],
                    evidence_spans=["张无名在角落里静静观察。"]
                )
            ]
            core_conflict = "主人公克服自身局限，实现成长的故事冲突。"
            plot_events = [
                PlotEvent(
                    event_id="EVT-999",
                    summary="遭遇突发变故，被迫走上主线旅程。",
                    characters=["张无名"],
                    conflict_type="人与命运的博弈",
                    evidence_span="命运的齿轮在这一刻开始转动。"
                )
            ]
            risk_points = ["同质化风险较高"]
            strengths = ["框架完整"]
            weaknesses = ["细节略显不足"]

        # 将解析到的角色配置文件，写入 Character Memory，确保后续节点引用一致
        for profile in characters:
            global_character_memory.update_character_profile(title, profile)

        # 组装 ScriptAnalysis 结构
        state.analysis = ScriptAnalysis(
            characters=characters,
            character_relations=character_relations,
            core_conflict=core_conflict,
            plot_events=plot_events,
            risk_points=risk_points,
            strengths=strengths,
            weaknesses=weaknesses
        )
        
        state.history_logs.append(f"[{datetime.datetime.now().isoformat()}] ParserAgent 解析完成。提取出 {len(characters)} 个角色，{len(plot_events)} 个核心剧情事件。")
        return state

# 全局 ParserAgent 单例
parser_agent = ParserAgent()
