import os
import json
import sys
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from agent_core import DynamicAgent
from blackboard import MissionContext

# ================= 全局状态 =================
blackboard = MissionContext()
agent_registry = {}


# ================= 工具定义 =================

# 1. 黑板工具
def update_blackboard(key: str, content: str):
    """更新项目黑板上的共享信息。keys: project_manifest, api_schema, runtime_logs, code_repository"""
    return blackboard.write(key, content)


def read_blackboard(key: str):
    """读取黑板信息"""
    return blackboard.read(key)


# 2. 召唤师专用工具 (Handoff)
def dispatch_mission(target_agent: str, task_description: str, prompt_patch: str = ""):
    """[Summoner Only] 将任务移交给专家 Agent。可附带 prompt_patch (热更新指令) 来微调专家行为。"""
    if target_agent not in agent_registry:
        return f"Error: Agent {target_agent} not found."


    # 应用热更新
    worker = agent_registry[target_agent]
    worker.apply_patch(prompt_patch)

    # 返回 Agent 对象，触发 Main Loop 切换
    return worker


# 3. Worker 互调工具 (Subroutine) - 核心难点
# 我们需要一个全局引擎引用来执行递归调用，为了简化，我们在这里使用闭包或全局引用
def call_peer(target_agent: str, specific_query: str):
    """[Worker Only] 打电话给另一个 Agent 寻求协助。这是同步调用，你会等待对方返回结果。"""
    if target_agent not in agent_registry:
        return f"Error: Peer {target_agent} not found."

    print(f"\n   📞 [Call Peer] 正在呼叫 {target_agent}...")

    # 这里通过 Engine 的类方法来执行子程序
    # 为了代码解耦，我们假设 Engine 是单例或通过外部调用
    # 在这个简单实现中，我们直接调用 run_subroutine_loop
    return run_subroutine_loop(agent_registry[target_agent], specific_query, current_depth=1)  # 深度起始为1

# 4. 全自动结束信号
def mark_mission_complete(final_report: str):
    """[Summoner Only] 当所有代码都编写完成，且项目已具备交付标准时，调用此工具结束自动化流程。"""
    return f"MISSION_COMPLETE_SIGNAL: {final_report}"

# ================= 引擎逻辑 =================

