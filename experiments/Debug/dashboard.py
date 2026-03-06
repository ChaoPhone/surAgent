# File: Debug/dashboard.py
import streamlit as st
import json
import time
import os
import pandas as pd
import altair as alt
import streamlit.components.v1 as components

# === 页面配置 ===
st.set_page_config(
    page_title="SurAgent Command Center",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# === 样式定制 ===
st.markdown("""
<style>
    :root {
        --metric-bg: #ffffff;
        --metric-label: #6c6f7f;
        --metric-value: #0f1c2e;
        --metric-delta-positive: #0f9d58;
        --metric-delta-negative: #d93025;
        --metric-delta-icon: currentColor;
        --metric-border: 1px solid #e6e9ef;
        --metric-border-radius: 0.5rem;
        --metric-padding: 1rem;
        --card-bg: #ffffff;
        --card-border-left: #00ADB5;
        --card-text: #0f1c2e; 
    }
    @media (prefers-color-scheme: dark) {
        :root {
            --metric-bg: #1e1e1e;
            --metric-label: #b0b3b8;
            --metric-value: #e4e6eb;
            --metric-delta-positive: #81c995;
            --metric-delta-negative: #f28b82;
            --metric-border: 1px solid #3a3b3d;
            --card-bg: #1e1e1e;
            --card-border-left: #00ADB5;
            --card-text: #e4e6eb;
        }
    }
    [data-testid="stMetric"] {
        background-color: var(--metric-bg);
        border: var(--metric-border);
        border-radius: var(--metric-border-radius);
        padding: var(--metric-padding);
        transition: background-color 0.3s ease, border-color 0.3s ease;
    }

    [data-testid="stMetricLabel"] {
        color: var(--metric-label) !important;
        font-size: 0.9rem !important;
        font-weight: 400 !important;
    }

    [data-testid="stMetricValue"] {
        color: var(--metric-value) !important;
        font-size: 2rem !important;
        font-weight: 600 !important;
    }

    [data-testid="stMetricDelta"] {
        color: var(--metric-delta) !important;
        font-size: 0.9rem !important;
    }
    [data-testid="stMetricDelta"] svg {
        fill: currentColor;
    }
    [data-testid="stMetricDelta"][data-testid="stMetricDelta-positive"] {
        color: var(--metric-delta-positive) !important;
    }
    [data-testid="stMetricDelta"][data-testid="stMetricDelta-negative"] {
        color: var(--metric-delta-negative) !important;
    }
    .agent-stat-card {
        background-color: var(--card-bg);
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid var(--card-border-left);
        color: var(--card-text);
        transition: background-color 0.3s ease, border-color 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)


# === 数据加载 ===
def load_data():
    path = os.path.join("Debug", "run_state.json")
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return None


data = load_data()

# 自动刷新 (2s)
if not data:
    st.warning("📡 等待系统信号...")
    time.sleep(2)
    st.rerun()

# ==============================================================================
# 1. 顶层：极简 HUD
# ==============================================================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    last_active = data.get("last_active_time", time.time())
    diff = int(time.time() - last_active)
    label = "🟢 运行中" if diff < 15 else "🔴 已挂起"
    st.metric("系统心跳", f"{label}", f"{diff}s 前刷新", height = 128)

with col2:
    st.metric("Token 总量", f"{data.get('token_total', 0):,}", height = 128)

with col3:
    start_time = data.get("system_start_time", time.time())
    run_duration = int(time.time() - start_time)
    m, s = divmod(run_duration, 60)
    st.metric("运行时间", f"{m}分 {s}秒", height = 128)

with col4:
    st.metric("当前执政", data.get("current_agent", "System"), height = 128)

st.divider()

# ==============================================================================
# 2. 核心层：战术指挥台 (Tactical Command)
# ==============================================================================
col_map, col_inspector = st.columns([1.5, 1])

# --- 左侧：动态拓扑图 ---
with col_map:
    st.subheader("协作拓扑")

    trace = data.get("sequence_trace", [])
    parallel_history = data.get("parallel_history", [])
    current_agent = data.get("current_agent", "")

    # 构建 Mermaid
    mermaid_code = "graph TD\n"
    mermaid_code += "  Start((🚀)) --> Summoner\n"

    # 绘制主干
    # 简化：只显示最近的链路，避免图过大
    display_trace = trace[-8:] if len(trace) > 8 else trace
    if len(trace) > 8:
        mermaid_code += f"  Previous[...] --> {display_trace[0]}\n"

    for i in range(len(display_trace) - 1):
        mermaid_code += f"  {display_trace[i]} --> {display_trace[i + 1]}\n"

    # 绘制最新的并行子图
    if parallel_history:
        latest = parallel_history[-1]
        manager = latest['manager']
        mermaid_code += f"\n  subgraph Parallel_Batch [⚡ {manager} 的子任务]\n"
        mermaid_code += "  direction TB\n"
        for task in latest['tasks']:
            role = task['role'].replace(" ", "_")  # 安全清洗
            mermaid_code += f"    {manager} -.-> {role}({role})\n"

            # 状态染色 (根据 agent_stats)
            stats = data.get("agent_stats", {}).get(task['role'], {})
            status = stats.get("status", "idle")
            if status == "finished":
                mermaid_code += f"    style {role} fill:#4CAF50,stroke:#fff;\n"
            elif status == "error":
                mermaid_code += f"    style {role} fill:#F44336,stroke:#fff;\n"
            else:
                mermaid_code += f"    style {role} fill:#FFEB3B,stroke:#333,color:#000;\n"
        mermaid_code += "  end\n"

    # 高亮当前
    if current_agent:
        mermaid_code += f"  style {current_agent} fill:#FF5722,stroke:#fff,stroke-width:4px;\n"

    # 渲染
    mermaid_html = f"""
        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            mermaid.initialize({{ startOnLoad: true, theme: 'dark' }});
        </script>
        <div class="mermaid" style="text-align: center;">
            {mermaid_code}
        </div>
    """
    components.html(mermaid_html, height=350, scrolling=True)

# --- 右侧：审查面板 (Inspector) ---
with col_inspector:
    st.subheader("节点审查")

    # 1. 获取所有已知 Agent
    all_agents = list(data.get("agent_stats", {}).keys())
    # 加上 Profile 里有的但可能还没跑数据的
    all_agents += list(data.get("agent_profiles", {}).keys())
    all_agents = sorted(list(set(all_agents)))

    if not all_agents:
        st.info("暂无 Agent 活跃数据")
    else:
        # 联动选择器
        selected_agent = st.selectbox("🔍 选择要审查的 Agent", all_agents, index=0)

        # 读取数据
        stats = data.get("agent_stats", {}).get(selected_agent, {})
        profile = data.get("agent_profiles", {}).get(selected_agent, {})

        # 展示卡片
        st.markdown(f"""
        <div class="agent-stat-card">
            <h3>🤖 {selected_agent}</h3>
            <div><strong>Status:</strong> {stats.get('status', 'Unknown')}</div>
            <div><strong>Last Active:</strong> {time.strftime('%H:%M:%S', time.localtime(stats.get('last_seen', 0))) if stats else 'N/A'}</div>
            <hr style="border-color: #444;">
            <div style="display: flex; justify-content: space-between;">
                <span style="color: #42A5F5;">📥 Input: {stats.get('input', 0):,}</span>
                <span style="color: #FFA726;">📤 Output: {stats.get('output', 0):,}</span>
            </div>
            <div style="text-align: right; font-weight: bold; margin-top: 5px;">
                Total: {stats.get('tokens', 0):,}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 展示 Prompt
        if profile:
            with st.expander("查看完整指令", expanded=False):
                st.markdown(f"**Temp:** `{profile.get('temperature')}` | **Model:** `{profile.get('model')}`")
                st.code(profile.get('instruction', 'No instruction recorded'), language="markdown")
        else:
            st.caption("*该 Agent 为系统预设或尚未被并行调度捕获，暂无 Prompt 记录*")

# ==============================================================================
# 3. 资源透视 (堆叠柱状图)
# ==============================================================================
st.subheader("资源消耗透视")

if data.get("agent_stats"):
    # 数据转换：Flat Map
    chart_data = []
    for name, s in data["agent_stats"].items():
        chart_data.append({"Agent": name, "Type": "Input", "Tokens": s.get("input", 0)})
        chart_data.append({"Agent": name, "Type": "Output", "Tokens": s.get("output", 0)})

    df_chart = pd.DataFrame(chart_data)

    # Altair 堆叠图
    chart = alt.Chart(df_chart).mark_bar().encode(
        x=alt.X('Agent', title=None, sort='-y'),
        y=alt.Y('Tokens', title='Token Count'),
        color=alt.Color('Type', scale=alt.Scale(domain=['Input', 'Output'], range=['#42A5F5', '#FFA726'])),
        tooltip=['Agent', 'Type', 'Tokens']
    ).properties(height=250, width='container')

    st.altair_chart(chart, width="content")

# ==============================================================================
# 4. 日志层：黑客终端
# ==============================================================================
st.divider()
st.subheader("实时信号流")

logs = data.get("logs", [])[-30:]  # 显示最后30条
log_html = """
<div style="background-color: #000; padding: 15px; border-radius: 5px; height: 300px; overflow-y: auto;">
    <style>
        .terminal-log { font-family: 'Courier New', monospace; font-size: 13px; line-height: 1.5; }
        .log-time { color: #569cd6; margin-right: 10px; }
        .log-agent-TechLead { color: #E65100; font-weight: bold; }
        .log-agent-Summoner { color: #B71C1C; font-weight: bold; }
        .log-agent-System { color: #607D8B; }
        .log-agent-Worker { color: #2E7D32; }
    </style>
"""

for log in reversed(logs):
    # 兼容旧日志
    if isinstance(log, str): continue

    t = log.get('time', '')
    a = log.get('agent', 'System')
    act = log.get('action', '')

    # 颜色映射
    color_class = "log-agent-Worker"
    if a == "TechLead":
        color_class = "log-agent-TechLead"
    elif a == "Summoner":
        color_class = "log-agent-Summoner"
    elif a == "System":
        color_class = "log-agent-System"

    log_html += f"""
    <div class="terminal-log">
        <span class="log-time">[{t}]</span>
        <span class="{color_class}">{a}</span>: 
        <span style="color: #d4d4d4;">{act}</span>
    </div>
    """
log_html += '</div>'
# print(log_html)
components.html(log_html, height = 300)

st.divider()
st.subheader("全局黑板")
st.markdown("<br>", unsafe_allow_html=True)
with st.expander("点击展开/收起", expanded=False):
    bb = data.get("blackboard", {})
    if bb:
        st.json(bb)
    else:
        st.caption("黑板暂无数据")

# 自动刷新
time.sleep(2)
st.rerun()