import pygame
from src.common.entities.entity import Entity
from src.common.utils.helpers import load_image
from src.config.settings import TILE_SIZE

class Tile(Entity):
    def __init__(self, x, y, tile_type='.'):
        super().__init__(x, y, TILE_SIZE, TILE_SIZE)
        
        self.tile_type = tile_type
        self.is_solid = False
        self.blocks_player = False
        
        if tile_type == 'W':
            self.image = load_image("Wall_tile.png")
            self.is_solid = True
            self.blocks_player = True
        elif tile_type == 'B':
            self.image = load_image("Blockade_tile.png")
            self.is_solid = False
            self.blocks_player = True
        else:
            self.image = load_image("Floor_tile.png")
            self.is_solid = False
            self.blocks_player = False
    
    def draw(self, screen):
        screen.blit(self.image, (self.rect.x, self.rect.y))
