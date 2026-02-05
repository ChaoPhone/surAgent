
---

# 🐝 Swarm Agent Framework (v0.2: The Trinity / 三位一体)

### 🚀 核心摘要 (Executive Summary)

**Swarm Agent Framework** 是一个基于 **“蜂群架构”** 的轻量级多智能体协作开发框架。

v0.2 版本（代号：*The Trinity*）针对代码一致性和 Token 消耗进行了重大重构。我们将原来的前后端工兵合并为全栈开发者，引入了“手术刀”式的代码修改能力，并新增了基于 Streamlit 的实时可视化监控面板。

**核心特性：**

* **🧙‍♂️ 角色重组**：确立了 **架构师 (Design)** -> **全栈开发 (Build)** -> **质检官 (Test)** 的铁三角闭环。
* **📉 降本增效**：Agent 学会了使用 `replace_file_lines` 进行按行修改，不再全量重写文件，Token 消耗降低 90%。
* **📊 实时监控**：内置 Streamlit 仪表盘，支持 Mermaid 动态拓扑图，实时显示 Agent 思考路径与 Token 计费。
* **🛠️ 强一致性**：全栈 Developer 独自负责前后端对接，彻底解决变量名不一致（Interface Mismatch）问题。

---

### 🏛️ 架构设计 (Architecture)

#### 1. 角色分工 (The Roles)

| 图标 | 角色名 | 职能描述 | 核心技能 |
| --- | --- | --- | --- |
| 🧙‍♂️ | **Summoner** | **项目经理**。维护有限状态机 (FSM)，负责任务分发与进度把控，不亲自写代码。 | 调度 (`dispatch`), 验收 (`mark_complete`) |
| 📐 | **Architect** | **顶层设计**。负责定义文件树结构、技术选型和 API 接口契约。 | 读写黑板, 列出目录 |
| 👨‍💻 | **Developer** | **全栈执行**。v0.2 核心角色。负责从后端逻辑到前端 UI 的所有代码实现，确保接口对齐。 | **精准修改 (`replace_lines`)**, 写文件, 联网搜索 |
| 🕵️‍♂️ | **Inspector** | **质量保证**。负责运行代码、执行测试脚本。拥有“一票否决权”，报错即打回。 | 运行 Shell/Python, 依赖安装 |

#### 2. 黑板模式 (The Blackboard)

所有 Agent 共享一个内存中的上下文对象 `MissionContext`。

* **Project Manifest**: 架构师的设计图。
* **Code Repository**: 仅存储文件路径索引（Token 优化），不再存储全文。
* **Runtime Logs**: 运行报错与测试结果。

---

### 💻 安装与配置 (Setup)

#### 1. 环境准备

确保 Python 3.10+ 环境。

```bash
# 克隆项目（假设位于 experiments 目录）
cd experiments

# 安装依赖
pip install langchain langchain-openai duckduckgo-search streamlit

```

#### 2. API Key 配置

在 `config/` 目录下新建 `keys.json`（已通过 `.gitignore` 忽略）：

```json
{
  "deepseek": {
    "api_key": "sk-xxxx",
    "base_url": "https://api.deepseek.com"
  },
  "openrouter": {
    "api_key": "sk-or-xxxx",
    "base_url": "https://openrouter.ai/api/v1"
  }
}

```

---

### 🚀 运行指南 (Usage)

本项目采用 **双进程模式**：一个跑业务，一个跑监控。

#### 步骤 1：启动可视化监控 (Eyes)

在第一个终端窗口中运行：

```bash
# 使用 python 模块模式启动，避免路径问题
python -m streamlit run Debug/dashboard.py

```

*浏览器将自动打开，显示“等待主程序启动...”*

#### 步骤 2：启动蜂群主程序 (Brain)

在第二个终端窗口中运行：

```bash
python main.py

```

#### 步骤 3：下达指令

在主程序终端输入需求，例如：

> “写一个贪吃蛇游戏，要有计分板和暂停功能。”

此时，你可以切回浏览器，观看 Agent 们的 **蛇形交互拓扑图** 和 **实时 Token 消耗**。

---

### 📂 项目结构 (Structure)

```text
experiments/
├── main.py                # [入口] 核心引擎与主循环
├── agent_core.py          # [核心] Agent 类与动态 Prompt 加载
├── blackboard.py          # [数据] 共享黑板 (已瘦身)
├── llm_connection.py      # [网络] LLM 连接与 Token 埋点
├── Debug/                 # [监控] 可视化模块
│   ├── dashboard.py       # Streamlit 前端面板
│   ├── monitor.py         # 状态记录单例
│   └── run_state.json     # 运行时产生的临时状态文件
├── config/
│   ├── agents_config.json # 角色定义与工具绑定
│   └── AgentLanguage.json # 通信协议
├── prompts/               # [人设] 三位一体 Agent 的 Prompt
│   ├── Architect.md
│   ├── Developer.md
│   └── Inspector.md
├── skills/                # [技能] 工具库
│   ├── File_Skills.py     # 包含 write_file 和 replace_file_lines
│   ├── Shell_Skills.py    # 包含防卡死的 run_shell_command
│   └── ...
└── output/                # [产出] 所有生成的代码位于此处

```

---

### ⚠️ v0.2 重要更新说明

1. **关于 `Developer` 的使用**：
* Developer 能够使用 `replace_file_lines` 修改特定行号的代码。这要求模型具备较好的指令遵循能力（推荐 GPT-4o-mini 或 DeepSeek-V3）。


2. **关于 `Inspector` 的防死循环**：
* Shell 命令增加了 `timeout` 和 `stdin=DEVNULL`，防止因交互式 CLI（如 `pip` 询问 y/n）导致的程序挂起。
* Inspector 遵循“事不过三”原则，连续报错 3 次会自动将任务标记为 Failed 并打回给 Developer。



---

**Happy Coding with Swarm! 🐝**