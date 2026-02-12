import os
import json
import time
import copy

from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage

# 核心注册表 (Registry)
AGENT_REGISTRY = {}
SKILL_REGISTRY = {}

# 延迟导入，防止循环引用
def get_dynamic_agent_class():
    from Core.agent import DynamicAgent
    return DynamicAgent

def get_validator():
    from Core.validator import check_code_blocks
    return check_code_blocks


def get_agent(name: str):
    return AGENT_REGISTRY.get(name)


try:
    from Debug.monitor import monitor
except ImportError:
    monitor = None


# ================= 辅助逻辑 =================

def execute_agent_turn(agent, messages, tools, patch=None):
    """
    统一的 Agent 执行回合。
    注意：这里不再进行“上下文瘦身”，必须保留完整参数给执行层！
    """
    if monitor:
        monitor.update_state(agent.name, action="Thinking...")

    response = agent.client.get_completion(
        model=agent.model,
        messages=[SystemMessage(content=agent.get_full_instructions(dynamic_patch=patch))] + messages,
        tools=tools
    )

    # 1. API 级错误拦截
    if isinstance(response, str):
        print(f"\n🚨 API调用失败: {response}")
        return response, False

    # 2. 无效工具调用拦截
    if hasattr(response, "invalid_tool_calls") and response.invalid_tool_calls:
        print(f"🛑 [INTERCEPT] 拦截到无效工具调用 (JSON Error)！")
        error_details = response.invalid_tool_calls[0].get('error', 'Unknown Error')
        # 返回 response 以保持流程，后续循环会处理报错回复
        return response, True

    # 3. 幽灵工具清洗
    if not response.tool_calls and response.additional_kwargs.get("tool_calls"):
        del response.additional_kwargs["tool_calls"]

    # 4. 输出内容语法质检
    if not response.tool_calls and response.content and len(response.content) > 10:
        check_code_blocks = get_validator()
        syntax_error = check_code_blocks(response.content)
        if syntax_error:
            print(f"🛑 [INTERCEPT] 代码语法检查未通过！")
            reject_msg = f"SYSTEM REJECTION: Your output code contains syntax errors.\nErrors:\n{syntax_error}\nAction: Fix the code."
            return reject_msg, True

    # 【重要改动】删除了原来的“第5步 上下文瘦身”，防止在执行前污染参数！

    return response, True


# ================= 引擎核心 =================

def load_agents():
    # 依赖注入：主动从 skills 包拉取导出的工具
    from skills import EXPORTED_SKILLS
    SKILL_REGISTRY.update(EXPORTED_SKILLS)

    path = os.path.join(os.path.dirname(__file__), "..", "config", "agents_config.json")
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
        base_tools = [SKILL_REGISTRY["read_blackboard"]]
        json_tools = []
        if "tools" in cfg:
            for t_name in cfg["tools"]:
                if t_name in SKILL_REGISTRY:
                    json_tools.append(SKILL_REGISTRY[t_name])
                else:
                    print(f"⚠️ 警告: Agent [{cfg['name']}] 配置了未知工具 '{t_name}'")

        final_tools = list(set(base_tools + json_tools))
        DynamicAgent = get_dynamic_agent_class()
        new_agent = DynamicAgent(name=cfg['name'], model=cfg['model'], provider=cfg['provider'],
                                 base_prompt_file=cfg['prompt_file'], is_root=cfg.get("is_root", False))
        new_agent.client.tools = final_tools
        AGENT_REGISTRY[new_agent.name] = new_agent
        print(f"   ✅ 加载角色: {new_agent.name} (工具数: {len(final_tools)})")


def run_subroutine_loop(agent, query, current_depth):
    from skills.Pruner_Skills import generate_code_skeleton
    messages = [HumanMessage(content=query)]
    MAX_DEPTH, MAX_TURNS = 3, 7

    if current_depth > MAX_DEPTH:
        return "System Error: Max call depth exceeded."

    print(f"   Now Running Subroutine: {agent.name} (Depth: {current_depth})")
    tools = [SKILL_REGISTRY["update_blackboard"], SKILL_REGISTRY["read_blackboard"], SKILL_REGISTRY["call_peer"]]

    for _ in range(MAX_TURNS):
        response, should_continue = execute_agent_turn(agent, messages, tools)
        if not should_continue: return f"Error: {response}"

        if isinstance(response, str):
            messages.append(HumanMessage(content=response))
            continue

        messages.append(response)

        if response.tool_calls:
            # 1. 深拷贝一份完整参数用于执行 (绝对不能动！)
            execution_tool_calls = copy.deepcopy(response.tool_calls)

            # 2. 原地修改原始对象，利用 Pruner 生成“代码骨架”存入记忆
            for tc in response.tool_calls:
                args = tc.get("args", {})

                # 针对写文件类操作进行瘦身
                if tc["name"] in ["write_file", "replace_file_lines"]:
                    # 处理 content 参数
                    if "content" in args and isinstance(args["content"], str):
                        original_len = len(args["content"])
                        if original_len > 500:  # 超过 500 字符才触发压缩
                            # ✨ 调用 Pruner 的 AST 压缩技能
                            compressed_code = generate_code_skeleton(args["content"])

                            # 加上标记，让 Agent 知道这不是完整代码
                            args[
                                "content"] = f"# [System: Code Compressed for Memory. Real file on disk is complete.]\n{compressed_code}"

                    # 处理 new_content 参数 (针对 replace_file_lines)
                    if "new_content" in args and isinstance(args["new_content"], str):
                        if len(args["new_content"]) > 500:
                            args["new_content"] = generate_code_skeleton(args["new_content"])

            # 3. 遍历执行（使用完整数据的拷贝）
            for tool_call in execution_tool_calls:
                fn_name = tool_call["name"]
                execute_args = tool_call["args"]  # 这是完整的参数

                # 打印日志时可以用瘦身后的参数（从原始 response 里取对应的）来避免刷屏，或者直接截断打印
                args_str = str(execute_args)[:100] + ("..." if len(str(execute_args)) > 100 else "")
                print(f"      ⚙️ {agent.name} -> {fn_name}({args_str})")

                try:
                    if fn_name == "call_peer":
                        target = execute_args.get("target_agent")
                        if target == agent.name:
                            res = f"System Error: Recursion forbidden."
                        else:
                            execute_args["_depth"] = current_depth + 1
                            res = SKILL_REGISTRY["call_peer"](**execute_args)
                    elif fn_name in SKILL_REGISTRY:
                        res = SKILL_REGISTRY[fn_name](**execute_args)
                    else:
                        res = f"System Error: Tool '{fn_name}' not found."
                except Exception as e:
                    res = f"System Error: {str(e)}"

                messages.append(ToolMessage(content=str(res), tool_call_id=tool_call["id"]))

        # 处理无效工具调用
        if hasattr(response, "invalid_tool_calls") and response.invalid_tool_calls:
            for inv_call in response.invalid_tool_calls:
                messages.append(
                    ToolMessage(content=f"SYSTEM REJECTION: Invalid JSON", tool_call_id=inv_call.get("id", "unknown")))

        if not response.tool_calls and not (hasattr(response, "invalid_tool_calls") and response.invalid_tool_calls):
            return response.content

    return "Error: Timeout."


