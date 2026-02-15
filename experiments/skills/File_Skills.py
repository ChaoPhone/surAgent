import ast
import json
import os

from Core.memory import project_context
from .Pruner_Skills import apply_context_pruning


# [PREP] 新增路径解析函数
def _resolve_path(file_path: str) -> str:
    """
    统一的路径解析器。
    当前版本：直接指向 output/
    未来版本：根据线程上下文指向 workspaces/{id}/
    """
    # 1. 路径清洗 (兼容 Windows 的 \ 符号)
    clean_path = file_path.replace("\\", "/")
    if clean_path.startswith("./"):
        clean_path = clean_path[2:]
    clean_path = clean_path.lstrip("/")

    # 剥离可能重复输入的 output 前缀
    parts = clean_path.split('/')
    if parts[0] == "output":
        parts = parts[1:]

    # [未来在这里插入 Sandbox 逻辑]
    base_dir = "output"

    return os.path.join(base_dir, *parts)


def validate_syntax(file_path: str, content: str) -> tuple:
    """
    [内部函数] 强制语法校验
    返回 (error_msg, parsed_tree)
    """
    if file_path.endswith(".py"):
        try:
            tree = ast.parse(content)
            return None, tree
        except SyntaxError as e:
            return f"❌ Python Syntax Error on line {e.lineno}: {e.msg}...", None
        except Exception as e:
            return f"❌ Python Parse Error: {str(e)}", None

    elif file_path.endswith(".json"):
        try:
            json.loads(content)
            return None, None
        except json.JSONDecodeError as e:
            return f"❌ Invalid JSON format: {e.msg}. YOU MUST FIX THIS.", None

    elif file_path.endswith(".html"):
        if "<html" not in content.lower() or "</html>" not in content.lower():
            return "⚠️ Warning: HTML file seems incomplete (missing <html> tags). Please verify.", None
        return None, None

    return None, None


def write_file(file_path: str, content: str, description: str = "Update code"):
    """
    【必须使用此工具来创建或修改文件】将内容写入指定路径的文件中。
    🚨注意：本工具会自动创建所有不存在的文件夹（父目录），你绝不需要请求建目录！

    Args:
        file_path: 文件的相对路径，例如 'snake_game/core.py'
        content: 要写入的完整代码内容。
        description: 对此次写入的简短描述。
    """
    try:
        # =========== 🛡️ 新增：防偷懒拦截器 (Anti-Laziness Guard) ===========
        # 检测常见的 LLM 偷懒占位符
        lazy_markers = [
            "Content omitted",
            "content omitted",
            "rest of the code",
            "Existing code",
            "..."  # 只有当 ... 独占一行或在注释中时才危险，这里做简单检测
        ]

        # 1. 严格拦截显式的 "Content omitted"
        if "Content omitted" in content or "content omitted" in content:
            return "❌ SYSTEM REJECTION: 检测到偷懒行为！你写入了 '(Content omitted)'。你必须输出完整代码！如果文件太长，请先写骨架，再用 replace_file_lines 填充。"

        # 2. 启发式拦截：如果文件很短却包含大量 ...，可能是偷懒
        # (这里只做简单警告，防止误伤 Python 的 Ellipsis 对象)
        if content.count("...") > 3 and len(content) < 500:
            return "⚠️ WARNING: 检测到过多的 '...'。请确认你没有省略代码逻辑。如果需要分块写入，请使用 replace_file_lines。"
        # =================================================================
        # 2. 使用统一解析器获取目标路径
        target_path = _resolve_path(file_path)

        # 强制阻断散落根目录
        parts = os.path.normpath(target_path).split(os.sep)
        # parts[0] 应该是 'output'，如果总长度小于 3，说明是在 output/ 直接写文件
        if len(parts) < 3:
            return f"❌ REJECTION: 路径错误！你试图将文件 '{file_path}' 直接散落在根目录。必须将其放在项目子文件夹内 (例如: output/snake_game/main.py)。"

        # 3. 安全检查与自动建目录
        if ".." in target_path:
            return "Error: Access to parent directories is restricted."

        parent_dir = os.path.dirname(target_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)

        # 4. 写入磁盘
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # 5. 语法校验与元数据提取
        syntax_error, parsed_tree = validate_syntax(target_path, content)

        if syntax_error:
            status_msg = f"⚠️ WROTE FILE BUT FAILED SYNTAX CHECK:\n{syntax_error}\n\n👉 ACTION REQUIRED: Rewrite the file immediately to fix the syntax!"
            structure_data = {"error": syntax_error}
        else:
            status_msg = f"✅ Success..."
            if target_path.endswith(".py"):
                from .Python_Skills import analyze_code_structure
                structure_data = analyze_code_structure(content, parsed_tree=parsed_tree)
            else:
                # 【核心修复】：为非 Python 文件 (如 txt, json) 赋予初始值，彻底消灭 UnboundLocalError
                structure_data = "Success (Non-Python file)"

        # 6. 更新黑板 (使用相对于 output 的路径作为标识)
        clean_relative_path = "/".join(os.path.normpath(target_path).split(os.sep)[1:])
        project_context.register_file(clean_relative_path, description, structure_data)

        return status_msg

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
    target_path = _resolve_path(file_path)
    print(f"DEBUG: read_file called for {file_path} (resolved: {target_path}) with focus_question='{focus_question}'")
    if not os.path.exists(target_path):
        return f"Error: File {target_path} not found."
    try:
        with open(target_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 如果提供了关注点，且内容较长，则进行裁剪
        if focus_question and len(content) > 2000: # 只要超过 2000 字符就尝试裁剪，提高精准度
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
        file_path: 文件路径 (如 snake_game/main.py)
        start_line: 起始行号 (从 1 开始)
        end_line: 结束行号 (包含该行)
        new_content: 新的代码片段
    """
    try:
        # [PREP] 使用统一解析器
        target_path = _resolve_path(file_path)

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
        new_lines = new_content.splitlines(keepends=True)
        # 确保最后一行始终带有换行符，防止与后面的内容粘连
        if new_lines and not new_lines[-1].endswith('\n'):
            new_lines[-1] += '\n'

        # 核心切片逻辑
        final_lines = lines[:start_line - 1] + new_lines + lines[end_line:]

        # 5. 写回文件
        with open(target_path, 'w', encoding='utf-8') as f:
            f.writelines(final_lines)

        return f"Success: Lines {start_line}-{end_line} replaced in {target_path}. New file size: {len(final_lines)} lines."

    except Exception as e:
        return f"Error replacing lines: {str(e)}"