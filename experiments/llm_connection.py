import os
import json
import sys
from langchain_openai import ChatOpenAI


class LLMClient:
    def __init__(self, provider="openrouter"):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        key_path = os.path.join(base_dir, "config", "keys.json")

        try:
            with open(key_path, 'r', encoding='utf-8') as f:
                keys_config = json.load(f)
        except FileNotFoundError:
            print(f"❌ 错误：找不到 {key_path}")
            sys.exit(1)

        config = keys_config.get(provider)
        if not config:
            raise ValueError(f"keys.json 中缺少 provider: {provider}")

        self.api_key = config["api_key"]
        self.base_url = config["base_url"]

    def get_completion(self, model, messages, tools=None):
        """支持工具调用的统一接口"""
        try:
            llm = ChatOpenAI(
                model=model,
                openai_api_key=self.api_key,
                openai_api_base=self.base_url,
                temperature=0.1  # 极低温度，确保工具调用准确
            )
            if tools:
                return llm.bind_tools(tools).invoke(messages)
            return llm.invoke(messages)
        except Exception as e:
            return f"System Error: LLM 调用失败 - {str(e)}"