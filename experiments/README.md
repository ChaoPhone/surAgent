
---

# 🐝 Swarm Agent Framework (v0.1: 召唤师与召唤物)

### 🚀 核心摘要 (Executive Summary)

本项目实现了一个基于 **“蜂群架构 (Swarm Architecture)”** 的多智能体协作系统（Multi-Agent System）。不同于传统的单体 Agent 或简单的 Chain 模式，我们构建了一个**分工明确、自主协作**的虚拟开发团队。

**核心角色与机制：**

* **🧙‍♂️ 召唤师 (Summoner)**：**绝对核心与项目经理**。负责拆解用户需求，利用有限状态机（FSM）调度合适的专家 Agent，并把控项目进度。它拥有“上帝视角”，但不亲自写代码。
* **🛠️ 召唤物 (Workers)**：各司其职的专家 Agent。
* **Structure (架构师)**：负责画图纸，定义文件树与 API。
* **Kernel (后端工兵)**：负责写逻辑，实现 Python/Node.js 等后端代码。
* **Surface (前端工兵)**：负责写界面，实现 HTML/CSS/JS。
* **Audit (验收官)**：负责质检，运行代码并反馈 Bug。


* **📋 黑板模式 (Blackboard Pattern)**：所有 Agent 通过一个全局共享的“黑板” (`MissionContext`) 交换信息。架构师画完图纸贴在黑板上，后端工兵看到后直接开工，无需口头转述，极大降低了 Token 消耗和幻觉风险。
* **📂 强制落地 (File Skills)**：所有生成的代码会被强制写入 `output/` 目录，真正实现从“文本对话”到“可运行项目”的交付。

---

### 📖 目录 (Table of Contents)

