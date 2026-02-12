import os
import sys
import json

from langchain_openai import ChatOpenAI

# 尝试导入监控模块
try:
    from Debug.monitor import monitor
except ImportError:
    monitor = None


class LLMClient:
    def __init__(self, provider="openrouter"):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # 修正路径：从 Core/ 回退到根目录找 config
        key_path = os.path.join(base_dir, "..", "config", "keys.json")

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
                temperature=0.2
            )

            # 执行调用
            if tools:
                response = llm.bind_tools(tools).invoke(messages)
            else:
                response = llm.invoke(messages)

            # 【新增】Token 监控埋点
            if monitor and hasattr(response, 'response_metadata'):
                usage = response.response_metadata.get('token_usage', {})
                monitor.log_token_usage(
                    input_tokens=usage.get('prompt_tokens', 0),
                    output_tokens=usage.get('completion_tokens', 0),
                    model=model
                )

            return response

        except Exception as e:
            return f"System Error: LLM 调用失败 - {str(e)}"

    def get_structured_completion(self, model, messages, response_schema):
        """专门用于结构化输出（强制返回 JSON 格式的对象）"""
        try:
            llm = ChatOpenAI(
                model=model,
                openai_api_key=self.api_key,
                openai_api_base=self.base_url,
                temperature=0.0  # 强制为 0，保证提取的稳定性
            )
            
            # 绑定 Pydantic Schema，强制按结构输出
            structured_llm = llm.with_structured_output(response_schema)
            
            response = structured_llm.invoke(messages)
            return response
            
        except Exception as e:
            return f"System Error: 结构化 LLM 调用失败 - {str(e)}"