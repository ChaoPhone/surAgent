# File: Debug/monitor.py
import json
import os
import shutil
import time
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree
from rich.text import Text
from Core.bus import EventType

console = Console()


class UnifiedMonitor:
    def __init__(self, bus):
        # 使用基于文件位置的绝对路径
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_path = os.path.join(base_dir, "run_state.json")
        # os.makedirs("Debug", exist_ok=True) # 不再需要，因为 Debug 目录肯定存在
        # 启动即重置，保证数据纯净
        self.data = self._reset_and_init_data()

        # 订阅全量事件
        bus.subscribe(EventType.TOKEN_USAGE, self._on_token)
        bus.subscribe(EventType.AGENT_THINK, self._on_think)
        bus.subscribe(EventType.AGENT_ACTION, self._on_action)
        bus.subscribe(EventType.AGENT_SWITCH, self._on_switch)
        bus.subscribe(EventType.BLACKBOARD_UPDATE, self._on_bb_update)
        bus.subscribe(EventType.MISSION_COMPLETE, self._on_complete)
        bus.subscribe(EventType.PARALLEL_START, self._on_parallel_start)
        bus.subscribe(EventType.WORKER_FINISH, self._on_worker_finish)

    def _reset_and_init_data(self):
        """初始化数据，备份旧日志"""
        if os.path.exists(self.data_path):
            try:
                backup_path = self.data_path + ".bak"
                shutil.copy(self.data_path, backup_path)
            except Exception as e:
                console.print(f"[red]⚠️ 备份失败: {e}[/red]")

        return {
            "current_agent": "System",
            "system_start_time": time.time(),
            "last_active_time": time.time(),
            "turn_count": 0,
            "logs": [],
            "blackboard": {},
            "sequence_trace": [],
            "parallel_history": [],
            "token_total": 0,
            "agent_stats": {},  # Input/Output 分离统计
            "agent_profiles": {}  # 档案柜
        }

    def _save(self):
        try:
            with open(self.data_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except:
            pass

    def _update_agent_stat(self, agent_name, input_delta=0, output_delta=0):
        """更新 Agent 的详细统计"""
        stats = self.data["agent_stats"]
        if agent_name not in stats:
            stats[agent_name] = {
                "tokens": 0,
                "input": 0,
                "output": 0,
                "calls": 0,
                "first_seen": time.time(),
                "last_seen": time.time(),
                "status": "idle"
            }

        entry = stats[agent_name]
        entry["tokens"] += (input_delta + output_delta)
        entry["input"] += input_delta
        entry["output"] += output_delta
        entry["last_seen"] = time.time()
        self.data["agent_stats"] = stats

    # === 事件回调 ===

    def _on_token(self, data):
        input_t = data.get('input', 0)
        output_t = data.get('output', 0)
        total = input_t + output_t

        self.data['token_total'] += total

        # 归属给当前 Agent
        current = self.data.get("current_agent", "System")
        self._update_agent_stat(current, input_delta=input_t, output_delta=output_t)

        self._save()
        # 🔥 静默命令行输出：不再在终端打印 Token 消耗
        # console.print(f"[dim]  ∟ Token ({current}): +{total} | Total: {self.data['token_total']}[/dim]")

    def _on_think(self, data):
        agent = data["agent"]
        self.data["current_agent"] = agent
        self.data["last_active_time"] = time.time()
        self.data["turn_count"] += 1

        self._update_agent_stat(agent)
        self.data["agent_stats"][agent]["calls"] += 1
        self.data["agent_stats"][agent]["status"] = "thinking"

        self._save()
        console.print(Panel(Text(f"🤔 {agent} Thinking...", style="bold magenta"), border_style="magenta"))

    def _on_switch(self, data):
        target = data["to"]
        prev = data.get("from", "?")
        self.data["current_agent"] = target

        trace = self.data["sequence_trace"]
        if not trace or trace[-1] != target:
            trace.append(target)

        self._save()
        console.print(f"\n[bold cyan]🔄 Switch:[/bold cyan] {prev} ➔ {target}")

    def _on_action(self, data):
        entry = {
            "time": time.strftime('%H:%M:%S'),
            "agent": data['agent'],
            "action": data['action'],
            "type": "info"
        }
        self.data["logs"].append(entry)
        if len(self.data["logs"]) > 200: self.data["logs"].pop(0)
        self._save()
        # 🔥 静默命令行输出：不再在终端打印 "正在执行工具..."
        # console.print(f"[green]🔧 {data['agent']}[/green]: {data['action']}")

    def _on_bb_update(self, data):
        key = data.get("key") or list(data.keys())[0]
        content = data.get("content") or list(data.values())[0]
        self.data["blackboard"][key] = content
        self._save()
        console.print(f"[dim cyan]📋 Blackboard Updated: {key}[/dim cyan]")

    def _on_complete(self, data):
        self.data["logs"].append({
            "time": time.strftime('%H:%M:%S'),
            "agent": "System",
            "action": f"MISSION COMPLETE: {data.get('result')}",
            "type": "success"
        })
        self._save()
        console.print(Panel(f"🏁 Mission Complete: {data.get('result')}", style="bold green"))

    def _on_parallel_start(self, data):
        manager = data.get("manager", "System")
        tasks = data.get("tasks", [])

        # 1. 存入并行历史
        snapshot = {
            "timestamp": time.strftime('%H:%M:%S'),
            "manager": manager,
            "tasks": tasks
        }
        self.data["parallel_history"].append(snapshot)

        # 2. 建立档案 (Profile)
        profiles = self.data["agent_profiles"]
        for t in tasks:
            role = t.get('role', 'Worker')
            profiles[role] = {
                "instruction": t.get('instruction', ''),
                "temperature": t.get('temperature', 0.2),
                "model": t.get('model', 'deepseek-chat'),
                "manager": manager
            }
        self.data["agent_profiles"] = profiles

        # 3. 日志
        self.data["logs"].append({
            "time": time.strftime('%H:%M:%S'),
            "agent": manager,
            "action": f"启动并行任务 (Batch: {len(tasks)})",
            "type": "warning"
        })
        self._save()

        # 终端显示
        tree = Tree(f"[bold yellow]🚀 {manager} 启动并行任务[/bold yellow]")
        for t in tasks:
            tree.add(f"🧊 {t.get('role')}")
        console.print(Panel(tree, border_style="yellow"))

    def _on_worker_finish(self, data):
        role = data.get("role", "Worker")
        status = data.get("status", "unknown")

        self._update_agent_stat(role)
        self.data["agent_stats"][role]["status"] = "finished" if status == "success" else "error"

        self.data["logs"].append({
            "time": time.strftime('%H:%M:%S'),
            "agent": role,
            "action": f"子任务结束: {status}",
            "type": "success" if status == "success" else "error"
        })
        self._save()
        color = "green" if status == "success" else "red"
        console.print(f"  └─ [{color}]✅ {role}[/{color}]: {status}")