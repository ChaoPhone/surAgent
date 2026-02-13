# File: Core/network.py
import os
import sys
import json
from langchain_openai import ChatOpenAI
from Core.bus import EventType


class LLMClient:
    def __init__(self, bus, provider="openrouter"):
        self.bus = bus  # 强依赖总线

        base_dir = os.path.dirname(os.path.abspath(__file__))
        key_path = os.path.join(base_dir, "..", "config", "keys.json")
        try:
            with open(key_path, 'r', encoding='utf-8') as f:
                keys_config = json.load(f)
            config = keys_config.get(provider)
            self.api_key = config["api_key"]
            self.base_url = config["base_url"]
        except Exception:
            self.api_key = "ERROR"
            self.base_url = ""

    def get_completion(self, model, messages, tools=None, temperature=None):
        target_temp = temperature if temperature is not None else 0.2
        llm = ChatOpenAI(model=model, api_key=self.api_key, base_url=self.base_url, temperature=target_temp)

        if tools:
            response = llm.bind_tools(tools).invoke(messages)
        else:
            response = llm.invoke(messages)

        # 🔥 发布 Token 事件
        usage = {}
        if hasattr(response, 'response_metadata'):
            usage = response.response_metadata.get('token_usage', {}) or response.response_metadata.get(
                'usage_metadata', {})

        self.bus.publish(EventType.TOKEN_USAGE, {
            "model": model,
            "input": usage.get('prompt_tokens', 0),
            "output": usage.get('completion_tokens', 0)
        })

        return response