import os
import json
import sys
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from agent_core import DynamicAgent
from blackboard import project_context as blackboard
from skills import SKILL_REGISTRY
import time
from validator import check_code_blocks  # 确保 validator.py 在同级目录

# 【新增】导入监控
try:
    from Debug.monitor import monitor
except ImportError:
    monitor = None

# ================= 全局状态 =================

agent_registry = {}


# ================= 工具定义 =================

def update_blackboard(key: str, content: str):
    return blackboard.write(key, content)


def read_blackboard(key: str):
    return blackboard.read(key)


def dispatch_mission(target_agent: str, task_description: str, prompt_patch: str = ""):
    if target_agent not in agent_registry:
        return f"Error: Agent {target_agent} not found."
    worker = agent_registry[target_agent]
    worker.apply_patch(prompt_patch)
    return worker


def call_peer(target_agent: str, specific_query: str):
    if target_agent not in agent_registry:
        return f"Error: Peer {target_agent} not found."
    print(f"\n   📞 [Call Peer] 正在呼叫 {target_agent}...")
    return run_subroutine_loop(agent_registry[target_agent], specific_query, current_depth=1)


def mark_mission_complete(final_report: str):
    return f"MISSION_COMPLETE_SIGNAL: {final_report}"


# ================= 引擎逻辑 =================

