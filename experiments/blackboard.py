import json
import os


class MissionContext:
    def __init__(self):
        self._data = {}
        self._load_schema()

    def _load_schema(self):
        """加载 AgentLanguage.json 定义的允许 Key"""
        # 获取当前文件所在目录
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # 拼接 config 路径
        path = os.path.join(base_dir, "config", "AgentLanguage.json")

        try:
            with open(path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.allowed_keys = config.get("blackboard_keys", {}).keys()

            # 初始化空黑板
            for key in self.allowed_keys:
                self._data[key] = None
        except Exception as e:
            print(f"❌ Error loading blackboard schema: {e}")
            self.allowed_keys = []

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
        """获取当前黑板快照（瘦身版，防止 Token 爆炸）"""
        snapshot = self._data.copy()

        # 强制隐藏代码库的具体内容，只显示 keys (文件名)
        if "code_repository" in snapshot and isinstance(snapshot["code_repository"], dict):
            # 只保留文件名列表，不给 LLM 看具体代码，节省大量 Token
            snapshot["code_repository"] = list(snapshot["code_repository"].keys())

        return json.dumps(snapshot, indent=2, ensure_ascii=False)