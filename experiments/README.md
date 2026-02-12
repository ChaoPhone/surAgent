
# **🐝 surAgent 介绍【v0.4.3】**

### **📖 项目简介 (Introduction)**

**Swarm Agent Framework** 是一个基于 **“蜂群架构”** 的轻量级多智能体协作开发框架。它通过模拟软件工程中的专业分工，实现了从需求分析到代码落地的全自动化流程。

**核心架构：**

* **🧙‍♂️ 召唤师 (Summoner)**：项目经理，负责维护有限状态机 (FSM)，进行任务分发与宏观进度把控。  
* **The Trinity (铁三角)**：  
  * **📐 架构师 (Architect)**：负责顶层设计、文件树结构定义与 API 接口契约规划。  
  * **👨‍💻 全栈开发 (Developer)**：负责从后端逻辑到前端 UI 的所有代码实现与精准修改。  
  * **🕵️‍♂️ 质检官 (Inspector)**：负责代码运行、依赖安装、测试执行与错误定位（拥有一票否决权）。

**主要特性：**

* **📉 降本增效**：集成 **Neural Skimmer** 机制，通过“目标驱动读取”大幅降低 Token 消耗。  
* **🛡️ 稳健架构**：v0.4.3 重构了底层核心，引入线程安全内存与路径抽象，为并行化扩展打下基石。
* **📊 实时监控**：内置 Streamlit 仪表盘，提供 Mermaid 动态拓扑图与实时 Token 计费监控。  
* **🛠️ 强一致性**：共享“黑板”内存模式，配合全栈开发角色，彻底解决接口不一致问题。

### **💻 快速开始 (Quick Start)**

#### **1\. 环境与配置**

确保 Python 3.10+ 环境。

```bash
# 安装依赖
pip install langchain langchain-openai duckduckgo-search streamlit tiktoken filelock
````

在 `config/` 目录下新建 `keys.json` 配置 API Key（推荐 GPT-4o-mini 或 DeepSeek-V3 以获得最佳性价比）。

#### **2. 运行指南 (Usage)**

本项目采用 **双进程模式**，请在两个终端分别运行：

1. **启动监控 (Eyes)**：

   Bash

   ```
   python -m streamlit run Debug/dashboard.py
   ```

   _浏览器将自动打开，显示 Swarm Dashboard。_

2. **启动主程序 (Brain)**：

   Bash

   ```
   python main.py
   ```

3. **下达指令**：

   在主程序终端输入需求，例如：“写一个贪吃蛇游戏，要有计分板和暂停功能。”

### **📂 项目结构 (Structure)**

Plaintext

```
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

### **📅 版本演进 (Changelog)**

#### **v0.4.3: The Foundation / 基石 (Current)**

> _"为了迎接即将到来的多 Agent 并行时代，我们对底层架构进行了彻底的加固与重构。"_

* **🏗️ 模块化重构 (Modular Core)**：废弃了扁平的文件结构，将核心逻辑封装进 `Core/` 包，技能库独立为 `skills/` 包。大幅提升了代码的可维护性与扩展性。

* **🔌 纯函数化改造**：`execute_agent_turn` 被改造为无副作用的纯函数，支持通过参数注入 `Hot-Patch`，不再修改 Agent 对象属性。

#### **v0.4.2: The Interceptor / 拦截者**

* **🛡️ 三道防线**：构建了 API 熔断、无效工具拦截、语法强制自检三道防线。

* **🧹 JSON 逃逸修复**：彻底解决 DeepSeek 等模型在输出 JSON 时夹带注释或格式错误导致的系统崩溃问题。

* **⚡️ 强制 AST 自检**：`write_file` 内置 Python 语法检查，写入烂代码会直接报错并拒收。

#### **v0.4.1: The Pruner / 剪枝者**

* **📉 语义裁剪**：集成 **Neural Skimmer**。读取大文件时强制要求提供 focus\_question，智能裁剪无关代码行，Token 节省率高达 76%。

#### **v0.4: Token Optimization**

* 引入 **SWE-Pruner** 论文理论，探索基于语义的上下文裁剪方案。

* 在 File\_Skills.py 中增加基础的拦截逻辑，测试不同模型的指令遵循能力。

#### **v0.2: The Trinity / 三位一体**

* **🧙‍♂️ 角色重组**：合并原来的前后端工兵为 **全栈开发 (Developer)**，确立 Design -> Build -> Test 的闭环。

* **🛠️ 精准修改**：引入 replace\_file\_lines，支持按行修改代码，不再全量重写。

* **👀 可视化**：首发基于 Streamlit 的监控面板，支持动态交互拓扑。

#### **v0.1: Summoner / 召唤师**

* 确立基本的 Summoner 调度架构。

* 实现基础的 FSM 状态机与工具调用能力。

### **🤖 AI 维护指南 (AI Maintenance Guide)**

**致 AI 协作者**：当你被要求更新此 README 时，请严格遵守以下规范：

1. **结构保持**：

   * **前半部分**（简介、快速开始、项目结构）保持稳定，仅在项目核心逻辑或运行方式发生**破坏性变更**时才进行修改。

2. **更新流程**：

   * 请将新版本的特性摘要添加到 **📅 版本演进 (Changelog)** 的顶部。

   * 摘要格式应包含：**版本号**、**代号**、**一句话核心价值**（Blockquote格式）、**关键特性列表**。

3. **最小化修改**：

   * 不要重写整个文档。

   * 保留历史版本的记录，除非用户明确要求删除。

   * 保持语言简洁、专业，适当使用 Emoji 增强可读性。
