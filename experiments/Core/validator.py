import ast
import json
import re


def strip_json_comments(json_str):
    """
    [增强] 去除 JSON 字符串中的 C 风格注释 (// 或 /* */)
    DeepSeek 写架构设计时经常会在 JSON 里写注释，导致解析失败。
    """
    # 去除 // 注释
    json_str = re.sub(r'//.*', '', json_str)
    # 去除 /* */ 注释
    json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
    return json_str


def check_code_blocks(content: str) -> str:
    """
    扫描文本中的代码块，并进行语法检查。
    """
    # 匹配 Markdown 代码块
    code_blocks = re.findall(r'```(\w+)\n(.*?)```', content, re.DOTALL)

    if not code_blocks:
        return None

    errors = []

    for lang, code in code_blocks:
        lang = lang.strip().lower()

        # --- Python 校验 ---
        if lang == 'python':
            try:
                ast.parse(code)
            except SyntaxError as e:
                errors.append(f"🐍 Python Syntax Error (Line {e.lineno}): {e.msg}")
            except Exception as e:
                errors.append(f"🐍 Python Error: {str(e)}")

        # --- JSON 校验 (Architect 高频使用) ---
        elif lang in ['json', 'jsonc']:  # 支持 jsonc (带注释的 json)
            try:
                # 尝试直接解析
                json.loads(code)
            except json.JSONDecodeError:
                try:
                    # 失败则尝试去注释后解析
                    clean_code = strip_json_comments(code)
                    json.loads(clean_code)
                except json.JSONDecodeError as e:
                    errors.append(f"📋 JSON Syntax Error: {e.msg} (Check quotes, commas, or brackets)")

        # --- HTML 校验 ---
        elif lang in ['html', 'xml']:
            pass

    if errors:
        return "🛑 [AUTO-INTERCEPT] Syntax Check Failed:\n" + "\n".join(errors)

    return None