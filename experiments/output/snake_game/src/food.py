import pygame
import random

class Food:
    def __init__(self):
        self.position = self.generate_position()

    def generate_position(self):
        """生成食物位置"""
        return (random.randint(0, 79) * 10, random.randint(0, 59) * 10)

    def spawn(self, snake_body=None):
        """重新生成食物位置，确保不在蛇身上"""
        if snake_body is None:
            snake_body = []
            
        while True:
            new_position = self.generate_position()
            if new_position not in snake_body:
                self.position = new_position
                break

    def draw(self, surface):
        pygame.draw.rect(surface, (255, 0, 0), pygame.Rect(self.position[0], self.position[1], 10, 10))