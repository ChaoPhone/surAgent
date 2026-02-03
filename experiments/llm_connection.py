import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage


class LLMClient:
    def __init__(self, provider="openrouter"):
        """
        根据 provider (deepseek 或 openrouter) 自动加载 keys.json 中的配置
        """
        # 读取 keys.json
        current_dir = os.path.dirname(os.path.abspath(__file__))
        key_file_path = os.path.join(current_dir, "keys.json")

        try:
            with open(key_file_path, 'r', encoding='utf-8') as f:
                keys_config = json.load(f)
        except FileNotFoundError:
            raise Exception("❌ 找不到 keys.json，请先创建并配置 API Key！")

        # 获取对应厂商的配置
        config = keys_config.get(provider)
        if not config:
            raise Exception(f"❌ keys.json 中缺少 '{provider}' 的配置！")

        self.model_name = ""  # 临时占位，具体调用时指定或在外部指定
        self.api_key = config["api_key"]
        self.base_url = config["base_url"]

    def get_completion(self, model, messages, tools=None):
        """
        核心方法：支持工具调用的对话接口
        """
        # 动态初始化 ChatOpenAI，因为不同 Agent 可能用不同模型但同一个 Provider
        llm = ChatOpenAI(
            model=model,
            openai_api_key=self.api_key,
            openai_api_base=self.base_url,
            temperature=0.1  # 蜂群架构建议低温度，保证工具调用准确
        )

        if tools:
            llm_with_tools = llm.bind_tools(tools)
            return llm_with_tools.invoke(messages)
        else:
            return llm.invoke(messages)