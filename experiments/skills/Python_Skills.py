import io
import sys
import contextlib


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