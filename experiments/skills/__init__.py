# skills/__init__.py

from .File_Skills import write_file, read_file, list_directory
from .Shell_Skills import run_shell_command
from .Web_Skills import web_search
from .Python_Skills import run_python_code

# 定义一个注册表，方便通过字符串名字查找函数
SKILL_REGISTRY = {
    # 文件类
    "write_file": write_file,
    "read_file": read_file,
    "list_directory": list_directory,

    # 终端类
    "run_shell_command": run_shell_command,

    # 网络类
    "web_search": web_search,

    # 代码类
    "run_python_code": run_python_code
}

# 也可以根据角色打包工具集
ROLE_SKILLS = {
    "Kernel": [write_file, read_file, run_shell_command, run_python_code],
    "Surface": [write_file, read_file],  # 前端通常不需要跑 shell
    "Structure": [list_directory, read_file],
    "Audit": [read_file, run_shell_command]  # 审计需要运行代码检查
}