def run_main_loop(user_goal):
    root_agent = None
    for agent in AGENT_REGISTRY.values():
        if agent.is_root:
            root_agent = agent
            break
    if not root_agent: root_agent = AGENT_REGISTRY.get("Summoner")
    if not root_agent: return

    current_agent = root_agent
    messages = [HumanMessage(content=f"终极任务目标：{user_goal}\n请检查黑板状态，开始自动推进。")]
    print(f"\n🚀 [AUTO-MODE] 任务启动: {user_goal}\n")
    if monitor: monitor.reset()

    MAX_AUTO_TURNS = 256
    for turn_count in range(1, MAX_AUTO_TURNS + 1):
        print(f"🔄 [Turn {turn_count}/{MAX_AUTO_TURNS}] 主角: {current_agent.name}")
        tools = current_agent.client.tools

        response, should_continue = execute_agent_turn(current_agent, messages, tools)

        if not should_continue:
            time.sleep(5)
            current_agent = AGENT_REGISTRY["Summoner"]
            messages.append(HumanMessage(content=f"SYSTEM ALERT: API Error. Control returned to Summoner."))
            continue

        if isinstance(response, str):
            messages.append(HumanMessage(content=response))
            continue

        messages.append(response)

        if response.tool_calls:
            # 【核心修复 1】深拷贝一份完整参数用于执行
            execution_tool_calls = copy.deepcopy(response.tool_calls)

            # 【核心修复 2】原地修改原始对象，为历史记录瘦身
            for tc in response.tool_calls:
                if "args" in tc and "content" in tc["args"] and isinstance(tc["args"]["content"], str):
                    if len(tc["args"]["content"]) > 200:
                        tc["args"]["content"] = f"... (Content omitted, length: {len(tc['args']['content'])} chars) ..."

            # 遍历执行（使用完整数据的拷贝）
            for tool_call in execution_tool_calls:
                fn_name = tool_call["name"]
                execute_args = tool_call["args"]  # 完整参数

                args_str = str(execute_args)[:100] + ("..." if len(str(execute_args)) > 100 else "")
                print(f"⚙️  {current_agent.name} -> {fn_name}({args_str})")

                try:
                    if fn_name == "dispatch_mission":
                        new_agent = SKILL_REGISTRY["dispatch_mission"](**execute_args)
                        DynamicAgent = get_dynamic_agent_class()
                        if isinstance(new_agent, DynamicAgent):
                            print(f"👉 指挥棒交给 -> {new_agent.name}")
                            res = f"Transferred to {new_agent.name}"
                            current_agent = new_agent
                        else:
                            res = str(new_agent)
                    elif fn_name in SKILL_REGISTRY:
                        res = SKILL_REGISTRY[fn_name](**execute_args)
                    else:
                        res = f"Error: Tool {fn_name} not found."
                except Exception as e:
                    res = f"System Error: {str(e)}"

                messages.append(ToolMessage(content=str(res), tool_call_id=tool_call["id"]))

                if fn_name == "mark_mission_complete" and "MISSION_COMPLETE_SIGNAL" in str(res):
                    print("\n🎉🎉🎉 任务全自动完成！\n报告：", execute_args.get('final_report'))
                    return

        if hasattr(response, "invalid_tool_calls") and response.invalid_tool_calls:
            for inv_call in response.invalid_tool_calls:
                messages.append(
                    ToolMessage(content=f"SYSTEM REJECTION: Invalid JSON", tool_call_id=inv_call.get("id", "unknown")))

        if not response.tool_calls and not (hasattr(response, "invalid_tool_calls") and response.invalid_tool_calls):
            print(f"🤖 {current_agent.name} 思考: {response.content}")
            if current_agent.name != "Summoner":
                print("   ↩️ 工兵任务结束，控制权交还 Summoner...")
                current_agent = AGENT_REGISTRY["Summoner"]
                messages.append(HumanMessage(content="Worker task completed. Check Blackboard."))
            continue

    print("⚠️ 警告：达到最大自动运行轮数，强制停止。")