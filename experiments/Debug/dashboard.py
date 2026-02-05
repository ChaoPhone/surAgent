import streamlit as st
import streamlit.components.v1 as components
import json
import time
import os

# 页面配置
st.set_page_config(page_title="Swarm Monitor", layout="wide", page_icon="🐝")

# 自动刷新逻辑
if 'last_update' not in st.session_state:
    st.session_state.last_update = time.time()


def load_data():
    # 使用绝对路径，防止找不到文件
    current_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(current_dir, "run_state.json")

    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None


# --- Mermaid 渲染函数 (核心修改：蛇形时间轴版) ---
def render_mermaid(sequence_trace):
    """
    生成按时间顺序排列的“蛇形”流程图。
    """
    if not sequence_trace:
        return "暂无数据"

    # 1. 定义布局方向 (TB: 从上到下，适合长流程)
    mermaid_code = "graph TB;\n"

    # 2. 【核心配置】定义角色样式 (颜色 + Emoji)
    # 使用 CSS 类定义颜色
    styles = {
        "Summoner": {"fill": "#ff9900", "emoji": "🧙‍♂️"},  # 橙色
        "Architect": {"fill": "#00ccff", "emoji": "📐"},  # 天蓝
        "Developer": {"fill": "#00cc99", "emoji": "👨‍💻"},  # 青绿
        "Inspector": {"fill": "#9933ff", "emoji": "🕵️‍♂️"},  # 紫色
        "Default": {"fill": "#999999", "emoji": "❓"}  # 灰色
    }

    # 生成 Mermaid 样式定义 (classDef)
    for role, style in styles.items():
        # 定义样式类，设置背景色、白色文字、圆角边框
        mermaid_code += f"classDef {role} fill:{style['fill']},stroke:#fff,stroke-width:2px,color:white,rx:5,ry:5;\n"

    # 3. 【核心逻辑】生成链式节点
    # 为了让 Mermaid 画出长蛇，而不是环状图，
    # 每一个步骤都必须是一个独一无二的节点 ID (例如 N1, N2, N3...)
    node_ids = []
    for i, agent_name in enumerate(sequence_trace):
        node_id = f"N{i}"  # 生成唯一ID
        node_ids.append(node_id)

        # 获取对应的样式和 Emoji
        style_config = styles.get(agent_name, styles["Default"])
        emoji = style_config["emoji"]
        # 节点定义：N1["🧙‍♂️ Summoner"]:::Summoner
        mermaid_code += f'{node_id}["{emoji} {agent_name}"]:::{agent_name};\n'

    # 4. 绘制连接线 (N0 --> N1 --> N2 ...)
    # 使用粗箭头 (==>) 增加视觉冲击力
    mermaid_code += " ==> ".join(node_ids) + ";\n"

    # 5. 封装 HTML
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script type="module">
            // 使用最新版 Mermaid 以支持更好的样式
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.esm.min.mjs';
            mermaid.initialize({{ 
                startOnLoad: true,
                theme: 'base', // 使用基础主题以便自定义样式覆盖
                flowchart: {{ curve: 'monotoneY' }} // 使用平滑曲线
            }});
        </script>
        <style>
            /* 调整容器样式让图像居中 */
            .mermaid {{ 
                display: flex; 
                justify-content: center; 
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="mermaid">
            {mermaid_code}
        </div>
    </body>
    </html>
    """
    return html_code


# --- 主界面逻辑 ---

st.title("🐝 Swarm Agent 实时监控面板")

data = load_data()

if not data:
    st.warning("⏳ 等待主程序启动... (正在扫描 Debug/run_state.json)")
    time.sleep(2)
    st.rerun()

# 1. 顶部 KPI 指标
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("🤖 当前主角", data.get("current_agent", "Unknown"))
kpi2.metric("🪙 Token 消耗", f"{data.get('total_tokens', 0):,}")
kpi3.metric("💸 预估成本 ($)", f"{data.get('cost_estimate', 0):.6f}")

st.divider()

# 2. 中间：拓扑图与日志
col_graph, col_logs = st.columns([2, 1])
with col_graph:
    st.subheader("🐍 交互时间轴 (Snake Timeline)")
    # 【修改点】从 data 中读取 sequence_trace
    trace = data.get("sequence_trace", [])

    # 【修改点】调用新的渲染函数
    html_chart = render_mermaid(trace)

    # 渲染 HTML，增加高度以适应长流程
    components.html(html_chart, height=450, scrolling=True)
with col_logs:
    st.subheader("实时交互日志")
    logs = data.get("logs", [])
    # 容器高度固定，内部滚动
    with st.container(height=300):
        for log in reversed(logs):
            st.text(log)

# 3. 自动刷新 (每 2 秒)
time.sleep(2)
st.rerun()