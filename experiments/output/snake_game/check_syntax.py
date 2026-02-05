#!/usr/bin/env python3
"""
检查Python代码语法
"""

import sys
import os

def check_file_syntax(filepath):
    """检查单个文件的语法"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        compile(content, filepath, 'exec')
        return True, None
    except SyntaxError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)

def main():
    files_to_check = [
        'src/main.py',
        'src/game.py',
        'src/snake.py',
        'src/food.py',
        'src/utils.py',
        'tests/test_game.py',
        'tests/test_snake.py'
    ]
    
    print("检查Python代码语法...")
    print("=" * 50)
    
    all_good = True
    for filepath in files_to_check:
        if os.path.exists(filepath):
            success, error = check_file_syntax(filepath)
            if success:
                print(f"✅ {filepath}: 语法正确")
            else:
                print(f"❌ {filepath}: {error}")
                all_good = False
        else:
            print(f"⚠️  {filepath}: 文件不存在")
    
    print("=" * 50)
    if all_good:
        print("✅ 所有文件语法检查通过！")
    else:
        print("❌ 部分文件语法检查失败")
    
    return all_good

if __name__ == "__main__":
    sys.exit(0 if main() else 1)