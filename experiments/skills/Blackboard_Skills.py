# skills/Blackboard_Skills.py
from Core.memory import project_context

def update_blackboard(key: str, content: str):
    """
    更新项目黑板上的共享信息。
    Keys: project_manifest, file_registry, runtime_logs
    """
    # 强制拦截 Agent 手动更新这些自动维护的 Key
    if key in ["file_registry", "memory_stream"]:
        return f"SYSTEM REJECTION: '{key}' is auto-maintained by the system. You CANNOT update it manually. Go write some real code using 'write_file'!"
    return project_context.write(key, content)


def read_blackboard(key: str):
    """
    读取黑板信息。
    """
    return project_context.read(key)