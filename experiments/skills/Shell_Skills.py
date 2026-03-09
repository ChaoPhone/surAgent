import os
import re
import subprocess


def run_shell_command(command: str, timeout: int = 10):
    """
    执行 Shell 命令。采用严格的白名单策略与防卡死机制。
    """
    print(f"⚡️ Running: {command} (Timeout: {timeout}s)...")

    # 1. 严格白名单策略 (Whitelist Policy)
    # 仅允许执行的基础命令列表（根据你的项目需求，可自行添加 npm, node, pytest 等）
    ALLOWED_COMMANDS = {"python", "python3", "pip", "ls", "cd", "dir", "cat", "echo","pytest"}

    # 绝对禁止的重定向操作 (严格贯彻 Developer Prompt 要求)
    if ">" in command or ">>" in command:
        return "Error: Redirection (>, >>) is strictly forbidden. Use 'write_file' tool to modify files."

    # 解析可能被 &&, ;, | 连接的多条命令
    # 例如：cd output/snake_game && python main.py
    sub_commands = re.split(r'&&|;|\|', command)
    for sub_cmd in sub_commands:
        parts = sub_cmd.strip().split()
        if not parts:
            continue

        base_cmd = parts[0]  # 提取基础命令
        if base_cmd not in ALLOWED_COMMANDS:
            return (f"Error: Command '{base_cmd}' blocked by security policy. "
                    f"Allowed commands are: {', '.join(ALLOWED_COMMANDS)}.")

    # 2. 自动注入 PYTHONPATH
    env = os.environ.copy()
    project_roots = []
    
    # 获取绝对路径的 output 目录
    skills_dir = os.path.dirname(os.path.abspath(__file__))
    experiments_dir = os.path.dirname(skills_dir)
    output_dir = os.path.join(experiments_dir, "output")

    if os.path.exists(output_dir):
        for item in os.listdir(output_dir):
            full_path = os.path.abspath(os.path.join(output_dir, item))
            if os.path.isdir(full_path) and not item.startswith("."):
                project_roots.append(full_path)
                src_path = os.path.join(full_path, "src")
                if os.path.exists(src_path):
                    project_roots.append(src_path)

    separator = ";" if os.name == 'nt' else ":"
    additional_path = separator.join(project_roots)
    if additional_path:
        env["PYTHONPATH"] = (env.get("PYTHONPATH", "") + separator + additional_path).strip(separator)

    try:
        # 3. 执行命令 (含防卡死与编码容错)
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            stdin=subprocess.DEVNULL,  # 切断输入流，防止交互式命令卡死
            errors='backslashreplace'  # 编码容错
        )

        output = f"STDOUT:\n{result.stdout}\n"
        if result.stderr:
            output += f"\nSTDERR:\n{result.stderr}"

        if result.returncode != 0:
            output += f"\n[Process exited with code {result.returncode}]"

        return output.strip()

    except subprocess.TimeoutExpired as e:
        captured_out = e.stdout if e.stdout else "(No stdout captured)"
        captured_err = e.stderr if e.stderr else "(No stderr captured)"
        return (
            f"⚠️ [TIMEOUT] Process ran for {timeout}s and was terminated.\n"
            f"STDOUT: {captured_out}\n"
            f"STDERR: {captured_err}"
        )

    except UnicodeDecodeError as e:
        return f"Execution Error (Encoding): Output could not be decoded. {str(e)}"

    except Exception as e:
        return f"Execution Error: {str(e)}"