# **🐝 surAgent 介绍【v0.4.2】**

### **📖 项目简介 (Introduction)**

**Swarm Agent Framework** 是一个基于 **“蜂群架构”** 的轻量级多智能体协作开发框架。它通过模拟软件工程中的专业分工，实现了从需求分析到代码落地的全自动化流程。

**核心架构：**

* **🧙‍♂️ 召唤师 (Summoner)**：项目经理，负责维护有限状态机 (FSM)，进行任务分发与宏观进度把控。  
* **The Trinity (铁三角)**：  
  * **📐 架构师 (Architect)**：负责顶层设计、文件树结构定义与 API 接口契约规划。  
  * **👨‍💻 全栈开发 (Developer)**：负责从后端逻辑到前端 UI 的所有代码实现与精准修改。  
  * **🕵️‍♂️ 质检官 (Inspector)**：负责代码运行、依赖安装、测试执行与错误定位（拥有一票否决权）。

**主要特性：**

* **📉 降本增效**：集成 **SWE-Pruner** 语义裁剪框架，通过“目标驱动读取”大幅降低 Token 消耗（\~76%）。  
* **📊 实时监控**：内置 Streamlit 仪表盘，提供 Mermaid 动态拓扑图与实时 Token 计费监控。  
* **🛠️ 强一致性**：共享“黑板”内存模式，配合全栈开发角色，彻底解决接口不一致问题。

### **💻 快速开始 (Quick Start)**

#### **1\. 环境与配置**

确保 Python 3.10+ 环境。

\# 克隆项目并安装依赖  
cd experiments  
pip install langchain langchain-openai duckduckgo-search streamlit tiktoken

在 config/ 目录下新建 keys.json 配置 API Key（推荐 GPT-4o-mini 用于 Neural Skimmer 以获得最佳性价比）。

#### **2\. 运行指南 (Usage)**

本项目采用 **双进程模式**，请在两个终端分别运行：

1. **启动监控 (Eyes)**：  
   python -m streamlit run Debug/dashboard.py

   *浏览器将自动打开，显示 Swarm Dashboard。*  
2. **启动主程序 (Brain)**：  
   python main.py

3. **下达指令**：  
   在主程序终端输入需求，例如：“写一个贪吃蛇游戏，要有计分板和暂停功能。”  
   “帮我优化一下 blackboard.py 的存储逻辑。”

### **📂 项目结构 (Structure)**

experiments/   
├── main.py                 	# \[入口\] 核心引擎与主循环  
├── agent\_core.py           \# \[核心\] Agent 类与动态 Prompt 加载  
├── blackboard.py           \# \[数据\] 共享黑板 (Context)  
├── llm\_connection.py      \# \[网络\] LLM 连接与 Token 埋点  
├── validator.py 				#语法校验中间件 (AST/JSON检查)
├── Debug/                 \# \[监控\] 可视化模块 (Streamlit)  
├── config/                \# \[配置\] 角色定义与通信协议  
├── prompts/               \# \[人设\] Agent Prompt (含 CoT 指令)  
├── skills/                \# \[技能\] 工具库  
│   ├── File\_Skills.py     \# \[重点\] 集成 SWE-Pruner 裁剪逻辑  
│   └── Shell\_Skills.py    \# 防卡死 Shell 执行  
└── output/                \# \[产出\] 代码生成目录

### **📅 版本演进 (Changelog)**

#### **v0.4.2: The Interceptor / 拦截者 (Current)**

_构建了三道防线，彻底解决 "JSON 逃逸" 与 "语法错误" 导致的系统崩溃。_

* **🛡️ 中间件拦截 (Middleware Guardrails)**：在 `main.py` 层面植入 `validator.py`。Agent 输出的代码块（Python/JSON/HTML）若存在语法错误，会被强制拦截并打回重写，Summoner 对此无感知。

* **🧹 上下文清洗 (Context Sanitization)**：自动折叠历史记录中 `write_file` 的巨型参数，彻底根除因 HTML/JS 特殊字符未转义导致的 `JSONDecodeError` 及 400 死循环。

* **⚡️ 强制自检 (Tool-Level QA)**：`write_file` 工具内置 AST 语法检查。写入烂代码会返回警告而非成功，迫使 Agent 自主进入修复循环。

* **🔧 DeepSeek 兼容性修复**：修复了 DeepSeek V3 对工具调用历史严格校验导致的 400 错误（Shadow Tool Injection）。

#### **v0.4.1: The Pruner / 剪枝者 **

*针对 Coding Agent 的上下文 Token 消耗痛点进行的革命性升级。*

* **📉 极致降本**：集成 **Neural Skimmer** 机制。当 Agent 读取文件时，系统会根据 focus\_question 对代码进行行级语义过滤。  
* **🧠 目标驱动**：强制 Agent 在读取代码时必须明确“我在找什么”。若未提供关注点且试图读取大文件（\>2000字符），系统将触发 **强制拦截**。  
* **📊 监控升级**：Dashboard 新增 Token 节省率与语义裁剪触发统计。

#### **v0.4: Token Optimization**

* 引入 **SWE-Pruner** 论文理论，探索基于语义的上下文裁剪方案。  
* 在 File\_Skills.py 中增加基础的拦截逻辑，测试不同模型的指令遵循能力。

#### **v0.2: The Trinity / 三位一体**

* **🧙‍♂️ 角色重组**：合并原来的前后端工兵为 **全栈开发 (Developer)**，确立 Design \-\> Build \-\> Test 的闭环。  
* **🛠️ 精准修改**：引入 replace\_file\_lines，支持按行修改代码，不再全量重写。  
* **👀 可视化**：首发基于 Streamlit 的监控面板，支持动态交互拓扑。

#### **v0.1: Summoner / 召唤师**

* 确立基本的 Summoner 调度架构。  
* 实现基础的 FSM 状态机与工具调用能力。

### **🤖 AI 维护指南 (AI Maintenance Guide)**

**致 AI 协作者**：当你被要求更新此 README 时，请严格遵守以下规范：

1. **结构保持**：  
   * **前半部分**（简介、快速开始、项目结构）保持稳定，仅在项目核心逻辑或运行方式发生**破坏性变更**时才进行修改。  
   * **后半部分**（版本演进）是更新的重点区域。  
2. **更新流程**：  
   * 请将新版本的特性摘要添加到 **📅 版本演进 (Changelog)** 的顶部。  
   * 摘要格式应包含：**版本号**、**代号**、**一句话核心价值**（Blockquote格式）、**关键特性列表**。  
3. **最小化修改**：  
   * 不要重写整个文档。  
   * 保留历史版本的记录，除非用户明确要求删除。  
   * 保持语言简洁、专业，适当使用 Emoji 增强可读性。