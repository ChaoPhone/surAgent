# File: Core/bus.py
from collections import defaultdict
from typing import Callable, Any


class EventBus:
    def __init__(self):
        self._subscribers = defaultdict(list)

    def subscribe(self, event_type: str, handler: Callable):
        self._subscribers[event_type].append(handler)

    def publish(self, event_type: str, data: Any = None):
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                try:
                    handler(data)
                except Exception as e:
                    print(f"⚠️ Event Handler Error [{event_type}]: {e}")


class EventType:
    TOKEN_USAGE = "TOKEN_USAGE"
    AGENT_THINK_START = "THINK_START"  # 注意：Engine用的是 AGENT_THINK，Monitor用的是 AGENT_THINK，这里需保持字符串一致
    # 你的 Engine.py line 39 用的是 AGENT_THINK，但这里定义的是 AGENT_THINK_START
    # 建议统一改为 AGENT_THINK
    AGENT_THINK = "THINK_START"

    AGENT_ACTION = "AGENT_ACTION"
    AGENT_SWITCH = "AGENT_SWITCH"
    BLACKBOARD_UPDATE = "BB_UPDATE"
    MISSION_COMPLETE = "MISSION_DONE"

    # 🔥 必须补上这两个，否则 Monitor 订阅的字符串和 Skills 发布的可能不一致（如果硬编码字符串的话）
    PARALLEL_START = "PARALLEL_START"
    WORKER_FINISH = "WORKER_FINISH"