import os
import json
import sys
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from agent_core import DynamicAgent
from blackboard import MissionContext
from skills import SKILL_REGISTRY, ROLE_SKILLS # <--- 导入新写的技能库


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

# main.py 中替换这个函数

def load_agents():
    # 1. 【修复红线】真实读取配置文件
    path = os.path.join(os.path.dirname(__file__), "config", "agents_config.json")

    if not os.path.exists(path):
        print(f"❌ 错误：找不到配置文件 {path}")
        return

    try:
        with open(path, 'r', encoding='utf-8') as f:
            config = json.load(f)  # <--- 这里定义了 config 变量
    except Exception as e:
        print(f"❌ 配置文件读取失败: {e}")
        return

    print(f"🔍 发现配置文件，包含 {len(config)} 个角色定义。")

    # 2. 遍历配置
    for cfg in config:
        # A. 基础工具 (所有 Agent 都有的)
        base_tools = [update_blackboard, read_blackboard, call_peer]

        # B. 加载 JSON 配置的额外工具
        json_tools = []
        if "tools" in cfg:
            for t_name in cfg["tools"]:
                # 优先从 skills 库里找
                if t_name in SKILL_REGISTRY:
                    json_tools.append(SKILL_REGISTRY[t_name])
                # 也可以兼容 main.py 里定义的本地工具 (如 dispatch_mission)
                elif t_name in globals():
                    json_tools.append(globals()[t_name])
                else:
                    # 如果工具既不在 skills 也不在 main.py，说明配置写错了
                    print(f"⚠️ 警告: Agent [{cfg['name']}] 配置了未知工具 '{t_name}'")

        # C. 加载角色专属工具 (从 ROLE_SKILLS 查找)
        role_tools = ROLE_SKILLS.get(cfg['name'], [])

        # D. 合并所有工具 (去重)
        final_tools = list(set(base_tools + json_tools + role_tools))

        # 3. 实例化 Agent
        new_agent = DynamicAgent(
            name=cfg['name'],
            model=cfg['model'],
            provider=cfg['provider'],
            base_prompt_file=cfg['prompt_file']
        )

        # 注入工具
        new_agent.client.tools = final_tools

        # 注册到全局字典
        agent_registry[new_agent.name] = new_agent
        print(f"   ✅ 加载角色: {new_agent.name} (工具数: {len(final_tools)})")

    print(f"✅ 初始化完成，共加载 {len(agent_registry)} 个 Agent")

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

        # 处理 String 类型的错误返回
        if isinstance(response, str):
            print(f"      ❌ Subroutine LLM Error: {response}")
            return response

        messages.append(response)

        if response.tool_calls:
            for tool_call in response.tool_calls:
                fn_name = tool_call["name"]
                args = tool_call["args"]
                
                # 🛡️ 参数清洗：移除 Key 末尾的冒号
                args = {k.rstrip(':'): v for k, v in args.items()}
                
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
    # 1. 确保 Summoner 存在
    if "Summoner" not in agent_registry:
        print("❌ 错误：Agent Registry 中找不到 Summoner！请检查 load_agents 是否成功。")
        return

    current_agent = agent_registry["Summoner"]

    # 初始输入是用户的需求
    messages = [HumanMessage(content=f"终极任务目标：{user_goal}\n请检查黑板状态，开始自动推进，直到代码全部写完。")]

    print(f"\n🚀 [AUTO-MODE] 任务启动: {user_goal}\n")

    MAX_AUTO_TURNS = 66  # 防止死循环
    turn_count = 0

    while turn_count < MAX_AUTO_TURNS:
        turn_count += 1
        print(f"🔄 [Turn {turn_count}/{MAX_AUTO_TURNS}] 主角: {current_agent.name}")

        # 动态工具列表配置
        if current_agent.name == "Summoner":
            # Summoner 拥有调度和结束权限
            # 注意：dispatch_mission 和 mark_mission_complete 必须在 main.py 定义或导入
            tools = [dispatch_mission, read_blackboard, mark_mission_complete]
        else:
            # 工兵拥有基础工具 + 互调权限 + 自身携带的特殊 Skills
            # 注意：current_agent.client.tools 包含了 load_agents 时加载的所有工具
            # 这里我们取并集，确保 main.py 定义的核心工具也在其中
            # 但为了简化，通常 current_agent.client.tools 已经包含了所有需要的
            # 这里的 tools 列表是传给 LLM 告诉它"你可以用什么"
            tools = current_agent.client.tools

            # 调用 LLM
        response = current_agent.client.get_completion(
            model=current_agent.model,
            messages=[SystemMessage(content=current_agent.get_full_instructions())] + messages,
            tools=tools
        )

        # 222. 处理 String 类型的错误返回（针对 get_completion 返回 Error String 的情况）
        if isinstance(response, str):
             print(f"❌ LLM 调用失败: {response}")
             return

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
            
            # 🛡️ 参数清洗：移除 Key 末尾的冒号 (针对 LLM 幻觉的容错处理)
            args = {k.rstrip(':'): v for k, v in args.items()}
            
            print(f"⚙️  {current_agent.name} -> {fn_name}")

            # --- 1. 处理任务完成 ---
            if fn_name == "mark_mission_complete":
                print("\n🎉🎉🎉 任务全自动完成！ 🎉🎉🎉")
                print("================ 最终报告 ================")
                print(args.get('final_report'))
                # 这里会触发 save_code_to_disk (如果在 mark_mission_complete 函数里写了的话)
                save_res = mark_mission_complete(**args)
                print(save_res)
                print("==========================================")
                return  # 彻底退出循环

            # --- 2. 处理任务分发 (Summoner) ---
            elif fn_name == "dispatch_mission":
                # 这里的 dispatch_mission 是 main.py 里的函数
                new_agent = dispatch_mission(**args)
                if isinstance(new_agent, DynamicAgent):
                    print(f"👉 指挥棒交给 -> {new_agent.name}")
                    messages.append(
                        ToolMessage(content=f"Transferred to {new_agent.name}", tool_call_id=tool_call["id"]))
                    current_agent = new_agent
                else:
                    # 如果 dispatch 返回字符串错误
                    messages.append(ToolMessage(content=str(new_agent), tool_call_id=tool_call["id"]))


            # --- 3. 处理 P2P 互调 (增加容错) ---
            elif fn_name == "call_peer":
                target_name = args.get('target_agent')
                # ✅ 安全检查：防止 AI 叫错名字 (比如叫 'Worker')
                if target_name in agent_registry:
                    res = run_subroutine_loop(agent_registry[target_name], args['specific_query'], 1)
                else:
                    # 友好的错误提示，让 AI 重试
                    available_agents = list(agent_registry.keys())
                    res = f"System Error: Agent '{target_name}' not found. Available agents: {available_agents}"

                messages.append(ToolMessage(content=str(res), tool_call_id=tool_call["id"]))

            # --- 4. 处理其他通用工具 (黑板 + Skills) ---
            else:
                # 查找顺序：先找 globals() (main.py定义的)，再找 SKILL_REGISTRY (技能库)
                if fn_name in globals():
                    res = globals()[fn_name](**args)
                elif fn_name in SKILL_REGISTRY:
                    res = SKILL_REGISTRY[fn_name](**args)
                else:
                    res = f"System Error: Tool '{fn_name}' execution failed. Function not found in registry."

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
            if user_input.lower() in ['exit', 'quit', 'q', '结束', '退出']:
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