def load_agents():
    path = os.path.join(os.path.dirname(__file__), "config", "agents_config.json")
    if not os.path.exists(path):
        print(f"❌ 错误：找不到配置文件 {path}")
        return
    try:
        with open(path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ 配置文件读取失败: {e}")
        return

    print(f"🔍 发现配置文件，包含 {len(config)} 个角色定义。")

    for cfg in config:
        base_tools = [update_blackboard, read_blackboard, call_peer]
        json_tools = []
        if "tools" in cfg:
            for t_name in cfg["tools"]:
                if t_name in SKILL_REGISTRY:
                    json_tools.append(SKILL_REGISTRY[t_name])
                elif t_name in globals():
                    json_tools.append(globals()[t_name])
                else:
                    print(f"⚠️ 警告: Agent [{cfg['name']}] 配置了未知工具 '{t_name}'")
        final_tools = list(set(base_tools + json_tools))

        new_agent = DynamicAgent(
            name=cfg['name'],
            model=cfg['model'],
            provider=cfg['provider'],
            base_prompt_file=cfg['prompt_file']
        )
        new_agent.client.tools = final_tools
        agent_registry[new_agent.name] = new_agent
        print(f"   ✅ 加载角色: {new_agent.name} (工具数: {len(final_tools)})")
    print(f"✅ 初始化完成，共加载 {len(agent_registry)} 个 Agent")


# --- 递归子程序循环 ---
def run_subroutine_loop(agent, query, current_depth):
    # 这里也可以加上与 run_main_loop 相同的拦截逻辑，篇幅原因简化
    # 建议生产环境将拦截逻辑封装为函数复用
    messages = [HumanMessage(content=query)]
    MAX_DEPTH = 3
    MAX_TURNS = 7

    if current_depth > MAX_DEPTH:
        return "System Error: Max call depth exceeded."

    print(f"   Now Running Subroutine: {agent.name} (Depth: {current_depth})")
    tools = [update_blackboard, read_blackboard, call_peer]

    for _ in range(MAX_TURNS):
        sys_prompt = agent.get_full_instructions()
        sys_prompt += f"\nNote: You are in a Subroutine Call (Depth {current_depth}). Answer directly."

        response = agent.client.get_completion(
            model=agent.model,
            messages=[SystemMessage(content=sys_prompt)] + messages,
            tools=tools
        )

        if isinstance(response, str):
            print(f"❌ Subroutine Error: {response}")
            break

        messages.append(response)

        if response.tool_calls:
            for tool_call in response.tool_calls:
                fn_name = tool_call["name"]
                args = tool_call["args"]
                print(f"      ⚙️ {agent.name} -> {fn_name}")
                result = "Error"
                if fn_name == "update_blackboard":
                    result = update_blackboard(**args)
                elif fn_name == "read_blackboard":
                    result = read_blackboard(**args)
                elif fn_name == "call_peer":
                    result = run_subroutine_loop(agent_registry[args['target_agent']], args['specific_query'],
                                                 current_depth + 1)
                messages.append(ToolMessage(content=str(result), tool_call_id=tool_call["id"]))
        else:
            return response.content

    return "Error: Timeout."


# --- 全自动主循环 (核心修改区域) ---
def run_main_loop(user_goal):
    if "Summoner" not in agent_registry:
        print("❌ 错误：Summoner 未找到")
        return

    current_agent = agent_registry["Summoner"]
    messages = [HumanMessage(content=f"终极任务目标：{user_goal}\n请检查黑板状态，开始自动推进。")]

    print(f"\n🚀 [AUTO-MODE] 任务启动: {user_goal}\n")
    if monitor: monitor.reset()

    MAX_AUTO_TURNS = 256
    turn_count = 0

    while turn_count < MAX_AUTO_TURNS:
        turn_count += 1
        print(f"🔄 [Turn {turn_count}/{MAX_AUTO_TURNS}] 主角: {current_agent.name}")

        if monitor: monitor.update_state(current_agent.name, action="Thinking...")

        # 动态工具注入 (DeepSeek V3 修复)
        if current_agent.name == "Summoner":
            tools = [dispatch_mission, read_blackboard, mark_mission_complete]
            seen_tools = {t.__name__ for t in tools}
            for agent in agent_registry.values():
                for t in agent.client.tools:
                    if t.__name__ not in seen_tools:
                        tools.append(t)
                        seen_tools.add(t.__name__)
        else:
            tools = current_agent.client.tools

        # 调用 LLM
        response = current_agent.client.get_completion(
            model=current_agent.model,
            messages=[SystemMessage(content=current_agent.get_full_instructions())] + messages,
            tools=tools
        )

        # =========== 🛡️ 拦截器 1: API 级错误熔断 ===========
        if isinstance(response, str):
            error_msg = response
            print(f"\n🚨 API调用失败: {error_msg}")
            print("   🛡️ 策略: 冷却 5秒 -> 重启 Summoner 接管...")
            time.sleep(5)
            current_agent = agent_registry["Summoner"]
            messages.append(HumanMessage(
                content=f"SYSTEM ALERT: API Error detected ('{error_msg}'). Control returned to Summoner."))
            continue

        # =========== 🛡️ 拦截器 2: 无效工具调用 (核心修复: 解决 JSON 逃逸问题) ===========
        # 如果 JSON 格式烂了，LangChain 会生成 invalid_tool_calls。
        # 此时绝对不能把 response 存入历史，否则历史就脏了 (Dangling Tool Call)。
        if hasattr(response, "invalid_tool_calls") and response.invalid_tool_calls:
            print(f"🛑 [INTERCEPT] 拦截到无效工具调用 (JSON Error)！")
            error_details = response.invalid_tool_calls[0].get('error', 'Unknown Error')

            # 策略：不保存本次回答，直接伪造一条 System Error 逼迫 Agent 重试
            reject_msg = (
                f"SYSTEM REJECTION: You attempted to call a tool, but the JSON format was invalid (JSONDecodeError).\n"
                f"Error Details: {error_details}\n"
                f"CRITICAL: If you are writing code, ensure all quotes and special characters inside strings are properly escaped.\n"
                f"Action: Please try again with valid JSON."
            )
            messages.append(HumanMessage(content=reject_msg))
            continue  # 跳过本轮，强迫重试

        # =========== 🛡️ 拦截器 3: 幽灵工具清洗 (双重保险) ===========
        # 如果没有解析出工具，但 raw data 里有残留，手动删除
        if not response.tool_calls and response.additional_kwargs.get("tool_calls"):
            print("👻 清洗幽灵工具残留...")
            del response.additional_kwargs["tool_calls"]

        # =========== 🛡️ 拦截器 4: 输出内容语法质检 (Validator) ===========
        # 只有当 Agent 试图输出文本（而非调工具）时检查
        if not response.tool_calls and response.content and len(response.content) > 10:
            syntax_error = check_code_blocks(response.content)
            if syntax_error:
                print(f"🛑 [INTERCEPT] 代码语法检查未通过！")
                messages.append(HumanMessage(content=
                                             f"SYSTEM REJECTION: Your output code contains syntax errors. Do not output invalid code.\n"
                                             f"Errors:\n{syntax_error}\n"
                                             f"Action: Fix the code and output again."
                                             ))
                continue

        # =========== 🛡️ 拦截器 5: 上下文瘦身 ===========
        if response.tool_calls:
            for tool_call in response.tool_calls:
                args = tool_call.get("args", {})
                if isinstance(args, dict) and "content" in args and isinstance(args["content"], str):
                    if len(args["content"]) > 200:
                        # 修改引用，折叠历史记录中的长文本
                        args["content"] = f"... (Content omitted, length: {len(args['content'])} chars) ..."

        # --- 如果通过了所有拦截，才允许存入历史 ---
        messages.append(response)

        # --- 处理文本回复 ---
        if not response.tool_calls:
            print(f"🤖 {current_agent.name} 思考: {response.content}")
            if current_agent.name != "Summoner":
                print("   ↩️ 工兵任务结束，控制权交还 Summoner...")
                current_agent = agent_registry["Summoner"]
                messages.append(HumanMessage(content="Worker task completed. Check Blackboard."))
            continue

        # --- 处理工具调用 ---
        for tool_call in response.tool_calls:
            fn_name = tool_call["name"]
            args = tool_call["args"]
            print(f"⚙️  {current_agent.name} -> {fn_name}")

            # 1. 任务完成
            if fn_name == "mark_mission_complete":
                print("\n🎉🎉🎉 任务全自动完成！")
                print(args.get('final_report'))
                mark_mission_complete(**args)
                return

            # 2. 任务分发
            elif fn_name == "dispatch_mission":
                new_agent = dispatch_mission(**args)
                if isinstance(new_agent, DynamicAgent):
                    print(f"👉 指挥棒交给 -> {new_agent.name}")
                    messages.append(
                        ToolMessage(content=f"Transferred to {new_agent.name}", tool_call_id=tool_call["id"]))
                    current_agent = new_agent
                else:
                    messages.append(ToolMessage(content=str(new_agent), tool_call_id=tool_call["id"]))

            # 3. P2P 互调
            elif fn_name == "call_peer":
                target_name = args.get('target_agent')
                if target_name in agent_registry:
                    res = run_subroutine_loop(agent_registry[target_name], args['specific_query'], 1)
                else:
                    res = f"System Error: Agent '{target_name}' not found."
                messages.append(ToolMessage(content=str(res), tool_call_id=tool_call["id"]))

            # 4. 通用工具
            else:
                if fn_name in globals():
                    res = globals()[fn_name](**args)
                elif fn_name in SKILL_REGISTRY:
                    res = SKILL_REGISTRY[fn_name](**args)
                else:
                    res = f"System Error: Tool '{fn_name}' not found."
                messages.append(ToolMessage(content=str(res), tool_call_id=tool_call["id"]))

    print("⚠️ 警告：达到最大自动运行轮数，强制停止。")


if __name__ == "__main__":
    print("🔄 初始化蜂群系统...")
    load_agents()
    print("✅ 系统就绪。")
    while True:
        try:
            user_input = input("\n🙋 召唤师指令: ").strip()
            if user_input.lower() in ['q', 'exit']: break
            if not user_input: continue
            run_main_loop(user_input)
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception as e:
            print(f"Error: {e}")