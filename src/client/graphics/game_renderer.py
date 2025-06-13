import pygame
from src.config.settings import SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, WHITE, TITLE
from src.server.game_logic.game_state import GameStateType

class GameRenderer:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.fonts = {
            'small': pygame.font.SysFont(None, 24),
            'medium': pygame.font.SysFont(None, 36),
            'large': pygame.font.SysFont(None, 48)
        }
        
    def render_frame(self, game_state, pause_menu=None, game_mode=None):
        self.clear_screen()
        
        if game_state.current_state == GameStateType.MENU:
            self._render_menu()
        elif game_state.current_state == GameStateType.PLAYING:
            self._render_gameplay(game_state)
        elif game_state.current_state == GameStateType.PAUSED:
            self._render_gameplay(game_state)
            if pause_menu:
                pause_menu.draw()
        elif game_state.current_state == GameStateType.GAME_OVER:
            self._render_gameplay(game_state)
            self._render_game_over(game_state, game_mode)
        elif game_state.current_state == GameStateType.WAITING:
            self._render_gameplay(game_state)
            
        self.present()
        
    def clear_screen(self):
        self.screen.fill(BLACK)
        
    def _render_menu(self):
        title_text = self.fonts['large'].render("DUEL GAME", True, WHITE)
        start_text = self.fonts['medium'].render("Press SPACE to start", True, WHITE)
        
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
        start_rect = start_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
        
        self.screen.blit(title_text, title_rect)
        self.screen.blit(start_text, start_rect)
        
    def _render_gameplay(self, game_state):
        if game_state.game_map:
            game_state.game_map.draw(self.screen)
            
        for player in game_state.players:
            player.draw(self.screen, show_ui=False)
            
        for projectile in game_state.projectiles:
            projectile.draw(self.screen)
            
        self._render_ui(game_state)
        
    def _render_ui(self, game_state):
        for player in game_state.players:
            if player.player_id == 0:
                color = (100, 100, 255) if player.is_alive else (100, 100, 100)
                pos = (10, 10)
                team_name = "Blue"
            elif player.player_id == 1:
                color = (255, 100, 100) if player.is_alive else (100, 100, 100)
                team_name = "Red"
            else:
                continue
                
            health_status = f"{player.health}" if player.is_alive else "DEAD"
            respawn_info = ""
            
            if player.is_respawning:
                respawn_time = player.get_respawn_time_remaining() // 1000 + 1
                health_status = "DEAD"
                respawn_info = f"Respawning in {respawn_time}s"
            
            text = f"{team_name} - Score: {player.score} | HP: {health_status}"
            health_surface = self.fonts['medium'].render(text, True, color)
            
            if player.player_id == 1:
                pos = (SCREEN_WIDTH - health_surface.get_width() - 10, 10)
            
            self.screen.blit(health_surface, pos)
            
            if respawn_info:
                respawn_surface = self.fonts['small'].render(respawn_info, True, color)
                respawn_pos = (pos[0], pos[1] + 35)
                self.screen.blit(respawn_surface, respawn_pos)
            
        from src.config.settings import POINTS_TO_WIN
        progress_text = f"First to {POINTS_TO_WIN} points wins!"
        progress_surface = self.fonts['small'].render(progress_text, True, BLACK)
        progress_pos = (SCREEN_WIDTH//2 - progress_surface.get_width()//2, 50)
        self.screen.blit(progress_surface, progress_pos)
        
        if game_state.timer_active:
            timer_text = f"Time: {game_state.format_timer()}"
            timer_surface = self.fonts['medium'].render(timer_text, True, WHITE)
            timer_pos = (SCREEN_WIDTH//2 - timer_surface.get_width()//2, 10)
            self.screen.blit(timer_surface, timer_pos)
            
    def _render_game_over(self, game_state, game_mode=None):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        if game_state.winner:
            if game_state.winner.player_id == 0:
                winner_text = "BLUE PLAYER WINS!"
            elif game_state.winner.player_id == 1:
                winner_text = "RED PLAYER WINS!"
            else:
                winner_text = f"PLAYER {game_state.winner.player_id} WINS!"
        else:
            winner_text = "TIME'S UP - DRAW!" if game_state.get_remaining_time() <= 0 else "DRAW!"
        
        player_scores = []
        for player in game_state.players:
            if player.player_id == 0:
                player_scores.append(f"Blue: {player.score}")
            elif player.player_id == 1:
                player_scores.append(f"Red: {player.score}")
            else:
                player_scores.append(f"Player {player.player_id}: {player.score}")
        
        score_text = " | ".join(player_scores)
            
        game_over_text = self.fonts['large'].render("GAME OVER", True, (255, 0, 0))
        winner_display = self.fonts['medium'].render(winner_text, True, WHITE)
        scores_display = self.fonts['medium'].render(f"Final Scores: {score_text}", True, WHITE)
        
        if game_mode == 'host':
            option1_text = self.fonts['small'].render("Press R to restart round", True, WHITE)
            option2_text = self.fonts['small'].render("Press Q to quit to main menu", True, WHITE)
            
            game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 90))
            winner_rect = winner_display.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
            scores_rect = scores_display.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 10))
            option1_rect = option1_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 30))
            option2_rect = option2_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 60))
            
            self.screen.blit(game_over_text, game_over_rect)
            self.screen.blit(winner_display, winner_rect)
            self.screen.blit(scores_display, scores_rect)
            self.screen.blit(option1_text, option1_rect)
            self.screen.blit(option2_text, option2_rect)
        else:
            quit_text = self.fonts['small'].render("Press Q to quit to main menu", True, WHITE)
            
            game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 90))
            winner_rect = winner_display.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
            scores_rect = scores_display.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 10))
            quit_rect = quit_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 40))
            
            self.screen.blit(game_over_text, game_over_rect)
            self.screen.blit(winner_display, winner_rect)
            self.screen.blit(scores_display, scores_rect)
            self.screen.blit(quit_text, quit_rect)
        
    def present(self):
        pygame.display.flip()
        
    def tick(self, fps):
        return self.clock.tick(fps)
        
    def get_fps(self):
        return self.clock.get_fps()
        
    def cleanup(self):
        pygame.quit()
