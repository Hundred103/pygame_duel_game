from enum import Enum
from src.config.settings import PLAYING, GAME_OVER, MENU, POINTS_TO_WIN, GAME_TIMER_DURATION

class GameStateType(Enum):
    MENU = 0
    PLAYING = 1
    GAME_OVER = 2
    PAUSED = 3
    WAITING = 4

class GameState:
    
    def __init__(self):
        self.current_state = GameStateType.PLAYING
        self.players = []
        self.projectiles = []
        self.game_map = None
        self.winner = None
        self.game_time = 0
        self.timer_start_time = 0
        self.timer_duration = GAME_TIMER_DURATION
        self.timer_active = False
        
    def set_state(self, new_state):
        self.current_state = new_state
        
    def get_state(self):
        return self.current_state
        
    def is_playing(self):
        return self.current_state == GameStateType.PLAYING
        
    def is_game_over(self):
        return self.current_state == GameStateType.GAME_OVER
        
    def add_player(self, player):
        self.players.append(player)
        
    def remove_player(self, player):
        if player in self.players:
            self.players.remove(player)
            
    def add_projectile(self, projectile):
        self.projectiles.append(projectile)
        
    def remove_projectile(self, projectile):
        if projectile in self.projectiles:
            self.projectiles.remove(projectile)
            
    def get_alive_players(self):
        return [p for p in self.players if p.is_alive]
        
    def check_win_condition(self):
        for player in self.players:
            if player.score >= POINTS_TO_WIN:
                self.set_state(GameStateType.GAME_OVER)
                self.winner = player
                return
        
        if self.timer_active and self.get_remaining_time() <= 0:
            self.set_state(GameStateType.GAME_OVER)
            if len(self.players) >= 2:
                if self.players[0].score > self.players[1].score:
                    self.winner = self.players[0]
                elif self.players[1].score > self.players[0].score:
                    self.winner = self.players[1]
                else:
                    self.winner = None
            return
                
    def handle_respawn_logic(self):
        for player in self.players:
            if player.is_respawning and player.can_respawn():
                other_players = [p for p in self.players if p != player and p.is_alive]
                enemy_player = other_players[0] if other_players else None
                spawn_pos = self.game_map.find_safe_spawn_position(enemy_player)
                player.respawn(spawn_pos[0], spawn_pos[1])
                
    def reset(self):
        self.current_state = GameStateType.PLAYING
        self.winner = None
        self.game_time = 0
        self.timer_start_time = 0
        self.timer_active = False
        self.projectiles.clear()
        
        for player in self.players:
            player.health = player.max_health if hasattr(player, 'max_health') else 100
            player.is_alive = True
            player.score = 0
            player.is_respawning = False
            player.death_time = 0
            if hasattr(player, 'spawn_x') and hasattr(player, 'spawn_y'):
                player.x = player.spawn_x
                player.y = player.spawn_y
                player.rect.x = int(player.x)
                player.rect.y = int(player.y)
    
    def start_timer(self, current_time):
        self.timer_start_time = current_time
        self.timer_active = True
        
    def get_remaining_time(self):
        import pygame
        if not self.timer_active:
            return self.timer_duration
        elapsed = pygame.time.get_ticks() - self.timer_start_time
        return max(0, self.timer_duration - elapsed)
        
    def get_remaining_time_seconds(self):
        return self.get_remaining_time() / 1000.0
        
    def format_timer(self):
        remaining_seconds = max(0, self.get_remaining_time_seconds())
        minutes = int(remaining_seconds // 60)
        seconds = int(remaining_seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
