import pygame
from snake import Snake
from food import Food

class Game:
    def __init__(self):
        self.width = 800
        self.height = 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("贪吃蛇游戏")
        self.clock = pygame.time.Clock()
        self.snake = Snake()
        self.food = Food()
        self.running = True
        self.score = 0
        self.game_over = False

    def run(self):
        while self.running:
            self.handle_events()
            if not self.game_over:
                self.update()
            self.draw()
            self.clock.tick(15)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif not self.game_over:
                    # 键盘控制蛇的方向
                    if event.key == pygame.K_UP and self.snake.direction != (0, 10):
                        self.snake.direction = (0, -10)
                    elif event.key == pygame.K_DOWN and self.snake.direction != (0, -10):
                        self.snake.direction = (0, 10)
                    elif event.key == pygame.K_LEFT and self.snake.direction != (10, 0):
                        self.snake.direction = (-10, 0)
                    elif event.key == pygame.K_RIGHT and self.snake.direction != (-10, 0):
                        self.snake.direction = (10, 0)

    def update(self):
        self.snake.move()
        
        # 检查边界碰撞
        if self.snake.check_boundary_collision(self.width, self.height):
            self.game_over = True
            return
            
        # 检查自身碰撞
        if self.snake.check_self_collision():
            self.game_over = True
            return
            
        # 检查食物碰撞
        if self.snake.collide_with_food(self.food):
            self.snake.grow()
            self.food.spawn(self.snake.body)
            self.score += 10

    def draw(self):
        self.screen.fill((0, 0, 0))  # 清屏
        
        # 绘制蛇和食物
        self.snake.draw(self.screen)
        self.food.draw(self.screen)
        
        # 绘制分数
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"分数: {self.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (10, 10))
        
        # 如果游戏结束，显示游戏结束文字
        if self.game_over:
            game_over_font = pygame.font.Font(None, 72)
            game_over_text = game_over_font.render("游戏结束!", True, (255, 0, 0))
            text_rect = game_over_text.get_rect(center=(self.width//2, self.height//2))
            self.screen.blit(game_over_text, text_rect)
            
            restart_font = pygame.font.Font(None, 36)
            restart_text = restart_font.render("按 ESC 退出游戏", True, (255, 255, 255))
            restart_rect = restart_text.get_rect(center=(self.width//2, self.height//2 + 50))
            self.screen.blit(restart_text, restart_rect)
        
        pygame.display.flip()