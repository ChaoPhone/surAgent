import json
import os
import time
import streamlit as st
import streamlit.components.v1 as components

# 1. 页面配置 (必须是第一个 Streamlit 命令)
st.set_page_config(page_title="Swarm Monitor", layout="wide", page_icon="🐝")

# 自动刷新状态初始化
if 'last_update' not in st.session_state:
    st.session_state.last_update = time.time()


def load_data():
    """加载监控数据"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(current_dir, "run_state.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None


def render_snake_mermaid(sequence_trace):
    """
    生成紧凑的“蛇形”Mermaid 流程图代码
    """
    if not sequence_trace:
        return "graph TB; N0[Waiting for Data...];"

    # --- 样式定义 ---
    styles = {
        "Summoner": "#ff9900",  # 橙
        "Architect": "#00ccff",  # 蓝
        "Developer": "#00cc99",  # 绿
        "Inspector": "#9933ff",  # 紫
        "Pruner": "#ff3366",  # 红
        "Default": "#999999"  # 灰
    }

    emoji_map = {
        "Summoner": "🧙‍♂️", "Architect": "📐", "Developer": "👨‍💻",
        "Inspector": "🕵️‍♂️", "Pruner": "✂️"
    }

    # 基础图表定义
    mermaid_code = "graph TB;\n"

    # 注入样式类
    for role, color in styles.items():
        mermaid_code += f"classDef {role} fill:{color},stroke:#fff,stroke-width:2px,color:white,rx:5,ry:5,shadow:shadow;\n"

    # --- 核心：蛇形折返算法 ---
    ROW_SIZE = 8  # 每行显示的节点数量 (根据屏幕宽度调整)

    # 将 trace 切分为多行
    chunks = [sequence_trace[i:i + ROW_SIZE] for i in range(0, len(sequence_trace), ROW_SIZE)]

    links = []
    global_index = 0

    for row_idx, chunk in enumerate(chunks):
        # 偶数行从左到右 (LR)，奇数行从右到左 (RL)
        direction = "LR" if row_idx % 2 == 0 else "RL"

        mermaid_code += f"subgraph Row{row_idx}\n direction {direction}\n"

        row_node_ids = []
        for agent in chunk:
            node_id = f"N{global_index}"
            role_style = agent if agent in styles else "Default"
            emoji = emoji_map.get(agent, "🤖")

            # 定义节点: N1["emoji AgentName"]:::Style
            mermaid_code += f'{node_id}["{emoji} {agent}"]:::{role_style};\n'
            row_node_ids.append(node_id)
            global_index += 1

        # 行内连接 (A --> B)
        # 注意：Mermaid 的 RL 模式会自动反向渲染，所以逻辑连接顺序始终是正向的
        if len(row_node_ids) > 1:
            mermaid_code += " --> ".join(row_node_ids) + ";\n"

        mermaid_code += "end\n"  # 结束 subgraph

        # --- 行间连接 (连接上一行的尾巴 -> 当前行的头) ---
        if row_idx > 0:
            # 上一行的最后一个节点 ID
            prev_last_id = f"N{row_idx * ROW_SIZE - 1}"
            # 当前行的第一个节点 ID
            curr_first_id = f"N{row_idx * ROW_SIZE}"
            links.append(f"{prev_last_id} --> {curr_first_id}")

    # 添加所有的跨行连接
    if links:
        mermaid_code += "\n".join(links) + ";\n"

    # 封装 HTML
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.esm.min.mjs';
            mermaid.initialize({{ 
                startOnLoad: true, 
                theme: 'base', 
                flowchart: {{ curve: 'monotoneY', padding: 15 }} 
            }});
        </script>
    </head>
    <body style="background-color: transparent;">
        <div class="mermaid" style="display: flex; justify-content: center; width: 100%;">
            {mermaid_code}
        </div>
    </body>
    </html>
    """
    return html_code


# --- 主界面逻辑 ---

st.title("🐝 Swarm Agent 蜂群监控中心")

data = load_data()

if not data:
    st.warning("⏳ 等待数据初始化... (请先运行 main.py)")
    time.sleep(2)
    st.rerun()

# 1. 顶部 KPI 指标
k1, k2, k3 = st.columns(3)
k1.metric("🤖 当前执行者", data.get("current_agent", "Idle"))
k2.metric("🪙 Token 总耗", f"{data.get('total_tokens', 0):,}")
k3.metric("⏱️ 最后活跃", time.strftime('%H:%M:%S', time.localtime(data.get('last_active_time', 0))))

st.divider()

# 2. 核心布局：左侧 (图表+日志) vs 右侧 (黑板)
# 比例调整为 1.8 : 1.2，给黑板更多空间
col_left, col_right = st.columns([1.8, 1.2])

with col_left:
    st.subheader("🐍 协作追踪 (Snake Timeline)")
    trace = data.get("sequence_trace", [])
    # 渲染 Mermaid
    if trace:
        html = render_snake_mermaid(trace)
        components.html(html, height=450, scrolling=True)
    else:
        st.info("暂无交互记录")

    st.subheader("📜 运行日志 (最近200条)")
    logs = data.get("logs", [])
    if logs:
        # 倒序排列，让最新的显示在最上面
        log_text = "\n".join(reversed(logs))
        st.text_area("Live Logs", log_text, height=400, disabled=True)
    else:
        st.info("暂无日志")

with col_right:
    st.subheader("📋 项目黑板 (Blackboard)")
    blackboard = data.get("blackboard", {})

    if not blackboard:
        st.info("黑板暂无内容 (Waiting for Architect...)")
    else:
        # 遍历展示黑板上的所有 Key
        for key, content in blackboard.items():
            # 默认展开重要的 manifest
            is_expanded = (key == "project_manifest")

            with st.expander(f"📌 {key}", expanded=is_expanded):
                if isinstance(content, str):
                    # 如果内容是代码或 Markdown，进行高亮渲染
                    if len(content) > 2000:
                        st.caption(f"⚠️ 内容过长，仅展示前 2000 字符 (Total: {len(content)})")

                    # 根据 key 推测语言类型
                    lang = "markdown" if "manifest" in key else "python"
                    if "json" in key or content.strip().startswith("{"):
                        lang = "json"

                    st.code(content[:2000], language=lang)
                else:
                    # 如果是结构化数据（字典/列表），直接显示 JSON
                    st.json(content)

# 3. 自动刷新机制 (每 2 秒)
time.sleep(2)
st.rerun()