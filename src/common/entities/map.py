import pygame
import random
import math
from src.common.entities.tile import Tile
from src.config.settings import TILE_SIZE, MAP_1, MIN_SPAWN_DISTANCE_FROM_WALLS, MIN_SPAWN_DISTANCE_FROM_ENEMY

class Map:
    def __init__(self, map_data=None):
        self.tiles = []
        self.walls = []
        self.spawn_points = {}
        self.map_data = map_data if map_data is not None else MAP_1
        self.width = len(self.map_data[0]) if self.map_data else 0
        self.height = len(self.map_data) if self.map_data else 0
        
        for row_idx, row in enumerate(self.map_data):
            for col_idx, cell in enumerate(row):
                x = col_idx * TILE_SIZE
                y = row_idx * TILE_SIZE
                
                if cell == 'P':
                    self.spawn_points[0] = (x, y)
                    cell = '.'
                elif cell == 'O':
                    self.spawn_points[1] = (x, y)
                    cell = '.'
                
                tile = Tile(x, y, cell)
                self.tiles.append(tile)
                
                if cell in ['W', 'B']:
                    self.walls.append(tile)
    
    def draw(self, screen):
        for tile in self.tiles:
            tile.draw(screen)
    
    def get_spawn_position(self, player_number=0):
        if player_number in self.spawn_points:
            return self.spawn_points[player_number]
        else:
            return (TILE_SIZE * 3, TILE_SIZE * 3)
    
    def find_safe_spawn_position(self, enemy_player=None, max_attempts=100):
        for _ in range(max_attempts):
            tile_x = random.randint(MIN_SPAWN_DISTANCE_FROM_WALLS, 
                                  self.width - MIN_SPAWN_DISTANCE_FROM_WALLS - 1)
            tile_y = random.randint(MIN_SPAWN_DISTANCE_FROM_WALLS, 
                                  self.height - MIN_SPAWN_DISTANCE_FROM_WALLS - 1)
            
            x = tile_x * TILE_SIZE
            y = tile_y * TILE_SIZE
            
            if self.is_safe_spawn_position(x, y, enemy_player):
                return (x, y)
        
        return (TILE_SIZE * 5, TILE_SIZE * 5)
    
    def is_safe_spawn_position(self, x, y, enemy_player=None):
        tile_x = x // TILE_SIZE
        tile_y = y // TILE_SIZE
        
        for wall_x in range(max(0, tile_x - MIN_SPAWN_DISTANCE_FROM_WALLS),
                           min(self.width, tile_x + MIN_SPAWN_DISTANCE_FROM_WALLS + 1)):
            for wall_y in range(max(0, tile_y - MIN_SPAWN_DISTANCE_FROM_WALLS),
                               min(self.height, tile_y + MIN_SPAWN_DISTANCE_FROM_WALLS + 1)):
                if wall_y < len(self.map_data) and wall_x < len(self.map_data[wall_y]):
                    if self.map_data[wall_y][wall_x] in ['W', 'B']:
                        return False
        
        if enemy_player and enemy_player.is_alive:
            enemy_tile_x = enemy_player.rect.centerx // TILE_SIZE
            enemy_tile_y = enemy_player.rect.centery // TILE_SIZE
            
            distance = math.sqrt((tile_x - enemy_tile_x) ** 2 + (tile_y - enemy_tile_y) ** 2)
            if distance < MIN_SPAWN_DISTANCE_FROM_ENEMY:
                return False
        
        if tile_y < len(self.map_data) and tile_x < len(self.map_data[tile_y]):
            if self.map_data[tile_y][tile_x] in ['W', 'B']:
                return False
        
        return True
