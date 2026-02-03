import os
import json
from llm_connection import LLMClient


class DynamicAgent:
    def __init__(self, name, model, provider, base_prompt_file):
        self.name = name
        self.model = model
        self.provider = provider
        self.client = LLMClient(provider=provider)
        self.base_prompt = self._load_prompt(base_prompt_file)
        self.protocol_prompt = self._load_protocol()

        # 运行时状态
        self.current_patch = ""  # 热更新指令

    def _load_prompt(self, filename):
        path = os.path.join(os.path.dirname(__file__), "prompts", filename)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return "You are a helpful assistant."

    def _load_protocol(self):
        path = os.path.join(os.path.dirname(__file__), "config", "AgentLanguage.json")
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # 将协议转换为自然语言 Prompt
        protocol = "\n\n=== 🔴 SYSTEM PROTOCOL (MUST FOLLOW) ===\n"
        protocol += f"1. Max Peer Interaction Turns: {data['communication_protocol']['max_p2p_turns']}\n"
        protocol += "2. Shared Blackboard Keys:\n"
        for k, v in data['blackboard_keys'].items():
            protocol += f"   - {k}: {v}\n"
        return protocol

    def apply_patch(self, patch_text):
        """注入热更新指令"""
        self.current_patch = patch_text

    def get_full_instructions(self):
        """合成最终 Prompt: 基础 + 协议 + 热补丁"""
        final = self.base_prompt + self.protocol_prompt
        if self.current_patch:
            final += f"\n\n=== 🔥 MISSION HOT-PATCH (PRIORITY HIGH) ===\n{self.current_patch}"
        return final