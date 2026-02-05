# 贪吃蛇游戏

一个使用 Python 和 Pygame 开发的经典贪吃蛇游戏。

## 功能特点

- 经典的贪吃蛇游戏玩法
- 蛇可以吃到食物并增长
- 简单的游戏界面
- 可调节的游戏速度

## 安装要求

- Python 3.x
- Pygame 库

## 安装步骤

1. 克隆或下载项目
2. 安装依赖：
   ```
   pip install -r requirements.txt
   ```
3. 运行游戏：
   ```
   python src/main.py
   ```

## 游戏控制

- 使用键盘方向键控制蛇的移动方向
- 按 ESC 键退出游戏

## 项目结构

```
snake_game/
├── src/
│   ├── main.py          # 主程序入口
│   ├── game.py          # 游戏逻辑
│   ├── snake.py         # 蛇的类
│   ├── food.py          # 食物的类
│   └── utils.py         # 工具函数
├── assets/              # 资源文件
├── tests/               # 测试文件
├── requirements.txt     # 项目依赖
└── README.md            # 项目说明
```

## 开发说明

游戏使用面向对象编程设计，主要包含以下类：

1. **Game**: 游戏主循环和逻辑控制
2. **Snake**: 蛇的移动、生长和绘制
3. **Food**: 食物的生成和绘制

## 许可证

MIT License