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


def read_file(file_path: str, focus_question: str = None):
    """
    读取文件内容。
    Args:
        file_path: 相对路径
        focus_question: [可选] 如果文件很大，请提供你关注的具体问题（如“它是如何处理碰撞的？”）。
                        系统将利用语义裁剪技术，只为你保留相关的代码行，从而节省 Token。
    """
    print(f"DEBUG: read_file called for {file_path} with focus_question='{focus_question}'")
    if not os.path.exists(file_path):
        return f"Error: File {file_path} not found."
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 如果提供了关注点，且内容较长，则进行裁剪
        if focus_question and len(content) > 1200: # 只要超过 1200 字符就尝试裁剪，提高精准度
            return apply_context_pruning(content, focus_question)
        
        # 【强化拦截】强制要求 Agent 必须思考“我要读什么”
        if not focus_question and len(content) > 2000:
            msg = (
                f"⚠️ 拦截警告：文件 {file_path} 内容较多（约 {len(content)} 字符）。\n"
                f"为了避免过多的无关信息干扰你的判断并节省 Token 成本，系统禁止全量读取。\n"
                f"请重新调用 read_file，并在 focus_question 参数中明确说明你当前想要寻找的逻辑或变量名。\n"
                f"例如：'我想查看 Snake 类的构造函数' 或 '查找处理食物碰撞的逻辑'。"
            )
            print(f"DEBUG: Triggered INTERCEPTION for {file_path}")
            return msg

        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"


def apply_context_pruning(content: str, query: str):
    """
    [SWE-Pruner 核心逻辑]
    利用轻量级 LLM 模拟论文中的 Neural Skimmer 进行行级裁剪。
    """
    from llm_connection import LLMClient
    from langchain_core.messages import SystemMessage, HumanMessage
    
    # 1. 准备轻量级客户端 (建议使用最便宜的模型)
    client = LLMClient(provider="openrouter") # 或者你默认的 provider
    
    # 2. 构建裁剪指令
    lines = content.splitlines()
    indexed_content = "\n".join([f"{i+1}: {line}" for i, line in enumerate(lines)])
    
    prune_prompt = f"""
你是一个代码分析专家。你的任务是从下面的代码中提取与用户问题最相关的行号。

【用户问题】：{query}

【代码内容】：
{indexed_content}

【要求】：
1. 只输出相关的行号，用逗号分隔，如：1,2,3,10,11,12
2. 如果某一部分代码（如整个函数）都相关，请列出该函数的所有行号。
3. 不要输出任何文字解释，只输出数字和逗号。
"""
    
    try:
        response = client.get_completion(
            model="gpt-4o-mini", # 强制使用小模型以保证速度和成本
            messages=[HumanMessage(content=prune_prompt)]
        )
        
        # 3. 解析返回的行号
        target_line_nums = []
        import re
        nums = re.findall(r'\d+', response.content)
        target_line_nums = [int(n) for n in nums]
        
        if not target_line_nums:
            return content[:1000] + "\n... (裁剪失败，返回前 1000 字符) ..."

        # 4. 扩充上下文 (保留关键行及其前后各 2 行，避免逻辑断层)
        final_indices = set()
        for n in target_line_nums:
            for i in range(max(1, n-2), min(len(lines), n+2) + 1):
                final_indices.add(i-1)
        
        # 5. 组装结果
        sorted_indices = sorted(list(final_indices))
        pruned_lines = []
        last_idx = -1
        for idx in sorted_indices:
            if last_idx != -1 and idx > last_idx + 1:
                pruned_lines.append(f"\n... [已省略 {idx - last_idx - 1} 行] ...\n")
            pruned_lines.append(f"{idx+1}: {lines[idx]}")
            last_idx = idx
            
        return "\n".join(pruned_lines)

    except Exception as e:
        return f"Error during pruning: {str(e)}\n\nOriginal Content (Partial):\n{content[:1000]}"


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