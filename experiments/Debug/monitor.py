import json
import time
import os
import threading


class SystemMonitor:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(SystemMonitor, cls).__new__(cls)
                    cls._instance.reset()
        return cls._instance

    def reset(self):
        """重置监控数据"""
        self.data = {
            "total_tokens": 0,
            "cost_estimate": 0.0,
            "current_agent": "Summoner",
            "last_active_time": time.time(),
            "logs": [],
            # 【修改点 1】移除 graph_edges，改为 sequence_trace
            # graph_edges: [],  <-- 删除这行
            "sequence_trace": [] # <-- 新增这行：用于存储有序的 Agent 切换记录
        }
        # 初始化时把第一个 Agent 加进去
        self._append_trace("Summoner")
        self._save()

    def log_token_usage(self, input_tokens, output_tokens, model="unknown"):
        """记录 Token 消耗并估算价格"""
        # 简单估算：假设 Input $1/1M, Output $2/1M (DeepSeek参考价)
        cost = (input_tokens * 1e-6) + (output_tokens * 2e-6)

        self.data["total_tokens"] += (input_tokens + output_tokens)
        self.data["cost_estimate"] += cost
        self._save()

    def update_state(self, current_agent, action=None, target=None):
        """更新当前 Agent 状态"""
        self.data["current_agent"] = current_agent
        self.data["last_active_time"] = time.time()

        # 【修改点 2】记录有序的踪迹
        # 只有当主角发生变化时，才在时间轴上增加一个新节点
        self._append_trace(current_agent)

        # 格式化日志 (日志部分的代码不变)
        timestamp = time.strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {current_agent}"
        if action:
            log_entry += f": {action}"
        if target:
            log_entry += f" -> {target}"

        self.data["logs"].append(log_entry)
        if len(self.data["logs"]) > 50:
            self.data["logs"] = self.data["logs"][-50:]

        self._save()

    # 【修改点 3】新增一个辅助方法
    def _append_trace(self, agent_name):
        trace = self.data["sequence_trace"]
        # 如果列表为空，或者新的 Agent 与列表中最后一个不同，则添加
        if not trace or trace[-1] != agent_name:
            trace.append(agent_name)

    def _save(self):
        """将状态写入 JSON 文件"""
        # 确保 Debug 目录存在
        os.makedirs("Debug", exist_ok=True)
        try:
            # 使用原子写入或直接覆盖
            with open("Debug/run_state.json", "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass  # 忽略极低概率的写入冲突


# 全局单例导出
monitor = SystemMonitor()