1. [架构设计哲学](https://www.google.com/search?q=%23-%E6%9E%B6%E6%9E%84%E8%AE%BE%E8%AE%A1%E5%93%B2%E5%AD%A6-philosophy)
2. [核心组件详解](https://www.google.com/search?q=%23-%E6%A0%B8%E5%BF%83%E7%BB%84%E4%BB%B6%E8%AF%A6%E8%A7%A3-components)
3. [工作流演示](https://www.google.com/search?q=%23-%E5%B7%A5%E4%BD%9C%E6%B5%81%E6%BC%94%E7%A4%BA-workflow)
4. [安装与运行](https://www.google.com/search?q=%23-%E5%AE%89%E8%A3%85%E4%B8%8E%E8%BF%90%E8%A1%8C-installation)
5. [项目结构说明](https://www.google.com/search?q=%23-%E9%A1%B9%E7%9B%AE%E7%BB%93%E6%9E%84%E8%AF%B4%E6%98%8E-structure)
6. [常见问题 (FAQ)](https://www.google.com/search?q=%23-%E5%B8%B8%E8%A7%81%E9%97%AE%E9%A2%98-faq)

---

### 🧠 架构设计哲学 (Philosophy)

v0.1 版本名为 **“召唤师与召唤物”**，强调的是 **控制权与执行权的分离**。

* **去中心化的执行，中心化的调度**：
Summoner 是唯一的入口，它维护一个状态机（State Machine）。它不干涉具体代码怎么写，但它严格控制“现在该谁上场”。
* **黑板 > 聊天**：
传统的 Multi-Agent 容易陷入无限对话循环。我们引入了 **MissionContext (黑板)**。
* `Structure` 产出 Manifest（设计图）。
* `Kernel` 产出 Code（代码库）。
* `Audit` 产出 Logs（验收报告）。
* Agent 之间 **少说话，多看板**。


* **工具即技能 (Skills as Tools)**：
Agent 的能力被封装在 `skills/` 目录下。无论是写文件、跑 Shell 还是联网搜索，都是一个个可插拔的 Python 函数。

---

### 🧩 核心组件详解 (Components)

#### 1. The Summoner (控制层)

* **职责**：分析用户 Prompt -> 检查黑板状态 -> 决定派谁干活 -> 验收成果。
* **特权工具**：`dispatch_mission` (移交指挥棒), `mark_mission_complete` (结束任务)。
* **状态机逻辑**：
* 没设计图？ -> 找 Structure。
* 缺后端？ -> 找 Kernel。
* 缺前端？ -> 找 Surface。
* 写完了？ -> 找 Audit。



#### 2. The Workers (执行层)

* **Structure**: 产出文件目录树，规定文件路径必须在 `output/<项目名>/` 下。
* **Kernel**: 纯逻辑实现，严禁写 UI 代码。必须读取黑板上的设计图。
* **Surface**: 纯界面实现，根据后端 API 编写前端逻辑。
* **Audit**: 唯一的“反思”角色。它不生产代码，而是运行代码、检查完整性，决定是 Pass 还是打回重修。

#### 3. The Blackboard (数据层)

* 位于 `blackboard.py`。
* 它是内存中的共享数据库，存储 `project_manifest` (架构)、`code_repository` (代码)、`runtime_logs` (日志)。
* 支持快照 (`get_snapshot`)，方便调试。

#### 4. The Skill System (能力层)

* 位于 `skills/` 目录。
* **File_Skills**: 也就是“物理手”。强制将所有写操作重定向到 `output/` 目录，防止 Agent 污染项目根目录。
* **Shell_Skills / Python_Skills**: 赋予 Agent 执行代码、安装依赖的能力。
* **Web_Skills**: 赋予 Agent 联网解决未知报错的能力。

---

### 🎬 工作流演示 (Workflow)

当用户输入：*"写一个贪吃蛇游戏"*

1. **Summoner** 启动，发现黑板是空的。
* 👉 **Dispatch** -> `Structure`


2. **Structure** 上场，定义项目名为 `snake_game`，设计了 `main.py`, `game.py` 等文件结构。
* 📝 **Write** -> Blackboard (`project_manifest`)


3. **Summoner** 重新接管，发现有设计图但没代码。
* 👉 **Dispatch** -> `Kernel`


4. **Kernel** 上场，读取设计图，开始写 `game.py` 的逻辑。
* 💾 **Write File** -> `output/snake_game/game.py`


5. **Summoner** 再次接管，发现代码写完了，但没验收。
* 👉 **Dispatch** -> `Audit`


6. **Audit** 上场，运行代码，发现没报错。
* ✅ **Update** -> Blackboard (`runtime_logs`: PASSED)


7. **Summoner** 看到 PASSED，宣布任务完成。

---

### 💻 安装与运行 (Installation)

#### 1. 环境准备

确保已安装 Python 3.10+。

```bash
# 1. 克隆项目
git clone <repository_url>
cd surAgent/experiments

# 2. 安装依赖
pip install langchain langchain-openai duckduckgo-search

```

#### 2. 配置 Key

在 `config/` 目录下创建 `keys.json` 文件（**注意：此文件已被 .gitignore，严禁上传**）。

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

#### 3. 运行

```bash
python main.py

```

进入交互模式后，输入你的需求即可。例如：
`> 写一个基于 Flask 的待办事项管理系统，UI要简洁。`

---

### 📂 项目结构说明 (Structure)

```text
surAgent/
├── experiments/
│   ├── main.py              # [入口] 程序启动点，包含主循环
│   ├── agent_core.py        # [核心] Agent 类定义，Prompt 加载
│   ├── blackboard.py        # [核心] 黑板数据结构
│   ├── llm_connection.py    # [底层] LLM 连接器
│   ├── config/              # [配置] 角色定义、Key、协议
│   ├── prompts/             # [人设] 各个 Agent 的 System Prompt
│   ├── skills/              # [技能] 工具函数库 (File, Shell, Web...)
│   └── output/              # [产出] Agent 生成的代码都会在这里

```

---

### ❓ 常见问题 (FAQ)

**Q: 为什么 Agent 有时候会报错 'Worker not found'?**
A: 这是 Agent 的幻觉。v0.1 版本已在 `main.py` 中增加了容错逻辑，当 Agent 呼叫不存在的队友时，系统会拦截并提示它重试。

**Q: 代码生成在哪里？**
A: 都在根目录的 `output/` 文件夹下。`File_Skills.py` 做了强制路径重定向，确保不会覆盖你的系统文件。

**Q: 如何添加新的角色？**

1. 在 `prompts/` 下新建 `NewRole.md`。
2. 在 `config/agents_config.json` 中注册它。
3. 在 `skills/__init__.py` 中为它分配技能 (`ROLE_SKILLS`)。

---

**Happy Coding with Swarm! 🐝**