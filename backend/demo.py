import streamlit as st
import httpx
import json

st.set_page_config(
    page_title="剧本评估 Multi-Agent 系统 Demo",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 剧本立项决策评估 Multi-Agent 系统")
st.markdown("---")

# 准备预设数据，方便用户快速点击测试
PRESETS = {
    "测试预设 1: 《破晓猎杀》(悬疑/动作)": {
        "project_id": "proj-901",
        "title": "破晓猎杀",
        "genre": "悬疑",
        "target_audience": "男性动作悬疑爱好者",
        "raw_text": "在边境小镇上，代号'风影'的特工林啸正在秘密追查跨国财阀首脑赵乾的军火走私线索。林啸潜入仓库搜集证据，同时面临着苏晴（天才黑客）的技术配合与敌人疯狂的包围网。故事充斥着极端的创伤回忆与爆炸场面。"
    },
    "测试预设 2: 《非遗茶香与金融风暴》(都市/商战)": {
        "project_id": "proj-902",
        "title": "非遗茶香与金融风暴",
        "genre": "都市",
        "target_audience": "针对非遗国潮与励志成长受众",
        "raw_text": "天才青年投资人陈默在经历并购惨败后，偶然结识了非遗茶文化继承人苏瑶。李建国强拆苏瑶的百年茶馆，陈默决定出手相助，通过金融杠杆与商业博弈，对抗强拆与强行收购，同时也在此过程中寻回了内心的宁静。"
    },
    "测试预设 3: 《林晚的复仇誓言》(都市/言情)": {
        "project_id": "proj-903",
        "title": "林晚的复仇誓言",
        "genre": "都市",
        "target_audience": "都市言情与商战受众",
        "raw_text": "女主角林晚为了查清父亲死亡真相复仇，与男主角沈氏集团总裁沈知行达成协议，两人进行契约婚姻，在商战与豪门争斗中联手应对背后的杀父仇人。"
    }
}

# 页面布局
col_left, col_right = st.columns([1, 2])

with col_left:
    st.subheader("📝 剧本大纲与属性输入")
    
    preset_choice = st.selectbox("选择测试样本预设进行快速填充", ["手动输入"] + list(PRESETS.keys()))
    
    # 根据预设填充数据
    init_pid = "proj-101"
    init_title = ""
    init_genre = "悬疑"
    init_audience = "大男频硬核动作片爱好者"
    init_text = ""
    
    if preset_choice != "手动输入":
        p_data = PRESETS[preset_choice]
        init_pid = p_data["project_id"]
        init_title = p_data["title"]
        init_genre = p_data["genre"]
        init_audience = p_data["target_audience"]
        init_text = p_data["raw_text"]
        
    project_id = st.text_input("项目唯一 ID (project_id)", value=init_pid)
    title = st.text_input("剧本标题", value=init_title, placeholder="如：破晓猎杀")
    genre = st.text_input("题材类型", value=init_genre, placeholder="如：悬疑 / 都市")
    target_audience = st.text_input("目标受众", value=init_audience, placeholder="如：男性，20-45岁，动作片爱好者")
    raw_text = st.text_area("剧本大纲 / 梗概正文", value=init_text, height=300, placeholder="请输入剧本故事大纲或分集梗概...")
    
    # 触发按钮
    start_eval = st.button("🚀 开始 Multi-Agent 评估", use_container_width=True)

with col_right:
    st.subheader("📊 评估决策与 Agent 链路流转结果")
    
    if start_eval:
        if not title or not raw_text:
            st.error("请输入剧本标题和剧本文本内容后再开始评估。")
        else:
            payload = {
                "project_id": project_id if project_id else "proj-temp",
                "title": title,
                "genre": genre,
                "target_audience": target_audience,
                "raw_text": raw_text,
                "user_preferences": []
            }
            
            with st.spinner("🤖 Multi-Agent 协调器正在调配 Parser -> Memory -> Analysis -> Retrieval -> Review 节点执行..."):
                try:
                    # 默认请求本地 8000 端口的 evaluate 接口
                    response = httpx.post("http://127.0.0.1:8000/evaluate", json=payload, timeout=30.0)
                    if response.status_code != 200:
                        st.error(f"评估失败，后端返回错误：{response.text}")
                    else:
                        report = response.json()
                        st.session_state["report"] = report
                        st.success("🎉 评估工作流执行完毕！")
                except Exception as e:
                    st.error(f"无法连接后端 FastAPI 评估接口，请确认您已运行 `uvicorn app.main:app`。 异常详情: {e}")
                    
    # 展示评估结果
    if "report" in st.session_state:
        report = st.session_state["report"]
        
        # 1. 顶部核心结果区
        decision = report.get("decision_suggestion", "REVISE")
        if decision == "PASS":
            st.success(f"### 最终立项建议：🟢 **{decision} (直接通过)**")
        elif decision == "REVISE":
            st.warning(f"### 最终立项建议：🟡 **{decision} (修改后通过)**")
        else:
            st.error(f"### 最终立项建议：🔴 **{decision} (拒绝立项)**")
            
        # 2. 四大评估维度打分展示
        st.markdown("#### 📐 多维度评估得分 (1-5)")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("人物人设评分", f"{report.get('character_score')}/5")
        c2.metric("剧情逻辑评分", f"{report.get('plot_logic_score')}/5")
        c3.metric("戏剧冲突评分", f"{report.get('conflict_density_score')}/5")
        c4.metric("市场契合评分", f"{report.get('market_fit_score')}/5")
        
        # 3. 详细评估分析页签
        st.markdown("---")
        tab_summary, tab_chars, tab_suggestions, tab_review, tab_trace, tab_json = st.tabs([
            "📝 执行摘要", 
            "👥 人物与冲突", 
            "💡 修改建议 & 风险", 
            "🛡️ Review 质检项",
            "🔗 Agent 轨迹 Trace",
            "📁 JSON 原始报告"
        ])
        
        with tab_summary:
            st.markdown("### 📝 项目评估执行摘要")
            st.text(report.get("executive_summary", ""))
            
        with tab_chars:
            st.markdown("### 👥 客观抽取的角色列表 (Parser Agent)")
            chars = report.get("characters", [])
            if not chars:
                st.info("未提取到角色信息。")
            else:
                for idx, c in enumerate(chars):
                    with st.expander(f"👤 角色 {idx+1}: {c.get('name')} ({c.get('role')})"):
                        st.markdown(f"**核心动机**: {c.get('motivation')}")
                        st.markdown(f"**性格标签**: {', '.join(c.get('personality', []))}")
                        st.markdown(f"**人设约束**: {', '.join(c.get('constraints', []))}")
                        st.markdown("**与其他角色的关系**:")
                        for k, v in c.get("relationships", {}).items():
                            st.markdown(f"- 与 **{k}**: {v}")
                            
            st.markdown("---")
            st.markdown("### 🎭 核心戏剧冲突 (Parser Agent)")
            st.info(report.get("core_conflict", "暂无核心冲突描述。"))
            
            st.markdown("---")
            st.markdown("### 🔗 人物关系概览")
            for rel in report.get("character_relations", []):
                st.markdown(f"- {rel}")
                
        with tab_suggestions:
            st.markdown("### 💡 可落地的修改与优化建议 (Analysis Agent)")
            for i, sug in enumerate(report.get("improvement_suggestions", [])):
                st.markdown(f"{i+1}. {sug}")
                
            st.markdown("---")
            col_pos, col_neg = st.columns(2)
            with col_pos:
                st.markdown("##### 🟢 剧本亮点 (Strengths)")
                for s in report.get("strengths", []):
                    st.markdown(f"- {s}")
            with col_neg:
                st.markdown("##### 🟡 剧本弱点 (Weaknesses)")
                for w in report.get("weaknesses", []):
                    st.markdown(f"- {w}")
                    
            st.markdown("---")
            st.markdown("##### ⚠️ 立项潜在风险点说明 (Risk Points)")
            for r in report.get("risk_points", []):
                st.markdown(f"- {r}")
                
            st.markdown("---")
            st.markdown("### 📚 同类作品对标证据 (Retrieval Agent)")
            evidences = report.get("evidence_list", [])
            if not evidences:
                st.info("本报告无引用的同类对标作品证据。")
            else:
                for idx, ev in enumerate(evidences):
                    st.markdown(f"**证据 #{idx+1}: 《{ev.get('source_title')}》** (题材: {ev.get('source_type')})")
                    st.markdown(f"- **相似内容/情境**: {ev.get('content')}")
                    st.markdown(f"- **对标理由**: {ev.get('relevance_reason')}")
                    st.markdown(f"- **检索相似度**: `{ev.get('score'):.2f}`")
                    st.markdown("")
                    
        with tab_review:
            st.markdown("### 🛡️ Review Agent 质检安全审核")
            issues = report.get("review_issues", [])
            if not issues:
                st.success("✅ Review Agent 质检通过：报告无偏见、幻觉或无依据论断。")
            else:
                st.error(f"❌ Review Agent 质检未通过：共发现 {len(issues)} 项不符合标准。")
                for idx, issue in enumerate(issues):
                    with st.container():
                        st.markdown(f"**问题 #{idx+1}: {issue.get('issue_type')}** (严重程度: `{issue.get('severity')}`)")
                        st.markdown(f"- **报告中有争议的断言 (Claim)**: *\"{issue.get('claim')}\"*")
                        st.markdown(f"- **被判定为问题的审查原因 (Reason)**: {issue.get('reason')}")
                        st.markdown(f"- **推荐的修改方案 (Suggested Fix)**: **{issue.get('suggested_fix')}**")
                        st.markdown("---")
                        
        with tab_trace:
            st.markdown("### 🔗 Multi-Agent 节点执行 Trace 链路")
            traces = report.get("node_traces", [])
            if not traces:
                st.info("未包含执行链路追踪信息。")
            else:
                st.markdown("以下为系统状态机执行的详细流程轨迹：")
                for idx, trace in enumerate(traces):
                    node_name = trace.get("node_name")
                    retry = trace.get("retry_count", 0)
                    retry_suffix = f" (重试轮次: {retry})" if retry > 0 else ""
                    
                    with st.expander(f"📌 步骤 {idx+1}: {node_name}{retry_suffix}"):
                        st.markdown(f"**节点输入摘要**:")
                        st.code(trace.get("input_summary"), language="text")
                        st.markdown(f"**节点输出/状态摘要**:")
                        st.code(trace.get("output_summary"), language="text")
                        if trace.get("errors"):
                            st.markdown(f"**❌ 错误捕获**:")
                            st.error(trace.get("errors"))
                            
        with tab_json:
            st.markdown("### 📁 最终评估报告 JSON 原始数据")
            st.json(report)
            
            # 下载按钮
            json_str = json.dumps(report, ensure_ascii=False, indent=2)
            st.download_button(
                label="📥 下载 JSON 评估报告",
                data=json_str,
                file_name=f"evaluation_report_{project_id}.json",
                mime="application/json",
                use_container_width=True
            )
    else:
        st.info("👈 请在左侧输入剧本属性和梗概，然后点击“开始评估”查看多 Agent 工作流执行结果。")
