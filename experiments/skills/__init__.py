# skills/__init__.py

from .File_Skills import write_file, read_file, list_directory, replace_file_lines
from .Shell_Skills import run_shell_command
from .Web_Skills import web_search
from .Python_Skills import analyze_code_structure,run_python_code

# 全局技能注册表 (用于 config json 中通过字符串引用)
SKILL_REGISTRY = {
    "write_file": write_file,
    "read_file": read_file,
    "list_directory": list_directory,
    "replace_file_lines": replace_file_lines,
    "run_shell_command": run_shell_command,
    "web_search": web_search,
    "run_python_code": run_python_code,
    "analyze_code_structure": analyze_code_structure
}

