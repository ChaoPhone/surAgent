import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from snake import Snake

def test_snake_initialization():
    """测试蛇的初始化"""
    snake = Snake()
    assert len(snake.body) == 3
    assert snake.direction == (10, 0)

def test_snake_move():
    """测试蛇的移动"""
    snake = Snake()
    initial_head = snake.body[0]
    snake.move()
    new_head = snake.body[0]
    assert new_head[0] == initial_head[0] + snake.direction[0]
    assert new_head[1] == initial_head[1] + snake.direction[1]

def test_snake_grow():
    """测试蛇的生长"""
    snake = Snake()
    initial_length = len(snake.body)
    snake.grow()
    assert len(snake.body) == initial_length + 1