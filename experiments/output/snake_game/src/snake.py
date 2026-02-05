import pygame
import random

class Snake:
    def __init__(self):
        self.body = [(100, 100), (90, 100), (80, 100)]  # 蛇身坐标
        self.direction = (10, 0)  # 初始方向
        self.grow_next_move = False

    def move(self):
        head_x, head_y = self.body[0]
        new_head = (head_x + self.direction[0], head_y + self.direction[1])
        self.body.insert(0, new_head)
        
        if self.grow_next_move:
            self.grow_next_move = False
        else:
            self.body.pop()  # 移除尾部

    def grow(self):
        self.grow_next_move = True

    def collide_with_food(self, food):
        return self.body[0] == food.position

    def check_boundary_collision(self, width, height):
        """检查是否撞到边界"""
        head_x, head_y = self.body[0]
        return (head_x < 0 or head_x >= width or 
                head_y < 0 or head_y >= height)

    def check_self_collision(self):
        """检查是否撞到自己"""
        head = self.body[0]
        return head in self.body[1:]

    def draw(self, surface):
        # 绘制蛇头（不同颜色）
        head_x, head_y = self.body[0]
        pygame.draw.rect(surface, (0, 200, 0), pygame.Rect(head_x, head_y, 10, 10))
        
        # 绘制蛇身
        for segment in self.body[1:]:
            pygame.draw.rect(surface, (0, 255, 0), pygame.Rect(segment[0], segment[1], 10, 10))