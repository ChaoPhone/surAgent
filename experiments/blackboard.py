import json
import os


class MissionContext:
    def __init__(self):
        self._data = {}
        self._load_schema()

    def _load_schema(self):
        """加载 AgentLanguage.json 定义的允许 Key"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, "config", "AgentLanguage.json")
        with open(path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        self.allowed_keys = config.get("blackboard_keys", {}).keys()

        # 初始化空黑板
        for key in self.allowed_keys:
            self._data[key] = None

    def read(self, key):
        if key not in self.allowed_keys:
            return f"Error: Key '{key}' is not defined in AgentLanguage Protocol."
        return self._data.get(key, "Empty")

    def write(self, key, value):
        if key not in self.allowed_keys:
            return f"Error: You are not allowed to write to '{key}'. Check protocol."
        self._data[key] = value
        return f"Successfully updated '{key}'."

    def get_snapshot(self):
        """获取当前黑板快照（用于调试）"""
        return json.dumps(self._data, indent=2, ensure_ascii=False)