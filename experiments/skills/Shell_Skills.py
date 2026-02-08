import subprocess
import platform


def run_shell_command(command: str):
    """
    执行 Shell 命令行指令。
    Args:
        command: 具体的命令，如 "pip install flask" 或 "python --version"
    """
    # 安全拦截：禁止高危命令
    forbidden = ["rm -rf", "format", "mkfs", ":(){:|:&};:"]
    if any(bad in command for bad in forbidden):
        return "Error: Command blocked by safety policy."

    try:
        # 设置超时时间防止卡死，捕获标准输出和错误
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30  # 30秒超时
        )

        output = f"STDOUT:\n{result.stdout}\n"
        if result.stderr:
            output += f"\nSTDERR:\n{result.stderr}"

        if result.returncode != 0:
            output += f"\n[Process exited with code {result.returncode}]"

        return output.strip()
    except subprocess.TimeoutExpired:
        return "Error: Command timed out (30s limit)."
    except Exception as e:
        return f"Error executing command: {str(e)}"