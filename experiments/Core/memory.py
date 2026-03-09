import time
import threading


class MissionContext:
    def __init__(self):
        # [PREP] 预先引入锁，为并行做准备
        self._lock = threading.Lock()
        
        # 初始化数据结构
        self._data = {
            "project_manifest": "暂无架构设计",

            # [核心改进 1] 文件注册表：存元数据而非全量代码
            # Format: {"filename": {"desc": "...", "signatures": "..."}}
            "file_registry": {},

            # [核心改进 2] 记忆流：简短的事件日志，防失忆
            # Format: ["[Time] Event description", ...]
            "memory_stream": [],

            "runtime_logs": "暂无运行日志"
        }
        self.allowed_keys = self._data.keys()

    def read(self, key):
        """通用读取接口"""
        with self._lock:
            if key not in self.allowed_keys:
                return f"Error: Key '{key}' is not defined."
            return self._data.get(key, "Empty")

    def write(self, key, value):
        """通用写入接口（主要用于 Manifest 和 Logs）"""
        with self._lock:
            if key not in self.allowed_keys:
                return f"Error: You are not allowed to write to '{key}'."
            self._data[key] = value
            return f"Successfully updated '{key}'."

    def register_file(self, filename, description, structure_data):
        """
        更新文件注册表，接收结构化分析数据。
        """
        with self._lock:
            self._data["file_registry"][filename] = {
                "desc": description,
                "structure": structure_data  # 这里存的是字典，不是字符串了
            }
        self.add_event(f"Updated {filename}: {description}")

    def add_event(self, event_text):
        """[Trae 逻辑] 添加一条记忆"""
        with self._lock:
            timestamp = time.strftime('%H:%M:%S')
            self._data["memory_stream"].append(f"[{timestamp}] {event_text}")
            # 保持记忆流不超过 15 条，防止 Context 溢出
            if len(self._data["memory_stream"]) > 15:
                self._data["memory_stream"] = self._data["memory_stream"][-15:]

    def get_snapshot(self):
        """
        [核心] 生成高压缩比的上下文快照 (Smart Context)。
        包含架构、文件接口状态（红绿灯模式）、记忆流和报错日志。
        """
        snapshot = "=== 📂 PROJECT CONTEXT (State-Aware) ===\n"

        # 1. 架构概览 (Manifest)
        # 只截取前 500 字符，防止架构文档太长挤占 Token
        manifest = self._data.get('project_manifest', '暂无架构设计')
        snapshot += f"\n[Manifest]\n{manifest[:500]}{'...' if len(manifest) > 500 else ''}\n"

        # 2. 文件注册表 & 实现状态 (The "Traffic Light" View)
        snapshot += "\n[File Registry & Implementation Status]\n"

        file_reg = self._data.get("file_registry", {})
        if not file_reg:
            snapshot += "(No files created yet)\n"
        else:
            for fname, meta in file_reg.items():
                desc = meta.get('desc', 'No description')
                # 文件头：game.py (五子棋核心逻辑)
                snapshot += f"--- {fname} ({desc}) ---\n"

                # 获取结构化数据 (可能是 AST 分析的 dict，也可能是普通文件的 str)
                struct = meta.get('structure', {})

                # --- 情况 A: 非 Python 文件或旧数据 (直接显示字符串) ---
                if isinstance(struct, str):
                    # 如果内容太长，简单截断
                    display_str = struct[:200] + "..." if len(struct) > 200 else struct
                    snapshot += f"   {display_str}\n"
                    continue

                # --- 情况 B: 解析出错 (AST 失败) ---
                if "error" in struct:
                    snapshot += f"   ⚠️ Parse Error: {struct['error']}\n"
                    continue

                # --- 情况 C: 结构化数据 (Classes & Functions) ---
                has_content = False

                # C-1. 打印类及其方法
                if struct.get("classes"):
                    has_content = True
                    for cls in struct["classes"]:
                        # 格式: 📦 class Game (🟡 实现一半)
                        snapshot += f"   📦 class {cls['name']} ({cls.get('status', 'Unknown')})\n"

                        # 遍历方法
                        for method in cls.get("methods", []):
                            # 格式:      🔴 未实现 : def check_win(self)
                            snapshot += f"      {method['status']} : {method['signature']}\n"

                # C-2. 打印独立函数
                if struct.get("functions"):
                    has_content = True
                    for func in struct["functions"]:
                        # 格式: ƒ 🟢 已实现 : def main()
                        snapshot += f"   ƒ {func['status']} : {func['signature']}\n"

                # C-3. 只有变量或导入，没有函数/类
                if not has_content:
                    snapshot += "   (No classes or top-level functions detected)\n"

                snapshot += "\n"  # 文件间空一行，增加可读性

        # 3. 记忆流 (Memory Stream)
        # 只保留最近 10 条，防止上下文溢出
        snapshot += "\n[Memory Stream (Last 10 Events)]\n"
        mem_stream = self._data.get("memory_stream", [])
        for event in mem_stream[-10:]:
            snapshot += f"{event}\n"

        # 4. 运行日志 (Runtime Logs)
        # 这是 Inspector 报错的主要展示区
        snapshot += f"\n[Runtime Logs]\n{self._data.get('runtime_logs', '暂无日志')}\n"

        return snapshot


# [单例模式] 实例化一个全局共享的 context
# 这样 skills 目录下的文件可以直接 import project_context
project_context = MissionContext()