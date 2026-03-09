# Swarm Agent Framework (surAgent)

> [!note]
> 本文档撰写时的框架版本为 `v0.5` 。

---

## 项目简介

**Swarm Agent Framework (surAgent)** 是一个基于 **“蜂群架构”** 的轻量级多智能体协作开发框架。它通过模拟软件工程中的专业分工，实现了从需求分析到代码落地的全自动化流程。

### 核心架构：

- **召唤师 (Summoner)**：项目经理，负责维护有限状态机 (FSM)，进行任务分发与宏观进度把控。
- **技术主管 (TechLead)**：**\[v0.5.0 新增]** 负责指挥并行 Worker 完成任务，通过“动态温度矩阵”把控质量，并负责最终的代码持久化。

- **铁三角 - 具体工作执行**：
  - **架构师 (Architect)**：负责顶层设计、文件树结构定义与 API 接口契约规划。
  - **开发者 (Developer/Worker)**：负责具体代码实现。在 v0.5.0 中，Developer 可作为被 TechLead 调度的并行 Worker。
  - **质检官 (Inspector)**：负责代码运行、环境安装、测试执行与错误定位。

### 主要特性：

- **降本增效**：集成 **Neural Skimmer** 机制，通过“目标驱动读取”大幅降低读取 Token 消耗。
- **稳健架构**：v0.4.3 重构了底层核心，引入线程安全内存与路径抽象，为并行化扩展打下基石。
- **实时监控**：内置 Streamlit 仪表盘，提供 Mermaid 动态拓扑图与实时 Token 计费监控。
- **强一致性**：共享“黑板”内存模式，配合全栈开发角色，彻底解决接口不一致问题。

---

## 快速开始

### 环境与配置

1. 确保已安装 Python 3.10+ 环境。

> [!important]
> 虽然 Python 3.9 等更低版本的 Python 也**可能**可以运行本框架，但是我们无法为功能正常运作提供任何保证。

2. 键入下面的命令安装依赖：

   ```bash
   pip install langchain langchain-openai duckduckgo-search streamlit tiktoken filelock
   ```

3. 在 `config` 目录下新建 `keys.json` 配置 API Key（推荐 GPT-4o-mini 或 DeepSeek-V3 以获得最佳性价比）。

> [!warning]
> DeepSeek 于2026年春节前进行了热更新，现有版本的命令遵守能力有所降低，考虑谨慎使用此模型。

<a id="how_to_run"></a>

### 运行指南

> [!tip]
> 对于不同的系统，可能使用不同的命令头。
>
> 例如对于 Windows 用户，您的命令头有可能是 `py` 而非 `python`。
>
> 对于 Linux 用户，您的命令头有可能是 `python3` 。
>
> 如果您在稍后遇到了问题，请考虑更换其他命令头。

本项目采用 **双进程模式**，请在**两个终端**分别运行：

1. **启动监控**：

   ```bash
   python -m streamlit run Debug/dashboard.py
   ```

   浏览器将自动打开，显示 Swarm Dashboard。

2. **启动主程序**：

   ```bash
   python main.py
   ```

3. **下达指令**：

   等待主程序初始化完成，即可在主程序终端输入需求。

   例如：“写一个贪吃蛇游戏，要有计分板和暂停功能。”

   > [!tip]
   > “好的提示词是成功的一半”，建议提供尽可能详细和专业的要求说明。
   >
   > 例如 “使用面向过程的设计模式，编写一个解析下面 JSON 文件的 Python 脚本，下面是对文件中内容的详细说明：......” 要远好于 “编写一个解析 JSON 文件的程序” 。

4. **收获产出**：

   在项目根目录下的 `output` 文件夹获取输出的项目文件。

   > [!tip]
   > AI Coding 不是 Vibe Coding！
   >
   > 在将产出的代码用于实际运用（尤其是生产环境）前请务必另行检测代码可用性和健壮性，或者至少运行 Agent 为您提供的单元测试。

---

## **项目结构**

```Plaintext
experiments/
├── Core/                  # [核心] 引擎内核
│   ├── agent.py           # 动态 Agent 类定义
│   ├── engine.py          # 核心执行循环与调度逻辑
│   ├── memory.py          # [线程安全] 共享记忆与黑板
│   ├── network.py         # LLM 连接层
│   └── validator.py       # 语法校验中间件
├── skills/                # [技能] 工具库 (按领域拆分)
│   ├── File_Skills.py     # 文件读写与路径抽象
│   ├── Python_Skills.py   # 代码静态分析与执行
│   └── ...
├── Debug/                 # [监控] 可视化模块 (Streamlit)
├── config/                # [配置] 角色 Prompt 与 API Key
├── prompts/               # [人设] Agent System Prompts
├── output/                # [产出] 代码生成目录 (默认工作区)
└── main.py                # [入口] 启动脚本
```

---

## 版本演进

### v0.5.0: The Parallelist / 并行者 (Current)

