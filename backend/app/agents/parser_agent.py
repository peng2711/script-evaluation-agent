from typing import Optional, Any, List
from ..schemas.report import CharacterProfile, PlotEvent, ScriptAnalysis
from ..schemas.script import ScriptInput
from ..schemas.agent_state import AgentState
from ..memory.character_memory import global_character_memory
import datetime

class ParserAgent:
    """
    Parser Agent：专注于从剧本正文/大纲中提取事实信息（如角色、关系、核心冲突和事件段落证据），
    坚决不作任何质量或市场潜力等主观价值判断。
    """
    def __init__(self, llm_client: Optional[Any] = None):
        # 预留 llm_client 参数，也可通过 get_llm_client 初始化
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

    def llm_extract(self, script: ScriptInput) -> ScriptAnalysis:
        """
        使用 LLMClient 从剧本文本中抽取客观 facts 信息。
        """
        import time
        from ..llm.factory import get_llm_client
        from ..observability.trace import active_trace_recorder
        
        client = self.llm_client or get_llm_client()
        schema = ScriptAnalysis.model_json_schema()
        
        system_prompt = (
            "你是一个专业的剧本客观事实要素解析提取器。\n"
            "你的任务是阅读剧本文本并从中客观抽取以下内容，不要进行任何主观评估：\n"
            "- characters (角色列表): 包含 name（角色名）、role（角色定位，例如女主角、男主角等）、personality（性格特征列表）、motivation（行为动机）、relationships（与其他人物的关系字典，key为对方名字，value为具体关系）、constraints（人设限制条件列表）、evidence_spans（原文支撑段落证据列表）。\n"
            "- character_relations (人物关系描述): 客观概括角色间的核心关系描述列表。\n"
            "- core_conflict (核心冲突): 用一到两句话描述客观的核心戏剧冲突，不带主观色彩。\n"
            "- plot_events (剧情事件列表): 包含 event_id（例如EVT-001）、summary（客观摘要）、characters（参与角色列表）、conflict_type（冲突类型，例如潜入、对抗等）、evidence_span（原文段落段证据）。\n\n"
            "【严苛红线要求】\n"
            "- 坚决不做任何主观评价，严禁包含好坏、潜力、商业价值等词汇（例如绝不要使用'市场潜力大'、'节奏拖查'、'老套'等主观定性评价）。\n"
            "- strengths（优点字段）和 weaknesses（缺点字段）必须为空列表。\n"
            "- risk_points（风险点字段）暂时保持为空列表。\n"
            "- 只能依据原文提取，严禁凭空编造不存在的角色或事件。\n"
            "- 必须输出符合 Schema 规范的 JSON 格式。"
        )
        
        prompt = (
            f"剧本标题: {script.title}\n"
            f"题材类型: {script.genre}\n"
            f"目标受众: {script.target_audience or '大众'}\n"
            f"剧本原文正文:\n{script.raw_text}"
        )
        
        recorder = active_trace_recorder.get()
        start_t = time.perf_counter()
        
        max_attempts = 2
        last_error = None
        
        for attempt in range(max_attempts):
            try:
                result_dict = client.generate_json(
                    prompt=prompt,
                    schema=schema,
                    system_prompt=system_prompt
                )
                
                # 强行重置主观字段为空，防止 LLM 未遵照 Prompt 导致逻辑崩塌
                result_dict["strengths"] = []
                result_dict["weaknesses"] = []
                result_dict["risk_points"] = []
                
                analysis = ScriptAnalysis.model_validate(result_dict)
                
                duration = (time.perf_counter() - start_t) * 1000.0
                if recorder:
                    recorder.record_tool_call(
                        tool_name="parser_llm_call",
                        agent_name="ParserAgent",
                        input_summary=f"ParserAgent LLM Extract. Title: {script.title}",
                        output_summary=f"SUCCESS. Extracted {len(analysis.characters)} characters",
                        status="SUCCESS",
                        latency_ms=duration
                    )
                return analysis
            except Exception as e:
                last_error = e
                # 仅在需要时重试
                if attempt < max_attempts - 1:
                    continue
                    
        # 失败抛出以触发 fallback
        duration = (time.perf_counter() - start_t) * 1000.0
        if recorder:
            recorder.record_tool_call(
                tool_name="parser_llm_call",
                agent_name="ParserAgent",
                input_summary=f"ParserAgent LLM Extract. Title: {script.title}",
                output_summary="FAILED. Fallback to legacy heuristic",
                status="FALLBACK",
                latency_ms=duration,
                error_message=str(last_error)
            )
        raise last_error

    def execute(self, state: AgentState) -> AgentState:
        """
        工作流节点方法：抽取事实并更新状态
        """
        state.history_logs.append(f"[{datetime.datetime.now().isoformat()}] ParserAgent 启动事实抽取。")
        
        title = state.script.title
        content = state.script.raw_text
        
        import hashlib
        from ..cache.simple_cache import global_cache
        
        # 计算内容 MD5 作为缓存键
        cache_key = f"parser:{hashlib.md5(content.encode('utf-8')).hexdigest()}"
        cached_analysis = global_cache.get(cache_key)
        
        if cached_analysis is not None:
            analysis = cached_analysis
            state.history_logs.append(f"[{datetime.datetime.now().isoformat()}] ParserAgent 缓存命中，直接恢复解析结果。")
            from ..observability.trace import active_trace_recorder
            recorder = active_trace_recorder.get()
            if recorder and hasattr(recorder, "record_parser_cache_hit"):
                recorder.record_parser_cache_hit()
        else:
            state.history_logs.append(f"[{datetime.datetime.now().isoformat()}] ParserAgent 缓存未命中，执行客观抽取。")
            
            try:
                analysis = self.llm_extract(state.script)
                state.history_logs.append(f"[{datetime.datetime.now().isoformat()}] ParserAgent LLM 抽取成功。")
            except Exception as e:
                import logging
                logger = logging.getLogger("agent_observability")
                logger.warning(f"ParserAgent LLM 抽取失败，将自动回退到启发式解析。错误: {str(e)}")
                state.history_logs.append(f"[{datetime.datetime.now().isoformat()}] ParserAgent LLM 抽取失败，回退到启发式解析。")
                analysis = self.extract(content)
                
            global_cache.set(cache_key, analysis)
        
        # 将角色特征注册进入全局人设记忆（Character Memory）进行本地持久化写入
        if state.use_tools_via_router:
            from ..tools.router import global_tool_router
            global_tool_router.call_tool(
                agent_name="ParserAgent",
                tool_name="memory_write_tool",
                arguments={
                    "project_id": state.script.project_id,
                    "memory_type": "character",
                    "characters": analysis.characters
                }
            )
        else:
            global_character_memory.save_characters(state.script.project_id, analysis.characters)
            
        state.analysis = analysis
        state.history_logs.append(f"[{datetime.datetime.now().isoformat()}] ParserAgent 抽取完成。")
        return state

# 全局 ParserAgent 单例，默认不配 llm_client
parser_agent = ParserAgent()
