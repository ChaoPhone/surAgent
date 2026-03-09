# File: Core/agent.py
import os
from Core.network import LLMClient


class DynamicAgent:
    def __init__(self, name, model, provider, base_prompt_file, bus, is_root=False):
        self.name = name
        self.model = model
        self.provider = provider
        self.is_root = is_root

        # 🔥 依赖注入
        self.client = LLMClient(bus=bus, provider=provider)

        self.base_prompt = self._load_prompt(base_prompt_file)

    def _load_prompt(self, filename):
        if not filename: return ""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, "..", "prompts", filename)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return ""

    def get_full_instructions(self, dynamic_patch: str = None):
        content = self.base_prompt
        if dynamic_patch:
            content += f"\n\n=== 🔴 SYSTEM UPDATE ===\n{dynamic_patch}"
        return content