def load_agents():
    path = os.path.join(os.path.dirname(__file__), "config", "agents_config.json")
    with open(path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    for cfg in config:
        agent = DynamicAgent(cfg['name'], cfg['model'], cfg['provider'], cfg['prompt_file'])
        agent_registry[agent.name] = agent
    print(f"✅ 已加载 {len(agent_registry)} 个 Agent")


# --- 递归子程序循环 (Subroutine Loop) ---
def run_subroutine_loop(agent, query, current_depth):
    # 盲区五：最小信息原则，只传 Query，不传上文 History
    messages = [HumanMessage(content=query)]

    MAX_DEPTH = 3
    MAX_TURNS = 7

    if current_depth > MAX_DEPTH:
        return "System Error: Max call depth exceeded. Please return control to Summoner."

    print(f"   Now Running Subroutine: {agent.name} (Depth: {current_depth})")

    tools = [update_blackboard, read_blackboard, call_peer]  # Worker 只能调 Peer，不能 Dispatch

    for _ in range(MAX_TURNS):
        # 动态合成 Prompt
        sys_prompt = agent.get_full_instructions()
        sys_prompt += f"\nNote: You are in a Subroutine Call (Depth {current_depth}). Answer the user query directly."

        response = agent.client.get_completion(
            model=agent.model,
            messages=[SystemMessage(content=sys_prompt)] + messages,
            tools=tools
        )

        messages.append(response)

        if response.tool_calls:
            for tool_call in response.tool_calls:
                fn_name = tool_call["name"]
                args = tool_call["args"]
                print(f"      ⚙️ {agent.name} (Depth {current_depth}) -> {fn_name}")

                result = "Error"
                if fn_name == "update_blackboard":
                    result = update_blackboard(**args)
                elif fn_name == "read_blackboard":
                    result = read_blackboard(**args)
                elif fn_name == "call_peer":
                    # 递归调用，深度 +1
                    result = run_subroutine_loop(agent_registry[args['target_agent']], args['specific_query'],
                                                 current_depth + 1)

                messages.append(ToolMessage(content=str(result), tool_call_id=tool_call["id"]))
        else:
            # 没有工具调用，说明输出了最终回答
            print(f"   ✅ {agent.name} Subroutine Finished.\n")
            return response.content

    return "Error: Peer request timed out (Max turns reached)."


# --- 全自动主循环 (Auto-Pilot Loop) ---
def run_main_loop(user_goal):
    current_agent = agent_registry["Summoner"]

    # 初始输入是用户的需求
    # 注意：在全自动模式下，Summoner 需要不仅看 User Input，还要看 Blackboard
    messages = [HumanMessage(content=f"终极任务目标：{user_goal}\n请检查黑板状态，开始自动推进，直到代码全部写完。")]

    print(f"\n🚀 [AUTO-MODE] 任务启动: {user_goal}\n")

    MAX_AUTO_TURNS = 66  # 防止死循环，最多自动跑 15 轮
    turn_count = 0

    while turn_count < MAX_AUTO_TURNS:
        turn_count += 1
        print(f"🔄 [Turn {turn_count}/{MAX_AUTO_TURNS}] 主角: {current_agent.name}")

        # 动态工具列表
        if current_agent.name == "Summoner":
            # Summoner 多了一个“任务完成”按钮
            tools = [dispatch_mission, read_blackboard, mark_mission_complete]
        else:
            tools = [update_blackboard, read_blackboard, call_peer]

        # 调用 LLM
        response = current_agent.client.get_completion(
            model=current_agent.model,
            messages=[SystemMessage(content=current_agent.get_full_instructions())] + messages,
            tools=tools
        )

        messages.append(response)

        # 核心逻辑：如果没有工具调用，强制让 Summoner 思考下一步
        if not response.tool_calls:
            print(f"🤖 {current_agent.name} 思考: {response.content}")
            if current_agent.name != "Summoner":
                # 工兵干完活了，自动切回 Summoner，让它来验收
                print("   ↩️ 工兵任务结束，控制权交还 Summoner...")
                current_agent = agent_registry["Summoner"]
                # 给 Summoner 一个信号，让它继续
                messages.append(HumanMessage(content="上一个工兵已完成任务。请检查黑板，决定下一步行动。"))
            continue

        # 处理工具调用
        for tool_call in response.tool_calls:
            fn_name = tool_call["name"]
            args = tool_call["args"]
            print(f"⚙️  {current_agent.name} -> {fn_name}")

            if fn_name == "mark_mission_complete":
                print("\n🎉🎉🎉 任务全自动完成！ 🎉🎉🎉")
                print("================ 最终报告 ================")
                print(args.get('final_report'))
                print("==========================================")
                return  # 彻底退出循环

            elif fn_name == "dispatch_mission":
                new_agent = dispatch_mission(**args)
                if isinstance(new_agent, DynamicAgent):
                    print(f"👉 指挥棒交给 -> {new_agent.name}")
                    messages.append(
                        ToolMessage(content=f"Transferred to {new_agent.name}", tool_call_id=tool_call["id"]))
                    current_agent = new_agent
                else:
                    messages.append(ToolMessage(content=str(new_agent), tool_call_id=tool_call["id"]))

            elif fn_name in ["call_peer", "update_blackboard", "read_blackboard"]:
                # ... (保持原有的处理逻辑) ...
                if fn_name == "call_peer":
                    res = run_subroutine_loop(agent_registry[args['target_agent']], args['specific_query'], 1)
                else:
                    res = globals()[fn_name](**args)

                messages.append(ToolMessage(content=str(res), tool_call_id=tool_call["id"]))

    print("⚠️ 警告：达到最大自动运行轮数，强制停止。")

# ================= 6. 程序入口 (Interactive Mode) =================

if __name__ == "__main__":
    # 1. 初始化所有 Agent
    print("🔄 初始化蜂群系统...")
    load_agents()
    print("✅ 系统就绪。黑板 (Blackboard) 已重置。")
    print("--------------------------------------------------")
    print("💡 提示：输入 'exit', 'quit' 或 'q' 退出程序。")
    print("--------------------------------------------------")

    # 2. 进入交互循环
    while True:
        try:
            # 获取用户输入
            user_input = input("\n🙋 召唤师指令 (User): ").strip()

            # 处理退出
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\n👋 蜂群已解散。再见！")
                break

            # 处理空输入
            if not user_input:
                continue

            # 3. 运行主循环 (传入用户指令)
            # 注意：目前的 run_main_loop 是单次任务制的。
            # 如果你想让 Summoner 记住上一轮对话，需要把 messages 提到 while 外面，
            # 但蜂群架构通常建议每次 Task 独立，状态通过 Blackboard 传递。
            run_main_loop(user_input)

        except KeyboardInterrupt:
            # 捕获 Ctrl+C
            print("\n\n👋 强制终止。再见！")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ 发生未知错误: {e}")
            # 不退出循环，允许用户重试
            continue