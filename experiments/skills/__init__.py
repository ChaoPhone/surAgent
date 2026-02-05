# skills/__init__.py

from .File_Skills import write_file, read_file, list_directory, replace_file_lines
from .Shell_Skills import run_shell_command
from .Web_Skills import web_search
from .Python_Skills import run_python_code

# 1. 全局技能注册表 (用于 config json 中通过字符串引用)
SKILL_REGISTRY = {
    "write_file": write_file,
    "read_file": read_file,
    "list_directory": list_directory,
    "replace_file_lines": replace_file_lines,
    "run_shell_command": run_shell_command,
    "web_search": web_search,
    "run_python_code": run_python_code
}

# 2. 角色默认技能包 (ROLE_SKILLS)
# 这里必须与 agents_config.json 中的 "name" 对应
ROLE_SKILLS = {
    # 架构师：需要看目录、读文件、写设计图
    "Architect": [list_directory, read_file, write_file],

    # 全栈开发：它是超人，需要所有技能 (文件、Shell、Python、联网)
    "Developer": [
        write_file,
        read_file,
        list_directory,
        run_shell_command,
        run_python_code,
        web_search,
        replace_file_lines
    ],

    # 质检员：需要运行代码、读取文件来检查
    "Inspector": [
        read_file,
        run_shell_command,
        run_python_code
    ],

    # 召唤师 (Summoner) 通常不需要这里配置，它在 main.py 里有专属工具
    "Summoner": []
}