# File: Core/engine.py
import copy
import traceback
import time
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, AIMessage
from Core.bus import EventType

# 🔥 全局 Bus 引用
_GLOBAL_BUS = None
_GLOBAL_AGENTS = {}


def get_agent(name):
    """
    [全局辅助函数] 获取已注册的 Agent 实例
    供 Skills 模块调用 (如 Pruner)
    """
    return _GLOBAL_AGENTS.get(name)


def publish_event(event_type, data):
    if _GLOBAL_BUS:
        _GLOBAL_BUS.publish(event_type, data)


class Orchestrator:
    def __init__(self, bus, agent_registry, skill_registry):
        global _GLOBAL_BUS, _GLOBAL_AGENTS
        _GLOBAL_BUS = bus
        _GLOBAL_AGENTS = agent_registry
        self.bus = bus
        self.agents = agent_registry
        self.skills = skill_registry
        self.root_agent = agent_registry.get("Summoner")

    def _clean_response_immediately(self, response):
        """
        🔪 外科手术式清洗：源头阉割
        这是解决 400 错误的终极手段。
        如果决定把这条消息当作纯文本处理，必须彻底抹除所有 '潜意识' 里的工具调用痕迹。
        """
        # 1. 清空 LangChain 的标准字段
        if hasattr(response, 'tool_calls'):
            response.tool_calls = []

        if hasattr(response, 'invalid_tool_calls'):
            response.invalid_tool_calls = []

        # 2. 清空底层原始数据 (这才是 400 错误的真凶！)
        if hasattr(response, 'additional_kwargs'):
            # OpenAI/DeepSeek 协议
            if 'tool_calls' in response.additional_kwargs:
                response.additional_kwargs.pop('tool_calls')
            # 旧版 Function Calling 协议
            if 'function_call' in response.additional_kwargs:
                response.additional_kwargs.pop('function_call')

        return response

    def _sanitize_history_before_send(self, messages):
        """
        🛡️ 二道防线：发送前再次检查历史
        防止之前的轮次有漏网之鱼。
        """
        cleaned = []
        for i, msg in enumerate(messages):
            # 深拷贝，避免修改原始引用导致奇怪的副作用
            msg_copy = copy.deepcopy(msg)

            if isinstance(msg_copy, AIMessage):
                # 检查是否包含工具调用数据
                raw_tools = msg_copy.additional_kwargs.get('tool_calls', [])
                parsed_tools = getattr(msg_copy, 'tool_calls', [])

                has_tools = bool(raw_tools) or bool(parsed_tools)

                if has_tools:
                    # 检查下一条是不是 ToolMessage
                    next_is_tool = False
                    if i + 1 < len(messages):
                        if isinstance(messages[i + 1], ToolMessage):
                            next_is_tool = True

                    # 如果是断头调用（后面没跟结果），直接阉割
                    if not next_is_tool:
                        # print(f"🔧 [Auto-Fix] 修复历史记录第 {i} 条的幽灵调用")
                        msg_copy.tool_calls = []
                        msg_copy.invalid_tool_calls = []
                        if 'tool_calls' in msg_copy.additional_kwargs:
                            msg_copy.additional_kwargs.pop('tool_calls')

            cleaned.append(msg_copy)
        return cleaned

    def run(self, goal):
        if not self.root_agent:
            print("❌ 错误: 未找到 Summoner。")
            return

        current_agent = self.root_agent
        messages = [HumanMessage(content=f"目标: {goal}")]

        self.bus.publish(EventType.AGENT_SWITCH, {"to": current_agent.name})

        for turn in range(256):
            self.bus.publish(EventType.AGENT_THINK, {"agent": current_agent.name})

            # 🔥 [防线 1] 发送前全面安检
            safe_messages = self._sanitize_history_before_send(messages)

            try:
                # 调用 LLM
                response = current_agent.client.get_completion(
                    model=current_agent.model,
                    messages=[SystemMessage(content=current_agent.get_full_instructions())] + safe_messages,
                    tools=current_agent.client.tools
                )
            except Exception as e:
                print(f"🚨 LLM 调用崩溃: {e}")
                time.sleep(3)
                continue

            if isinstance(response, str):
                print(f"🚨 接口错误: {response}")
                break

            # -----------------------------------------------------------
            # ⚖️ 核心分支判断
            # -----------------------------------------------------------

            # 判断是否真的有工具调用 (显性且有效)
            has_valid_tool_calls = bool(response.tool_calls)

            if has_valid_tool_calls:
                # === 分支 A: 执行工具 ===
                self.bus.publish(EventType.AGENT_ACTION, {"agent": current_agent.name, "action": "正在执行工具..."})

                # 入库前，不用清洗，因为我们马上会追加 ToolMessage
                messages.append(response)

                for tc in response.tool_calls:
                    tool_result = "System Execution Error"
                    try:
                        fn_name = tc["name"]
                        args = tc["args"]

                        # === 特殊逻辑拦截 ===
                        if fn_name == "dispatch_mission":
                            target = args.get("target_agent")
                            if target in self.agents:
                                prev_agent = current_agent.name
                                current_agent = self.agents[target]
                                tool_result = f"已将控制权移交给 {target}"
                                self.bus.publish(EventType.AGENT_SWITCH, {"from": prev_agent, "to": target})
                            else:
                                tool_result = f"错误: 未找到 Agent {target}。"

                        elif fn_name == "mark_mission_complete":
                            print(f"🏁 任务完成: {args.get('result')}")
                            self.bus.publish(EventType.MISSION_COMPLETE, {"result": args.get('result')})
                            messages.append(ToolMessage(content=str(args.get('result')), tool_call_id=tc["id"]))
                            return

                        elif fn_name in self.skills:
                            # 记录日志
                            action_desc = f"执行技能: {fn_name}"
                            if fn_name == "write_file": action_desc += f" ({args.get('file_path')})"
                            self.bus.publish(EventType.AGENT_ACTION,
                                             {"agent": current_agent.name, "action": action_desc})

                            # 真正执行
                            tool_result = self.skills[fn_name](**args)

                            # 拦截黑板
                            if fn_name == "update_blackboard":
                                self.bus.publish(EventType.BLACKBOARD_UPDATE, args)
                        else:
                            tool_result = f"Error: Tool '{fn_name}' not found."

                    except Exception as e:
                        tool_result = f"Tool Execution Failed: {str(e)}"

                    # 🔥 [关键] 必须追加结果！
                    messages.append(ToolMessage(content=str(tool_result), tool_call_id=tc["id"]))

            else:
                # === 分支 B: 纯文本对话 ===

                # 🔥 [防线 2] 源头阉割！
                # 既然进了这个分支，就说明我们不打算执行工具。
                # 那么，任何残留在 response 里的工具信息都是有害的“病毒”。
                # 必须立即清除，防止带入下一轮历史。
                clean_response = self._clean_response_immediately(response)

                messages.append(clean_response)

                # 处理交接逻辑 (通过文本指令触发)
                if current_agent.name != "Summoner":
                    self.bus.publish(EventType.AGENT_ACTION,
                                     {"agent": current_agent.name, "action": "任务段落结束，交还控制权"})
                    self.bus.publish(EventType.AGENT_SWITCH, {"from": current_agent.name, "to": "Summoner"})

                    current_agent = self.agents["Summoner"]
                    messages.append(HumanMessage(content="Worker finished. Control returned to Summoner."))


# 工厂函数 (保持不变)
def create_ephemeral_agent(role_name, system_prompt, model="deepseek-chat"):
    from Core.agent import DynamicAgent
    if _GLOBAL_BUS is None:
        raise RuntimeError("系统尚未初始化")
    agent = DynamicAgent(name=role_name, model=model, provider="deepseek", base_prompt_file=None, bus=_GLOBAL_BUS)
    agent.get_full_instructions = lambda patch=None: system_prompt
    return agent