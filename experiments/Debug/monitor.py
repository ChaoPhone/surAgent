import json
import os
import threading
import time


class SystemMonitor:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(SystemMonitor, cls).__new__(cls)
                    # 如果文件不存在，或者需要重置，则初始化
                    if not os.path.exists("Debug/run_state.json"):
                        cls._instance.reset()
                    else:
                        # 尝试加载现有数据，避免重启丢失
                        cls._instance.load()
        return cls._instance

    def load(self):
        try:
            with open("Debug/run_state.json", "r", encoding="utf-8") as f:
                self.data = json.load(f)
            # 确保兼容性：如果旧数据没有 blackboard 字段，补上
            if "blackboard" not in self.data:
                self.data["blackboard"] = {}
            if "sequence_trace" not in self.data:
                self.data["sequence_trace"] = []
        except:
            self.reset()

    def reset(self):
        """重置监控数据"""
        self.data = {
            "total_tokens": 0,
            "cost_estimate": 0.0,
            "current_agent": "Summoner",
            "last_active_time": time.time(),
            "logs": [],
            "sequence_trace": [],
            "blackboard": {}  # 【新增】存储黑板键值对
        }
        self._append_trace("Summoner")
        self._save()

    def log_token_usage(self, input_tokens, output_tokens, model="unknown"):
        """记录 Token 消耗"""
        # 简单估算：假设 Input $1/1M, Output $2/1M
        cost = (input_tokens * 1e-6) + (output_tokens * 2e-6)
        self.data["total_tokens"] += (input_tokens + output_tokens)
        self.data["cost_estimate"] += cost
        self._save()

    def log_blackboard(self, key, content):
        """【新增】记录黑板更新"""
        self.data["blackboard"][key] = content
        self._save()

    def update_state(self, current_agent, action=None, target=None):
        """更新状态与日志"""
        self.data["current_agent"] = current_agent
        self.data["last_active_time"] = time.time()

        # 更新轨迹
        self._append_trace(current_agent)

        # 格式化日志
        timestamp = time.strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {current_agent}"
        if action:
            log_entry += f": {action}"
        if target:
            log_entry += f" -> {target}"

        self.data["logs"].append(log_entry)
        # 【修改】保留最近 200 条日志
        if len(self.data["logs"]) > 200:
            self.data["logs"] = self.data["logs"][-200:]

        self._save()

    def _append_trace(self, agent_name):
        trace = self.data["sequence_trace"]
        # 仅当角色发生切换时才记录，避免重复
        if not trace or trace[-1] != agent_name:
            trace.append(agent_name)

    def _save(self):
        """持久化存储"""
        os.makedirs("Debug", exist_ok=True)
        try:
            with open("Debug/run_state.json", "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


# 全局单例
monitor = SystemMonitor()