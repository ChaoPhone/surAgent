import pygame

def draw_text(surface, text, size, x, y, color=(255, 255, 255)):
    """在屏幕上绘制文本"""
    font = pygame.font.Font(None, size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.midtop = (x, y)
    surface.blit(text_surface, text_rect)

def check_collision(rect1, rect2):
    """检查两个矩形是否碰撞"""
    return rect1.colliderect(rect2)

def get_random_position(width, height, grid_size=10):
    """获取随机位置（网格对齐）"""
    x = (random.randint(0, width // grid_size - 1)) * grid_size
    y = (random.randint(0, height // grid_size - 1)) * grid_size
    return (x, y)