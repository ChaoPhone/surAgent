import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from game import Game

def test_game_initialization():
    """测试游戏初始化"""
    game = Game()
    assert game.width == 800
    assert game.height == 600
    assert game.running == True

def test_game_components():
    """测试游戏组件"""
    game = Game()
    assert game.snake is not None
    assert game.food is not None
    assert game.clock is not None