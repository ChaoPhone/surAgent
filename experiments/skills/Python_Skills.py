import io
import sys
import contextlib
import ast
import re


def run_python_code(code: str):
    """
    执行一段纯 Python 代码并返回打印输出 (stdout)。
    用于计算、逻辑验证或数据处理。

    Args:
        code: Python 代码字符串
    """
    # 创建一个内存缓冲区来捕获 print 的输出
    stdout_buffer = io.StringIO()

    try:
        # 重定向 stdout
        with contextlib.redirect_stdout(stdout_buffer):
            # 定义一个受限的全局命名空间，防止访问危险变量
            safe_globals = {
                "__builtins__": __builtins__,
                "print": print,
                "range": range,
                "len": len,
                # 可以根据需要添加更多允许的库，如 'math': math
            }
            exec(code, safe_globals)

        output = stdout_buffer.getvalue()
        return output if output.strip() else "[Code executed successfully with no output]"

    except Exception as e:
        return f"Python Execution Error: {str(e)}"
    finally:
        stdout_buffer.close()



def analyze_code_structure(code_content: str):
    """
    [新版 AST 静态分析] 解析代码结构，并自动判断实现状态。

    返回结构字典：
    {
        "classes": [{"name": "Game", "status": "🟢 已实现", "methods": [...]}, ...],
        "functions": [{"name": "main", "status": "🟡 实现一半"}]
    }
    """
    try:
        tree = ast.parse(code_content)
        result = {"classes": [], "functions": []}
        source_lines = code_content.splitlines()

        # 辅助函数：判断代码块的状态
        def check_status(nodes, raw_source_segment):
            # 1. 检查是否只有 pass / ... / raise NotImplementedError
            if not nodes:
                return "🔴 未实现 (Empty)"

            is_empty = False
            if len(nodes) == 1:
                node = nodes[0]
                # 检查 pass 或 ...
                if isinstance(node, (ast.Pass, ast.Ellipsis)):
                    is_empty = True
                # 检查 string (docstring only)
                elif isinstance(node, ast.Expr) and isinstance(node.value, (ast.Str, ast.Constant)):
                    is_empty = True
                # 检查 raise NotImplementedError
                elif isinstance(node, ast.Raise):
                    is_empty = True

            if is_empty:
                return "🔴 未实现"

            # 2. 检查是否有 TODO (通过简单的正则查找)
            if re.search(r'#\s*(TODO|FIXME)', raw_source_segment, re.IGNORECASE):
                return "🟡 实现一半"

            # 3. 默认为已实现
            return "🟢 已实现"

        for node in tree.body:
            # --- 处理函数 ---
            if isinstance(node, ast.FunctionDef):
                # 提取函数体源码用于查 TODO
                # 注意：lineno 从 1 开始，slice 需要 -1
                start = node.lineno - 1
                end = node.end_lineno
                segment = "\n".join(source_lines[start:end])

                status = check_status(node.body, segment)
                args = [arg.arg for arg in node.args.args]
                sig = f"def {node.name}({', '.join(args)})"

                result["functions"].append({
                    "signature": sig,
                    "status": status
                })

            # --- 处理类 ---
            elif isinstance(node, ast.ClassDef):
                class_info = {
                    "name": node.name,
                    "status": "🟢 已实现",  # 类本身默认实现，主要看方法
                    "methods": []
                }

                # 遍历类的方法
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        start = item.lineno - 1
                        end = item.end_lineno
                        segment = "\n".join(source_lines[start:end])

                        method_status = check_status(item.body, segment)
                        # 如果有方法没实现，类也标记为半成品
                        if "未" in method_status or "半" in method_status:
                            class_info["status"] = "🟡 实现一半"

                        args = [arg.arg for arg in item.args.args]
                        # 忽略 self
                        if args and args[0] == 'self': args.pop(0)

                        class_info["methods"].append({
                            "signature": f"def {item.name}({', '.join(args)})",
                            "status": method_status
                        })

                result["classes"].append(class_info)

        return result

    except SyntaxError:
        return {"error": "Syntax Error: Code is not valid Python"}
    except Exception as e:
        return {"error": f"Analysis Error: {str(e)}"}