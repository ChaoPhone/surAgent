# File: main.py
import os
import json
from Core.bus import EventBus
from Debug.monitor import UnifiedMonitor
from Core.engine import Orchestrator
from Core.agent import DynamicAgent
from skills import EXPORTED_SKILLS


def load_config():
    # 获取当前脚本所在目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "config", "agents_config.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    print("🔄 正在初始化事件驱动架构...")

    # 1. 创建总线 (Spine)
    bus = EventBus()

    # 2. 挂载监控 (Eyes) - 自动订阅总线
    monitor = UnifiedMonitor(bus)

    # 3. 加载 Agents (Limbs)
    agent_configs = load_config()
    agent_registry = {}
    
    for cfg in agent_configs:
        # 实例化 Agent，注入总线
        agent = DynamicAgent(
            name=cfg['name'],
            model=cfg['model'],
            provider=cfg['provider'],
            base_prompt_file=cfg['prompt_file'],
            bus=bus
        )
        
        # 组装工具
        my_skills = []
        if "read_blackboard" in EXPORTED_SKILLS:
            my_skills.append(EXPORTED_SKILLS["read_blackboard"])
            
        for t_name in cfg.get("tools", []):
            if t_name in EXPORTED_SKILLS:
                my_skills.append(EXPORTED_SKILLS[t_name])
        
        agent.client.tools = list(set(my_skills))
        agent_registry[agent.name] = agent
        print(f"   ✅ Agent 就绪: {agent.name}")

    # 4. 启动引擎 (Brain)
    orchestrator = Orchestrator(bus, agent_registry, EXPORTED_SKILLS)
    
    print("✅ 系统已就绪。请输入指令...")
    try:
        user_goal = input("🙋 目标任务: ")
        # 5. Run!
        orchestrator.run(user_goal)
    except KeyboardInterrupt:
        print("\n👋 用户终止系统。")


if __name__ == "__main__":
    main()