import os
import json

from Core.network import LLMClient


class DynamicAgent:
    def __init__(self, name, model, provider, base_prompt_file, is_root=False):
        self.name = name
        self.model = model
        self.provider = provider
        self.is_root = is_root
        self.client = LLMClient(provider=provider)
        self.base_prompt = self._load_prompt(base_prompt_file)
        self.protocol_prompt = self._load_protocol()

    def _load_prompt(self, filename):
        # 修正路径：从 core/ 回退到根目录找 prompts
        path = os.path.join(os.path.dirname(__file__), "..", "prompts", filename)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return "You are a helpful assistant."

    def _load_protocol(self):
        # 修正路径：从 core/ 回退到根目录找 config
        path = os.path.join(os.path.dirname(__file__), "..", "config", "AgentLanguage.json")
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # 将协议转换为自然语言 Prompt
        protocol = "\n\n=== 🔴 SYSTEM PROTOCOL (MUST FOLLOW) ===\n"
        protocol += f"1. Communication Instruction: {data['communication_protocol']['instruction']}\n"
        protocol += "2. Shared Blackboard Keys:\n"
        for k, v in data['blackboard_keys'].items():
            protocol += f"   - {k}: {v}\n"
        return protocol

    def apply_patch(self, patch_text):
        """[Deprecated] 注入热更新指令。在并行模式下不再安全，请改用参数化传入。"""
        # 为了兼容性暂时保留，但内部不再存储状态
        pass

    def get_full_instructions(self, dynamic_patch: str = None):
        """合成最终 Prompt: 基础 + 协议 + 热补丁"""
        final = self.base_prompt + self.protocol_prompt
        if dynamic_patch:
            final += f"\n\n=== 🔥 MISSION HOT-PATCH (PRIORITY HIGH) ===\n{dynamic_patch}"
        return final