> _"为了迎接大规模并行协作时代，我们重构了底层通信与调度逻辑。"_

- **🏗️ 内核重构**：引入 `EventBus`，支持全量事件订阅（Token 统计、角色切换、并行状态）。
- **🚀 并行调度**：新增 `TechLead` 角色与 `batch_coding_tasks` 技能，支持同时唤起多个 Worker 执行任务。
- **🌡️ 动态温度矩阵**：TechLead 可根据任务类型（代码 vs 创意）动态调整采样温度。
- **🧹 深度自愈**：在 `engine.py` 中增加历史记录自动清洗逻辑，修复“幽灵工具调用”产生的 API 异常。
- **🎨 仪表盘升级**：支持 Mermaid 拓扑自动着色、Token 资源消耗堆叠图及黑客风格实时终端。

### v0.4.3: The Foundation / 基石

> _"为了迎接即将到来的多 Agent 并行时代，我们对底层架构进行了彻底的加固与重构。"_

- **🏗️ 模块化重构**：废弃了扁平的文件结构，将核心逻辑封装进 `Core/` 包，技能库独立为 `skills/` 包。大幅提升了代码的可维护性与扩展性。
- **🔌 纯函数化改造**：`execute_agent_turn` 被改造为无副作用的纯函数，支持通过参数注入 `Hot-Patch`，不再修改 Agent 对象属性。

### v0.4.2: The Interceptor / 拦截者

- **🛡️ 三道防线**：构建了 API 熔断、无效工具拦截、语法强制自检三道防线。
- **🧹 JSON 逃逸修复**：彻底解决 DeepSeek 等模型在输出 JSON 时夹带注释或格式错误导致的系统崩溃问题。
- **⚡️ 强制 AST 自检**：`write_file` 内置 Python 语法检查，写入烂代码会直接报错并拒收。

### v0.4.1: The Pruner / 剪枝者

- **📉 语义裁剪**：集成 **Neural Skimmer**。读取大文件时强制要求提供 focus_question，智能裁剪无关代码行，Token 节省率高达 76%。

### v0.4: Token Optimization

- 引入 **SWE-Pruner** 论文理论，探索基于语义的上下文裁剪方案。
- 在 File_Skills.py 中增加基础的拦截逻辑，测试不同模型的指令遵循能力。

### v0.2: The Trinity / 三位一体

- **🧙‍♂️ 角色重组**：合并原来的前后端工兵为 **全栈开发 (Developer)**，确立 Design -> Build -> Test 的闭环。
- **🛠️ 精准修改**：引入 replace_file_lines，支持按行修改代码，不再全量重写。
- **👀 可视化**：首发基于 Streamlit 的监控面板，支持动态交互拓扑。

### v0.1: Summoner / 召唤师

- 确立基本的 Summoner 调度架构。
- 实现基础的 FSM 状态机与工具调用能力。

## 🤖 AI 维护指南

**致 AI 协作者**：当你被要求**更新**此 README 时，请严格遵守以下规范：

1. **结构保持**：
   - **简介、快速开始、项目结构**保持稳定，仅在项目核心逻辑、文件树、依赖或运行方式发生**破坏性变更**时才进行修改。

2. **更新流程**：
   - 请将新版本的特性摘要添加到 **版本演进** 的顶部。
   - 摘要格式应包含：**版本号**、**代号**、**一句话核心价值**（Blockquote格式）、**关键特性列表**。
     > 例如：
     >
     > v0.4.3: The Foundation / 基石
     >
     > > _"为了迎接即将到来的多 Agent 并行时代，我们对底层架构进行了彻底的加固与重构。"_
     >
     > v0.4.3: 版本号
     >
     > The Foundation / 基石: 代号（允许中英文混合，本条指令在编写代号时优先级高于编辑规范中的指令）
     >
     > _"为了迎接即将到来的多 Agent 并行时代，我们对底层架构进行了彻底的加固与重构。"_: 使用引用块、斜体和引号包含一句话简述。

3. **编辑规范**：
   - **禁止**重写整个文档。
   - 保留历史版本的记录，除非用户**明确要求**删除。
   - 保持语言简洁、专业。
   - 适当使用 Emoji 增强可读性，但是避免在 H1 标题和 H2 标题使用 Emoji。
   - 语法应符合 Markdown Lint 工具的规范（例如对于标题行不需要使用加粗）。
   - 为不同语言分别编写 README ，使用锚点和超链接来保证 README 之间能够相互跳转。禁止在同一份 README 中进行 i18n 。
     > 示例，编写标题时：
     >
     > 正确：
     >
     > - `## 版本演进` （在 README.md 中）
     > - `## Changelog` (In README_en.md)
     >
     > 错误：`## 版本演进 (Changelog)` （在 README.md 中）
   - 使用 GitHub Flavoured Markdown (GFM) 语法规范。允许使用所有提供的扩展规范。
