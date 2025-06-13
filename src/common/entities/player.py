import pygame
import math
from src.common.entities.entity import Entity
from src.common.entities.projectile import Projectile
from src.common.utils.helpers import load_image, get_direction_from_angle
from src.config.settings import PLAYER_SPEED, FIRE_COOLDOWN, PLAYER_HEALTH, TILE_SIZE, RESPAWN_DELAY

class Player(Entity):
    def __init__(self, x, y, player_image="player1.png", player_id=0):
        super().__init__(x, y, 48, 48)
        
        self.player_id = player_id
        
        self.spawn_x = x
        self.spawn_y = y
        
        self.original_image = load_image(player_image)
        self.image = self.original_image.copy()
        
        self.angle = 0
        self.speed = PLAYER_SPEED
        self.health = PLAYER_HEALTH
        self.max_health = PLAYER_HEALTH
        self.is_alive = True
        
        self.score = 0
        
        self.death_time = 0
        self.is_respawning = False
        self.respawn_time_remaining_override = None
        
        self.can_shoot = True
        self.last_shot_time = 0
        
        self.velocity_x = 0
        self.velocity_y = 0
        
    def update(self, dt, walls):
        if not self.is_alive:
            return
            
        if self.velocity_x != 0 or self.velocity_y != 0:
            diagonal = (self.velocity_x != 0 and self.velocity_y != 0)
            if diagonal:
                scale = 0.7071
                vel_x = self.velocity_x * scale * self.speed * dt
                vel_y = self.velocity_y * scale * self.speed * dt
            else:
                vel_x = self.velocity_x * self.speed * dt
                vel_y = self.velocity_y * self.speed * dt
            
            nearby_walls = [w for w in walls if abs(w.rect.x - self.rect.x) < 96 and 
                             abs(w.rect.y - self.rect.y) < 96]
            
            self.x += vel_x
            self.rect.x = int(self.x)
            
            for wall in nearby_walls:
                if wall.blocks_player and self.rect.colliderect(wall.rect):
                    if self.velocity_x > 0:
                        self.rect.right = wall.rect.left
                    else:
                        self.rect.left = wall.rect.right
                    self.x = float(self.rect.x)
                    break
            
            self.y += vel_y
            self.rect.y = int(self.y)
            
            for wall in nearby_walls:
                if wall.blocks_player and self.rect.colliderect(wall.rect):
                    if self.velocity_y > 0:
                        self.rect.bottom = wall.rect.top
                    else:
                        self.rect.top = wall.rect.bottom
                    self.y = float(self.rect.y)
                    break
        
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_shot_time >= FIRE_COOLDOWN:
                self.can_shoot = True
        
        return None
    
    def move(self, dx, dy):
        self.velocity_x = dx
        self.velocity_y = dy
    
    def rotate(self, dx, dy):
        if dx == 0 and dy == 0:
            return
            
        if dx == 0 and dy == -1:
            self.angle = 90
        elif dx == 1 and dy == -1:
            self.angle = 45
        elif dx == 1 and dy == 0:
            self.angle = 0
        elif dx == 1 and dy == 1:
            self.angle = 315
        elif dx == 0 and dy == 1:
            self.angle = 270
        elif dx == -1 and dy == 1:
            self.angle = 225
        elif dx == -1 and dy == 0:
            self.angle = 180
        elif dx == -1 and dy == -1:
            self.angle = 135
        
        old_center = self.rect.center
        
        temp_image = self.original_image.copy()
        temp_image = pygame.transform.flip(temp_image, False, True)
        rotated_image = pygame.transform.rotate(temp_image, self.angle)
        
        rotated_rect = rotated_image.get_rect()
        
        crop_x = max(0, (rotated_rect.width - 48) // 2)
        crop_y = max(0, (rotated_rect.height - 48) // 2)
        
        self.image = pygame.Surface((48, 48), pygame.SRCALPHA)
        
        source_rect = pygame.Rect(crop_x, crop_y, 48, 48)
        
        if rotated_rect.width < 48 or rotated_rect.height < 48:
            dest_x = (48 - rotated_rect.width) // 2
            dest_y = (48 - rotated_rect.height) // 2
            self.image.blit(rotated_image, (dest_x, dest_y))
        else:
            self.image.blit(rotated_image, (0, 0), source_rect)
        
        self.rect = pygame.Rect(0, 0, 48, 48)
        self.rect.center = old_center
    
    def shoot(self):
        if not self.can_shoot or not self.is_alive:
            return None
            
        self.can_shoot = False
        self.last_shot_time = pygame.time.get_ticks()
        
        center_x, center_y = self.rect.center
        direction_x, direction_y = get_direction_from_angle(self.angle)
        
        return Projectile(center_x, center_y, self.angle, self, 
                         player_velocity=(self.velocity_x, self.velocity_y))
    
    def take_damage(self, damage):
        if not self.is_alive:
            return
            
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            self.is_alive = False
            self.death_time = pygame.time.get_ticks()
            self.is_respawning = True
    
    def add_score(self, points=1):
        self.score += points
    
    def respawn(self, x=None, y=None):
        if x is not None and y is not None:
            self.spawn_x = x
            self.spawn_y = y
        
        self.x = self.spawn_x
        self.y = self.spawn_y
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        self.health = self.max_health
        self.is_alive = True
        self.is_respawning = False
        self.death_time = 0
        self.respawn_time_remaining_override = None
        
    def can_respawn(self):
        if not self.is_respawning:
            return False
        current_time = pygame.time.get_ticks()
        return current_time - self.death_time >= RESPAWN_DELAY
    
    def get_respawn_time_remaining(self):
        if not self.is_respawning:
            return 0
        
        if self.respawn_time_remaining_override is not None:
            return max(0, self.respawn_time_remaining_override)
        
        if self.death_time == 0:
            return 0
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.death_time
        remaining = RESPAWN_DELAY - elapsed
        return max(0, remaining)
    
    def get_team_color(self):
        if self.player_id == 0:
            return (0, 100, 255)
        elif self.player_id == 1:
            return (255, 100, 100)
        else:
            return (255, 255, 255)
    
    def draw(self, screen, show_ui=True):
        if self.is_alive:
            rect = self.image.get_rect(center=self.rect.center)
            screen.blit(self.image, rect.topleft)
            
            if show_ui:
                font = pygame.font.SysFont(None, 20)
                health_text = font.render(f"HP: {self.health}", True, self.get_team_color())
                screen.blit(health_text, (self.rect.x, self.rect.y - 20))
        
        elif self.is_respawning and show_ui:
            font = pygame.font.SysFont(None, 24)
            remaining_time = self.get_respawn_time_remaining() // 1000 + 1
            respawn_text = font.render(f"Respawning in {remaining_time}s", True, self.get_team_color())
            text_rect = respawn_text.get_rect(center=(self.spawn_x + 24, self.spawn_y + 24))
            screen.blit(respawn_text, text_rect)
        
        if show_ui:
            font = pygame.font.SysFont(None, 28)
            score_text = font.render(f"Player {self.player_id + 1}: {self.score}", True, self.get_team_color())
            score_y = 10 + (self.player_id * 30)
            screen.blit(score_text, (10, score_y))
