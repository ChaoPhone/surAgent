def dispatch_mission(target_agent: str, task_description: str, prompt_patch: str = ""):
    """
    [Summoner Only] 指派任务给特定的 Agent。
    """
    from Core.engine import get_agent
    worker = get_agent(target_agent)
    if not worker:
        return f"Error: Agent {target_agent} not found."
    worker.apply_patch(prompt_patch)
    return worker


def mark_mission_complete(final_report: str):
    """
    [Summoner Only] 标记任务完成并提交最终报告。
    """
    return f"MISSION_COMPLETE_SIGNAL: {final_report}"
