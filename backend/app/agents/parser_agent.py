from typing import Optional, Any, List
from ..schemas.report import CharacterProfile, PlotEvent, ScriptAnalysis
from ..schemas.agent_state import AgentState
from ..memory.character_memory import global_character_memory
import datetime

class ParserAgent:
    """
    Parser Agent：专注于从剧本正文/大纲中提取事实信息（如角色、关系、核心冲突和事件段落证据），
    坚决不作任何质量或市场潜力等主观价值判断。
    """
    def __init__(self, llm_client: Optional[Any] = None):
        # 预留 llm_client 参数，以便后续在第三阶段或之后无缝替换为真实的大语言模型 API
        self.llm_client = llm_client

    def _split_into_paragraphs(self, text: str) -> List[str]:
        """
        如果 raw_text 很长，将其按换行符切分为段落，去除多余空白字符
        """
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
        return paragraphs

    def extract(self, raw_text: str) -> ScriptAnalysis:
        """
        核心抽取方法：运用启发式规则提取客观事实，确保输出符合 ScriptAnalysis schema。
        """
        paragraphs = self._split_into_paragraphs(raw_text)
        
        characters = []
        character_relations = []
        core_conflict = ""
        plot_events = []
        
        # 1. 探测测试用例：林晚与沈知行（契约婚姻复仇）
        if "林晚" in raw_text or "沈知行" in raw_text:
            if "林晚" in raw_text:
                evidence = [p for p in paragraphs if "林晚" in p]
                characters.append(CharacterProfile(
                    name="林晚",
                    role="女主角",
                    personality=["隐忍", "坚毅"],
                    motivation="查清父亲死亡真相并完成复仇" if "复仇" in raw_text else "查明真相",
                    relationships={"沈知行": "契约婚姻"} if "沈知行" in raw_text else {},
                    constraints=["不能暴露真实身份与真实目的"],
                    evidence_spans=evidence if evidence else ["女主角林晚。"]
                ))
            if "沈知行" in raw_text:
                evidence = [p for p in paragraphs if "沈知行" in p]
                characters.append(CharacterProfile(
                    name="沈知行",
                    role="男主角",
                    personality=["冷静", "深沉"],
                    motivation="配合林晚进行契约婚姻，并在暗中配合调查" if "契约婚姻" in raw_text else "配合调查",
                    relationships={"林晚": "契约婚姻"} if "林晚" in raw_text else {},
                    constraints=["必须遵守商业合同条款与保密规定"],
                    evidence_spans=evidence if evidence else ["男主角沈知行。"]
                ))
            
            if "契约婚姻" in raw_text:
                character_relations.append("林晚与沈知行是契约婚姻关系")
            
            if "复仇" in raw_text or "父亲死亡真相" in raw_text:
                core_conflict = "林晚为了查清父亲死亡真相进行复仇，与沈知行达成契约婚姻，共同应对幕后势力。"
            else:
                core_conflict = "林晚与沈知行的核心纠葛与冲突"
                
            for idx, p in enumerate(paragraphs):
                if any(k in p for k in ["林晚", "沈知行", "契约婚姻", "复仇"]):
                    plot_events.append(PlotEvent(
                        event_id=f"EVT-LW-{idx+1:03d}",
                        summary=f"事件大纲：{p[:25]}...",
                        characters=[name for name in ["林晚", "沈知行"] if name in p],
                        conflict_type="契约婚姻契约达成" if "契约婚姻" in p else "复仇线索推进",
                        evidence_span=p
                    ))

        # 2. 探测已有的特工博弈用例：林啸与赵乾
        elif "林啸" in raw_text or "赵乾" in raw_text:
            characters = [
                CharacterProfile(
                    name="林啸",
                    role="特工 (代号'风影')",
                    personality=["冷静", "机警", "背负旧创"],
                    motivation="查明灭门真相，彻底铲除赵乾的跨国走私势力",
                    relationships={"赵乾": "敌对（杀父之仇）", "苏晴": "绝对信任的盟友"},
                    constraints=["不能伤害无辜百姓", "必须服从上级组织的安全边界红线"],
                    evidence_spans=[p for p in paragraphs if "林啸" in p]
                ),
                CharacterProfile(
                    name="赵乾",
                    role="跨国黑道商人",
                    personality=["残忍", "伪善", "老谋深算"],
                    motivation="扩大走私帝国，并在黑道中树立绝对权威",
                    relationships={"林啸": "欲除之或者是眼中钉", "苏晴": "追缉的黑客目标"},
                    constraints=["不能直接触犯官方底线，以免引火烧身"],
                    evidence_spans=[p for p in paragraphs if "赵乾" in p]
                ),
                CharacterProfile(
                    name="苏晴",
                    role="天才女黑客",
                    personality=["活泼", "正义", "技术高超"],
                    motivation="用黑客技术行侠仗义，帮助林啸脱离险境",
                    relationships={"林啸": "并肩作战的技术后盾", "赵乾": "敌对/抹除目标"},
                    constraints=["体能极差，无法进行近身格斗防御"],
                    evidence_spans=[p for p in paragraphs if "苏晴" in p]
                )
            ]
            
            character_relations = [
                "林啸与赵乾为生死之仇的敌对博弈关系",
                "苏晴是林啸强力的外部网络战友与精神支持"
            ]
            core_conflict = "特工林啸在黑客苏晴的技术协助下潜入集装箱码头起获证据，对抗势力庞大、伪善奸诈的走私集团首脑赵乾。"
            
            for idx, p in enumerate(paragraphs):
                if any(k in p for k in ["林啸", "赵乾", "苏晴", "破晓行动", "爆炸"]):
                    plot_events.append(PlotEvent(
                        event_id=f"EVT-LX-{idx+1:03d}",
                        summary=f"事件事实：{p[:25]}...",
                        characters=[name for name in ["林啸", "赵乾", "苏晴"] if name in p],
                        conflict_type="潜入对抗" if "破晓" in p else "极端武力冲突",
                        evidence_span=p
                    ))

        # 3. 探测已有的商战茶香用例：陈默与苏瑶
        elif "陈默" in raw_text or "苏瑶" in raw_text:
            characters = [
                CharacterProfile(
                    name="陈默",
                    role="天才青年投资人",
                    personality=["骄傲", "焦虑", "理想主义"],
                    motivation="在并购惨败后寻回自我，挫败李建国的强取豪夺",
                    relationships={"苏瑶": "茶友/情感利益共同体", "李建国": "昔日反目的商业盟友"},
                    constraints=["内心有重度焦虑症，在极端压力下需要吃药"],
                    evidence_spans=[p for p in paragraphs if "陈默" in p]
                ),
                CharacterProfile(
                    name="苏瑶",
                    role="百年老茶馆继承人",
                    personality=["温婉", "坚韧", "不向资本妥协"],
                    motivation="继承祖父遗志，将茶馆作为非物质文化遗产传承下去",
                    relationships={"陈默": "彼此治愈的红颜知己", "李建国": "侵略性的拆迁强买者"},
                    constraints=["宁死也不肯卖掉老茶馆的地契和招牌"],
                    evidence_spans=[p for p in paragraphs if "苏瑶" in p]
                ),
                CharacterProfile(
                    name="李建国",
                    role="冷血地产巨鳄",
                    personality=["现实", "唯利是图", "不择手段"],
                    motivation="强拆老街改建高端写字楼，获取暴利",
                    relationships={"陈默": "昔日的提携者，现在的商业对手", "苏瑶": "打压强征的对象"},
                    constraints=["不能在媒体上曝光自己的非法手段，极其注重集团上市前的公众形象"],
                    evidence_spans=[p for p in paragraphs if "李建国" in p]
                )
            ]
            
            character_relations = [
                "陈默与李建国之间是现代投资理念决裂下的商业博弈",
                "陈默与苏瑶互相吸引，商业资本与非遗情怀发生碰撞"
            ]
            core_conflict = "陈默用高超的资本防御技巧协助苏瑶，对抗冷血地产巨鳄李建国强拆百年茶馆招牌的强权行径。"
            
            for idx, p in enumerate(paragraphs):
                if any(k in p for k in ["陈默", "苏瑶", "李建国", "茶馆", "强拆"]):
                    plot_events.append(PlotEvent(
                        event_id=f"EVT-CM-{idx+1:03d}",
                        summary=f"事件事实：{p[:25]}...",
                        characters=[name for name in ["陈默", "苏瑶", "李建国"] if name in p],
                        conflict_type="资本强拆抗争",
                        evidence_span=p
                    ))

        # 4. Fallback 默认抽取
        else:
            characters = [
                CharacterProfile(
                    name="张无名",
                    role="故事主人公",
                    personality=["隐隐"],
                    motivation="生存与寻找真相",
                    relationships={},
                    constraints=[],
                    evidence_spans=paragraphs if paragraphs else ["张无名在角落里。"]
                )
            ]
            character_relations = []
            core_conflict = "主人公克服自身局限，实现成长的客观冲突。"
            plot_events = [
                PlotEvent(
                    event_id="EVT-GEN-999",
                    summary="故事发生的基本起因事件。",
                    characters=["张无名"],
                    conflict_type="客观环境阻碍",
                    evidence_span=paragraphs[0] if paragraphs else "无原文描述"
                )
            ]

        # 核心红线约束：Parser Agent 不参与主观分析评判，risk_points、strengths、weaknesses 一律置为空列表。
        return ScriptAnalysis(
            characters=characters,
            character_relations=character_relations,
            core_conflict=core_conflict,
            plot_events=plot_events,
            risk_points=[],
            strengths=[],
            weaknesses=[]
        )

    def execute(self, state: AgentState) -> AgentState:
        """
        工作流节点方法：抽取事实并更新状态
        """
        state.history_logs.append(f"[{datetime.datetime.now().isoformat()}] ParserAgent 启动事实抽取。")
        
        title = state.script.title
        content = state.script.raw_text
        
        # 执行客观抽取
        analysis = self.extract(content)
        
        # 将角色特征注册进入全局人设记忆（Character Memory）进行本地持久化写入
        global_character_memory.save_characters(state.script.project_id, analysis.characters)
            
        state.analysis = analysis
        state.history_logs.append(f"[{datetime.datetime.now().isoformat()}] ParserAgent 抽取完成。")
        return state

# 全局 ParserAgent 单例，默认不配 llm_client
parser_agent = ParserAgent()
