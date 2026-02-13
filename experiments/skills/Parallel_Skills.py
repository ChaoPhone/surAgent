# File: skills/Parallel_Skills.py
import json
import concurrent.futures
from langchain_core.messages import HumanMessage
from Core.bus import EventType  # 导入事件类型


def batch_coding_tasks(tasks: list):
    """
    并行执行多个编码/设计任务。
    Args:
        tasks: list[dict], 示例:
        [
            {"role": "UI_Dev", "instruction": "写一个登录页", "temperature": 0.1},
            {"role": "Creative_Writer", "instruction": "写一段游戏剧情", "temperature": 0.8}
        ]
    """
    # 🔥 从 Engine 导入发布接口和工厂函数 (延迟导入防循环)
    from Core.engine import create_ephemeral_agent, publish_event

    results = {}

    # 1. 🔥 [架构修复] 发布并行开始事件 (Payload 需匹配 Monitor 的 _on_parallel_start)
    publish_event(EventType.PARALLEL_START, {
        "manager": "TechLead",
        "tasks": tasks
    })

    def _worker_process(task):
        role = task.get("role", "Worker")
        instruction = task.get("instruction")
        temp = task.get("temperature", 0.2)
        model = task.get("model", "deepseek-chat")

        # 控制台辅助日志 (可选)
        print(f"    ├─ 👷 [Worker Started] {role}...")

        try:
            # 2. 创建临时 Agent
            agent = create_ephemeral_agent(role, instruction, model)

            # 3. 执行调用
            response = agent.client.get_completion(
                model=agent.model,
                messages=[HumanMessage(content="Start execution based on system instructions.")],
                temperature=temp
            )

            # 4. 🔥 [架构修复] 发布 Worker 完成事件
            publish_event(EventType.WORKER_FINISH, {
                "role": role,
                "status": "success",
                "output": response.content
            })

            print(f"    └─ ✅ [Worker Finished] {role} ({len(response.content)} chars).")
            return {"status": "success", "output": response.content}

        except Exception as e:
            # 5. 🔥 [架构修复] 发布 Worker 报错事件
            publish_event(EventType.WORKER_FINISH, {
                "role": role,
                "status": "error",
                "output": str(e)
            })
            print(f"    └─ ❌ [Worker Failed] {role}: {str(e)}")
            return {"status": "error", "error": str(e)}

    # 使用线程池并发
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_map = {executor.submit(_worker_process, t): t.get('role', 'Worker') for t in tasks}

        for future in concurrent.futures.as_completed(future_map):
            role = future_map[future]
            try:
                results[role] = future.result()
            except Exception as e:
                results[role] = {"status": "crash", "error": str(e)}

    return json.dumps(results, indent=2, ensure_ascii=False)