# File: skills/Blackboard_Skills.py
from Core.memory import project_context


def update_blackboard(key: str, content: str):
    """
    Update shared project information.
    Keys: project_manifest, file_registry, runtime_logs
    """
    # 1. 拦截非法 Key
    if key in ["file_registry", "memory_stream"]:
        return f"SYSTEM REJECTION: '{key}' is auto-maintained."

    # 2. 写入内存 (不再直接调用 Monitor)
    project_context.write(key, content)

    return f"Blackboard updated: {key}"


def read_blackboard(key: str):
    """Read shared information."""
    return project_context.read(key)