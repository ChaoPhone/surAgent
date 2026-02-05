import subprocess
import os
import sys


def run_shell_command(command: str, timeout: int = 10):
    """
    执行 Shell 命令。包含防卡死、自动路径注入和编码容错机制。
    """
    # 1. 安全拦截
    forbidden = ["rm -rf", "format", "mkfs", ":(){:|:&};:"]
    if any(bad in command for bad in forbidden):
        return "Error: Command blocked by safety policy."

    print(f"⚡️ Running: {command} (Timeout: {timeout}s)...")

    # 2. 自动注入 PYTHONPATH (逻辑保持不变，略作优化)
    env = os.environ.copy()
    project_roots = []
    if os.path.exists("output"):
        for item in os.listdir("output"):
            full_path = os.path.abspath(os.path.join("output", item))
            if os.path.isdir(full_path) and not item.startswith("."):  # 忽略 .git 等隐藏目录
                project_roots.append(full_path)
                src_path = os.path.join(full_path, "src")
                if os.path.exists(src_path):
                    project_roots.append(src_path)

    separator = ";" if os.name == 'nt' else ":"
    additional_path = separator.join(project_roots)
    if additional_path:
        env["PYTHONPATH"] = (env.get("PYTHONPATH", "") + separator + additional_path).strip(separator)

    try:
        # 3. 执行命令 (核心修改)
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,  # 自动解码为字符串
            timeout=timeout,  # 强制超时
            env=env,
            # ---【防卡死关键修改】---
            stdin=subprocess.DEVNULL,  # 1. 切断输入流：遇到交互式命令直接报错，而不是挂起等待
            errors='backslashreplace'  # 2. 编码容错：遇到无法解码的字符（如GBK乱码）用转义符替换，防止解码报错卡死
        )

        output = f"STDOUT:\n{result.stdout}\n"
        if result.stderr:
            output += f"\nSTDERR:\n{result.stderr}"

        if result.returncode != 0:
            output += f"\n[Process exited with code {result.returncode}]"

        return output.strip()

    except subprocess.TimeoutExpired as e:
        # 处理超时情况
        captured_out = e.stdout if e.stdout else "(No stdout captured)"
        captured_err = e.stderr if e.stderr else "(No stderr captured)"

        # Windows 特殊处理：如果是 Shell=True，TimeoutExpired 可能杀不掉孙子进程
        # 这里只是做个标记，真正的彻底查杀需要 psutil 库，但为了最小依赖，我们至少返回目前捕获到的信息

        return (
            f"⚠️ [TIMEOUT] Process ran for {timeout}s and was terminated.\n"
            f"STDOUT: {captured_out}\n"
            f"STDERR: {captured_err}"
        )

    except UnicodeDecodeError as e:
        return f"Execution Error (Encoding): Output could not be decoded. {str(e)}"

    except Exception as e:
        return f"Execution Error: {str(e)}"