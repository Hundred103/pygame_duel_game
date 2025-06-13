import pygame
import math
from src.common.entities.entity import Entity
from src.common.utils.helpers import get_direction_from_angle, load_sound
from src.config.settings import PROJECTILE_SPEED, PROJECTILE_LIFETIME, PROJECTILE_DAMAGE, TILE_SIZE, PLAYER_SPEED

class Projectile(Entity):
    def __init__(self, x, y, angle, owner, player_velocity=(0, 0), projectile_id=None, play_sound=True):
        super().__init__(x, y, 6, 6)
        
        self.angle = angle
        self.base_speed = PROJECTILE_SPEED
        self.damage = PROJECTILE_DAMAGE
        self.owner = owner
        self.projectile_id = projectile_id
        
        self.direction_x, self.direction_y = get_direction_from_angle(angle)
        
        player_vel_x, player_vel_y = player_velocity
        
        base_vel_x = self.direction_x * self.base_speed
        base_vel_y = self.direction_y * self.base_speed
        
        self.vel_x = base_vel_x + (player_vel_x * PLAYER_SPEED)
        self.vel_y = base_vel_y + (player_vel_y * PLAYER_SPEED)
        
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = PROJECTILE_LIFETIME
        
        if play_sound:
            self.sound = load_sound("shooting-sound-fx-159024.mp3")
            if self.sound:
                self.sound.play()
    
    def update(self, dt, walls, players):
        current_time = pygame.time.get_ticks()
        if current_time - self.spawn_time > self.lifetime:
            return False
            
        self.x += self.vel_x * dt
        self.y += self.vel_y * dt
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        
        nearby_walls = [w for w in walls if abs(w.rect.x - self.rect.x) < 64 and 
                         abs(w.rect.y - self.rect.y) < 64]
        
        for wall in nearby_walls:
            if self.rect.colliderect(wall.rect):
                if wall.is_solid:
                    return False
        
        for player in players:
            if player is not self.owner and player.is_alive and self.rect.colliderect(player.rect):
                was_alive = player.is_alive
                player.take_damage(self.damage)
                
                if was_alive and not player.is_alive and self.owner:
                    from src.config.settings import POINTS_PER_ELIMINATION
                    self.owner.add_score(POINTS_PER_ELIMINATION)
                
                return False
        
        return True
    
    def draw(self, screen):
        pygame.draw.circle(screen, (0, 0, 0), self.rect.center, 3)
