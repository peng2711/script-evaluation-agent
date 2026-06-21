from ..schemas.agent_state import AgentState
from ..schemas.report import Character, CharacterRelation, PlotEvent, Conflict, RoleType
from ..memory.character_memory import global_character_memory
import datetime

class ParserAgent:
    """
    Parser Agent (Mock 实现)：模拟将剧本大纲或正文内容解析，提取出角色设定、关系网络、关键事件与核心冲突。
    """
    def execute(self, state: AgentState) -> AgentState:
        state.history_logs.append(f"[{datetime.datetime.now().isoformat()}] ParserAgent 开始执行解析。")
        
        title = state.script.title
        content = state.script.content
        genre = state.script.genre or "通用"
        
        # 1. 尝试从文本中探测角色。如果文本中包含某些关键词，我们将动态提取它们，模拟 NLP 命名实体识别过程。
        characters = []
        relations = []
        events = []
        conflicts = []
        
        # 探测特征字，提供更灵动的 mock 体验
        if "林啸" in content or "赵乾" in content:
            characters = [
                Character(name="林啸", role=RoleType.PROTAGONIST, description="代号'风影'的特工，冷静、机智，身上背负着沉重的过去。"),
                Character(name="赵乾", role=RoleType.ANTAGONIST, description="跨国财阀首脑，表面是大慈善家，暗地里是军火走私集团头目。"),
                Character(name="苏晴", role=RoleType.SUPPORTING, description="天才黑客，林啸的技术支援，活泼且有正义感。")
            ]
            relations = [
                CharacterRelation(source_character="林啸", target_character="赵乾", relation_type="敌对", description="林啸追查多年的灭门仇人，两人多次展开生死较量。"),
                CharacterRelation(source_character="林啸", target_character="苏晴", relation_type="盟友", description="苏晴多次利用黑客技术协助林啸脱险，彼此绝对信任。")
            ]
            events = [
                PlotEvent(title="破晓行动", description="林啸潜入赵乾的机密仓库，搜集到了核心交易证据。", significance="引爆了全剧的戏剧冲突，赵乾开始全城通缉林啸。"),
                PlotEvent(title="黑客遭遇战", description="苏晴在帮林啸传输文件时被赵乾的网络安全官锁定，险些暴露位置。", significance="增加了情节紧迫感，促使林啸必须尽快收网。")
            ]
            conflicts = [
                Conflict(description="林啸的复仇与正义追求，同赵乾庞大的资本与黑道势力之间的对决", characters_involved=["林啸", "赵乾"]),
                Conflict(description="苏晴在技术入侵过程中面临的良知与自身安全的抉择", characters_involved=["苏晴"])
            ]
        elif "陈默" in content or "苏瑶" in content:
            characters = [
                Character(name="陈默", role=RoleType.PROTAGONIST, description="天才青年投资人，因一次失败的并购案背负巨债，誓要东山再起。"),
                Character(name="苏瑶", role=RoleType.PROTAGONIST, description="传统茶文化继承人，性格温和坚韧，拥有一家百年老茶馆。"),
                Character(name="李建国", role=RoleType.SUPPORTING, description="陈默的前期投资合伙人，商业利益至上的现实主义者。")
            ]
            relations = [
                CharacterRelation(source_character="陈默", target_character="苏瑶", relation_type="恋人/合伙人", description="从最初的商业利用，到最后共同保护茶馆，两人产生深厚情感。"),
                CharacterRelation(source_character="陈默", target_character="李建国", relation_type="昔日盟友/对手", description="因商业理念不合而决裂，李建国试图强行收购苏瑶的茶馆。")
            ]
            events = [
                PlotEvent(title="茶馆危机", description="李建国带拆迁队上门，要求茶馆限期搬迁，陈默出面阻拦。", significance="激化了陈默与李建国的商业冲突，也是陈默与苏瑶感情升温的关键点。")
            ]
            conflicts = [
                Conflict(description="陈默代表的现代资本运作家值理念，同苏瑶坚守的传统非遗文化传承之间的碰撞", characters_involved=["陈默", "苏瑶"]),
                Conflict(description="陈默与李建国在商业道德和个人利益之间的决裂博弈", characters_involved=["陈默", "李建国"])
            ]
        else:
            # 默认 fallback mock 数据
            characters = [
                Character(name="张无名", role=RoleType.PROTAGONIST, description=f"故事的主人公，在题材 '{genre}' 扮演核心角色。"),
                Character(name="李暗影", role=RoleType.ANTAGONIST, description="阻碍主人公达成目标的对手/反派。")
            ]
            relations = [
                CharacterRelation(source_character="张无名", target_character="李暗影", relation_type="敌对", description="李暗影的设计打压，逼迫张无名一步步走向反抗。")
            ]
            events = [
                PlotEvent(title="冲突爆发", description="张无名与李暗影发生了正面摩擦，揭示了核心矛盾。", significance="正式拉开整个故事的大幕。")
            ]
            conflicts = [
                Conflict(description="主人公努力打破现状的愿望，与对手维护旧秩序之间的碰撞冲突", characters_involved=["张无名", "李暗影"])
            ]

        # 2. 将人设写入人设记忆 (Character Memory) 以保持后续的一致性
        for char in characters:
            global_character_memory.update_character_profile(
                project_title=title,
                name=char.name,
                role=char.role.value,
                description=char.description
            )
            
        state.parsed_characters = characters
        state.parsed_relations = relations
        state.parsed_events = events
        state.parsed_conflicts = conflicts
        
        state.history_logs.append(f"[{datetime.datetime.now().isoformat()}] ParserAgent 解析完成。提取出 {len(characters)} 个角色，{len(events)} 个关键事件。")
        return state

# 全局 ParserAgent 单例
parser_agent = ParserAgent()
