import random

class SnakeGame:
    def __init__(self, grid_size=20, width=400, height=400):
        self.grid_size = grid_size
        self.width = width
        self.height = height
        self.reset_game()
    
    def reset_game(self):
        self.snake = [(100, 100), (90, 100), (80, 100)]  # 蛇的初始位置
        self.direction = "RIGHT"
        self.food = self.generate_food()
        self.game_over = False
        self.score = 0
    
    def move(self, direction):
        if self.game_over:
            return False
            
        # 防止直接反向移动
        if (direction == "LEFT" and self.direction == "RIGHT") or \
           (direction == "RIGHT" and self.direction == "LEFT") or \
           (direction == "UP" and self.direction == "DOWN") or \
           (direction == "DOWN" and self.direction == "UP"):
            direction = self.direction
            
        self.direction = direction
        
        # 计算新的头部位置
        head_x, head_y = self.snake[0]
        if direction == "LEFT":
            head_x -= self.grid_size
        elif direction == "RIGHT":
            head_x += self.grid_size
        elif direction == "UP":
            head_y -= self.grid_size
        elif direction == "DOWN":
            head_y += self.grid_size
        
        # 检查边界碰撞
        if head_x < 0 or head_x >= self.width or head_y < 0 or head_y >= self.height:
            self.game_over = True
            return False
        
        # 检查自身碰撞
        new_head = (head_x, head_y)
        if new_head in self.snake:
            self.game_over = True
            return False
        
        # 移动蛇
        self.snake.insert(0, new_head)
        
        # 检查是否吃到食物
        if new_head == self.food:
            self.score += 10
            self.food = self.generate_food()
        else:
            self.snake.pop()
        
        return True
    
    def check_collision(self):
        head_x, head_y = self.snake[0]
        
        # 边界碰撞
        if head_x < 0 or head_x >= self.width or head_y < 0 or head_y >= self.height:
            return True
        
        # 自身碰撞
        if (head_x, head_y) in self.snake[1:]:
            return True
        
        return False
    
    def generate_food(self):
        while True:
            food_x = random.randint(0, (self.width - self.grid_size) // self.grid_size) * self.grid_size
            food_y = random.randint(0, (self.height - self.grid_size) // self.grid_size) * self.grid_size
            food_pos = (food_x, food_y)
            
            if food_pos not in self.snake:
                return food_pos
    
    def get_snake(self):
        return self.snake
    
    def get_food(self):
        return self.food
    
    def get_score(self):
        return self.score
    
    def is_game_over(self):
        return self.game_over