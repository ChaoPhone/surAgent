# skills/__init__.py

from .Blackboard_Skills import update_blackboard, read_blackboard
from .File_Skills import write_file, read_file, list_directory, replace_file_lines
from .Mission_Skills import dispatch_mission, mark_mission_complete
from .Pruner_Skills import apply_context_pruning
from .Python_Skills import analyze_code_structure, run_python_code
from .Shell_Skills import run_shell_command
from .Web_Skills import web_search

# 导出技能字典，供 Core.engine 主动拉取
EXPORTED_SKILLS = {
    # File
    "write_file": write_file,
    "read_file": read_file,
    "list_directory": list_directory,
    "replace_file_lines": replace_file_lines,
    "apply_context_pruning": apply_context_pruning,

    # Shell & Python
    "run_shell_command": run_shell_command,
    "run_python_code": run_python_code,
    "analyze_code_structure": analyze_code_structure,

    # Web
    "web_search": web_search,

    # Blackboard & Mission Signals
    "update_blackboard": update_blackboard,
    "read_blackboard": read_blackboard,
    "dispatch_mission": dispatch_mission,
    "mark_mission_complete": mark_mission_complete
}

