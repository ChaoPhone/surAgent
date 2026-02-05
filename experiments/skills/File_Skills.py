import os


def write_file(file_path: str, content: str):
    """
    将内容写入文件。
    【强制约束】所有文件将被强制保存到根目录的 output/ 文件夹中。
    """
    try:
        # 1. 路径清洗：移除开头的 ./ 或 /
        clean_path = file_path.lstrip("./").lstrip("/")

        # 2. 【核心修改】强制添加 output 前缀
        # 如果 Agent 已经很聪明地写了 output/project_x/main.py，我们就不加了
        # 如果 Agent 只写了 main.py，我们就强制变成 output/main.py (或者建议在Prompt里让Agent生成项目名)

        if not clean_path.startswith("output"):
            # 这里的策略是：强制放入 output 目录
            # 注意：为了实现 output/子项目名称/代码，我们需要 Agent 在 file_path 里提供子项目名称
            # 例如 Agent 传入 "wolf_game/app.py"，我们变成 "output/wolf_game/app.py"
            target_path = os.path.join("output", clean_path)
        else:
            target_path = clean_path

        # 3. 安全检查
        if ".." in target_path:
            return "Error: Access to parent directories is restricted."

        # 4. 自动创建父目录
        parent_dir = os.path.dirname(target_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)

        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return f"Success: File written to {target_path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


def read_file(file_path: str):
    """
    读取文件内容。
    Args:
        file_path: 相对路径
    """
    if not os.path.exists(file_path):
        return f"Error: File {file_path} not found."
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"


def list_directory(dir_path: str = "."):
    """
    列出目录下的所有文件结构。
    """
    try:
        tree_str = ""
        for root, dirs, files in os.walk(dir_path):
            # 忽略隐藏目录和 venv
            if ".git" in root or "venv" in root or "__pycache__" in root:
                continue
            level = root.replace(dir_path, '').count(os.sep)
            indent = ' ' * 4 * (level)
            tree_str += f"{indent}{os.path.basename(root)}/\n"
            subindent = ' ' * 4 * (level + 1)
            for f in files:
                tree_str += f"{subindent}{f}\n"
        return tree_str if tree_str else "Directory is empty."
    except Exception as e:
        return f"Error listing directory: {str(e)}"


def replace_file_lines(file_path: str, start_line: int, end_line: int, new_content: str):
    """
    【精准修改】替换文件中指定行号范围的内容。
    Args:
        file_path: 文件路径 (如 output/snake_game/main.py)
        start_line: 起始行号 (从 1 开始)
        end_line: 结束行号 (包含该行)
        new_content: 新的代码片段
    """
    try:
        # 1. 路径清洗
        clean_path = file_path.lstrip("./").lstrip("/")
        if not clean_path.startswith("output"):
            target_path = os.path.join("output", clean_path)
        else:
            target_path = clean_path

        if not os.path.exists(target_path):
            return f"Error: File {target_path} not found."

        # 2. 读取所有行
        with open(target_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 3. 校验行号
        total_lines = len(lines)
        if start_line < 1 or start_line > total_lines:
            return f"Error: Start line {start_line} is out of range (Total: {total_lines})."

        # 修正 end_line，允许 -1 表示到最后
        if end_line == -1 or end_line > total_lines:
            end_line = total_lines

        if start_line > end_line:
            return f"Error: Start line {start_line} is greater than end line {end_line}."

        # 4. 执行替换 (注意 Python 列表是从 0 开始，而行号是从 1 开始)
        # 转换 new_content 为列表，确保末尾有换行
        new_lines = [line + '\n' if not line.endswith('\n') else line for line in new_content.splitlines()]

        # 核心切片逻辑
        final_lines = lines[:start_line - 1] + new_lines + lines[end_line:]

        # 5. 写回文件
        with open(target_path, 'w', encoding='utf-8') as f:
            f.writelines(final_lines)

        return f"Success: Lines {start_line}-{end_line} replaced in {target_path}. New file size: {len(final_lines)} lines."

    except Exception as e:
        return f"Error replacing lines: {str(e)}"