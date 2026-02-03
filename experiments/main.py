import sys
import time
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from llm_connection import LLMClient


# ================= 1. 定义 Agent 类 =================
class Agent:
    def __init__(self, name, model, provider, instructions, tools=None):
        self.name = name
        self.model = model
        self.instructions = instructions
        self.tools = tools if tools else []
        self.client = LLMClient(provider=provider)


# ================= 2. 定义工具 (Tools) =================

# --- 业务工具：工兵干活用的 ---
def check_server_status():
    """查询服务器当前的CPU、内存和网络延迟状态"""
    # 模拟思考时间
    time.sleep(1)
    return "【数据库反馈】Server_A: CPU 12%, RAM 40%, Latency 20ms. 状态: 健康。"


def query_sales_data():
    """查询今日的销售数据"""
    time.sleep(1)
    return "【数据库反馈】今日总销售额: $5,400. 订单数: 120。"


# --- 路由工具：召唤师用的 ---
def summon_worker_agent():
    """召唤【全能工兵】来处理具体的查询任务"""
    return agent_registry["Worker"]


# --- 路由工具：工兵用的 (干完活交卷) ---
def transfer_to_summary():
    """任务执行完毕，将结果移交给【总结专员】进行汇总"""
    return agent_registry["Summary"]


# ================= 3. 配置 Agent 战队 =================

agent_registry = {}

# A. 召唤师 (Summoner) - 负责分发
summoner = Agent(
    name="Summoner(召唤师)",
    model="deepseek-chat",  # 聪明且便宜
    provider="deepseek",
    instructions="""你是指挥官。
    1. 分析用户意图。
    2. 如果需要查数据/状态，**必须**调用 `summon_worker_agent` 派单。
    3. 并在调用工具前，用简短的话告诉用户你正在派谁。
    4. 如果是闲聊，你自己回。
    """,
    tools=[summon_worker_agent]
)

# B. 召唤物 (Worker) - 负责干活
worker = Agent(
    name="Worker(工兵)",
    model="openai/gpt-4o-mini",  # 速度快
    provider="openrouter",
    instructions="""你是执行者。
    1. 根据上文要求，选择使用 `check_server_status` 或 `query_sales_data`。
    2. **获得数据后，必须立刻调用 `transfer_to_summary` 将结果移交，严禁自己直接输出最终结果！**
    """,
    tools=[check_server_status, query_sales_data, transfer_to_summary]
)

# C. 总结者 (Summary) - 负责汇报
summary_agent = Agent(
    name="Summary(总结者)",
    model="deepseek-chat",  # 总结能力强
    provider="deepseek",
    instructions="""你是汇报员。
    1. 你会收到工兵提交的原始数据。
    2. 请将数据整理成一份精美的报告反馈给用户。
    3. 你的回复将作为最终结果结束流程。
    """,
    tools=[]  # 它不需要工具，只负责说话
)

# 注册
agent_registry["Summoner"] = summoner
agent_registry["Worker"] = worker
agent_registry["Summary"] = summary_agent


# ================= 4. 蜂群可视化循环 =================

def run_swarm(user_input):
    current_agent = summoner
    messages = [HumanMessage(content=user_input)]

    # 统计召唤物数量（除召唤师外的活跃Agent）
    active_worker_count = 0

    print("\n" + "=" * 50)
    print(f"🎬 任务启动: {user_input}")
    print("=" * 50 + "\n")

    while True:
        # 1. 打印当前持球人
        print(f"🧠 [{current_agent.name}] 正在思考...", end="", flush=True)

        # 2. 调用 LLM
        current_messages = [SystemMessage(content=current_agent.instructions)] + messages
        response = current_agent.client.get_completion(
            model=current_agent.model,
            messages=current_messages,
            tools=current_agent.tools
        )
        messages.append(response)
        print(" 完成。")

        # 3. 处理工具调用
        if response.tool_calls:
            for tool_call in response.tool_calls:
                fn_name = tool_call["name"]

                # --- 场景 A: 召唤师派单 ---
                if fn_name == "summon_worker_agent":
                    print(f"\n📢 [系统广播] 召唤师决定: 启动工兵 Agent 处理任务！")
                    print(f"📜 [派单日志] 任务控制权: Summoner -> Worker")
                    active_worker_count = 1
                    print(f"👥 当前战场召唤物数量: {active_worker_count}")

                    current_agent = agent_registry["Worker"]

                    # 记录工具调用结果(为了闭环)
                    messages.append(ToolMessage(content="Worker Joined", tool_call_id=tool_call["id"]))

                # --- 场景 B: 工兵交卷给总结者 ---
                elif fn_name == "transfer_to_summary":
                    print(f"\n📨 [系统广播] 工兵任务完成，正在移交数据给总结者...")
                    print(f"📜 [流转日志] 任务控制权: Worker -> Summary")

                    current_agent = agent_registry["Summary"]
                    messages.append(ToolMessage(content="Data Transferred", tool_call_id=tool_call["id"]))

                # --- 场景 C: 普通干活工具 ---
                else:
                    print(f"🛠️  [{current_agent.name}] 调用工具: {fn_name} ... ", end="")
                    # 执行函数
                    if fn_name == "check_server_status":
                        result = check_server_status()
                    elif fn_name == "query_sales_data":
                        result = query_sales_data()
                    else:
                        result = "Unknown Tool"

                    print(f"✅ 获取结果")
                    # 这里打印具体的思考过程/中间数据
                    print(f"   └── 数据: {result}")

                    messages.append(ToolMessage(content=result, tool_call_id=tool_call["id"]))

            # 无论什么工具调用，都进入下一轮循环，让新 Agent 或原 Agent 继续处理
            continue

        # 4. 如果没有工具调用，说明是最终文本输出
        else:
            final_content = response.content
            print("\n" + "=" * 50)
            print(f"🏁 [{current_agent.name}] 最终报告")
            print("=" * 50)
            print(final_content)
            print("\n✅ 流程结束。")
            break


# ================= 5. 入口 =================

if __name__ == "__main__":
    # 由用户决定初始任务
    task = input("🙋 请输入你的任务 (例如: '帮我查一下服务器状态'): ")
    if task.strip():
        run_swarm(task)
    else:
        print("❌ 未输入任务，程序退出。")