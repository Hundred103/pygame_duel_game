import pygame

class Entity:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    
    def update(self, dt):
        pass
    
    def draw(self, screen):
        pass
    
    def get_position(self):
        return (self.x, self.y)
    
    def set_position(self, x, y):
        self.x = x
        self.y = y
        self.rect.x = int(x)
        self.rect.y = int(y)
    
    def get_center(self):
        return self.rect.center
