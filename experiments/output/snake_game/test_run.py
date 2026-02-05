#!/usr/bin/env python3
"""
贪吃蛇游戏测试脚本
用于验证代码是否能正常运行
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """测试所有模块是否能正确导入"""
    print("测试模块导入...")
    try:
        import pygame
        from game import Game
        from snake import Snake
        from food import Food
        print("✅ 所有模块导入成功")
        return True
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_classes():
    """测试类是否能正确实例化"""
    print("\n测试类实例化...")
    try:
        snake = Snake()
        food = Food()
        print("✅ Snake 和 Food 类实例化成功")
        
        # 测试游戏类（不创建窗口）
        import pygame
        pygame.init()
        game = Game()
        print("✅ Game 类实例化成功")
        pygame.quit()
        return True
    except Exception as e:
        print(f"❌ 类实例化失败: {e}")
        return False

def test_snake_methods():
    """测试蛇类的方法"""
    print("\n测试蛇类方法...")
    try:
        snake = Snake()
        
        # 测试移动
        initial_head = snake.body[0]
        snake.move()
        new_head = snake.body[0]
        print(f"✅ 蛇移动: {initial_head} -> {new_head}")
        
        # 测试生长
        initial_length = len(snake.body)
        snake.grow()
        snake.move()  # 需要移动一次才能生长
        new_length = len(snake.body)
        print(f"✅ 蛇生长: {initial_length} -> {new_length}")
        
        # 测试边界碰撞
        collision = snake.check_boundary_collision(800, 600)
        print(f"✅ 边界碰撞检测: {collision}")
        
        # 测试自身碰撞
        self_collision = snake.check_self_collision()
        print(f"✅ 自身碰撞检测: {self_collision}")
        
        return True
    except Exception as e:
        print(f"❌ 蛇类方法测试失败: {e}")
        return False

def test_food_methods():
    """测试食物类的方法"""
    print("\n测试食物类方法...")
    try:
        food = Food()
        print(f"✅ 食物位置: {food.position}")
        
        # 测试重新生成
        food.spawn()
        print(f"✅ 食物重新生成: {food.position}")
        
        return True
    except Exception as e:
        print(f"❌ 食物类方法测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("贪吃蛇游戏代码测试")
    print("=" * 50)
    
    tests_passed = 0
    tests_total = 4
    
    if test_imports():
        tests_passed += 1
    
    if test_classes():
        tests_passed += 1
    
    if test_snake_methods():
        tests_passed += 1
    
    if test_food_methods():
        tests_passed += 1
    
    print("\n" + "=" * 50)
    print(f"测试结果: {tests_passed}/{tests_total} 通过")
    
    if tests_passed == tests_total:
        print("✅ 所有测试通过！代码应该可以正常运行。")
        print("\n运行游戏:")
        print("cd output/snake_game")
        print("python src/main.py")
    else:
        print("❌ 部分测试失败，请检查代码。")
    
    return tests_passed == tests_total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)