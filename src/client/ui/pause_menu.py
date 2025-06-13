import pygame
from src.config.settings import SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, WHITE, BLUE

class PauseMenu:
    def __init__(self, screen):
        self.screen = screen
        self.font_large = pygame.font.SysFont(None, 48)
        self.font_medium = pygame.font.SysFont(None, 36)
        self.selected_option = 0
        self.options = ["Resume", "Quit to Main Menu"]
        
    def handle_input(self, action):
        if action.get('type') == 'pause_menu_up':
            self.selected_option = (self.selected_option - 1) % len(self.options)
        elif action.get('type') == 'pause_menu_down':
            self.selected_option = (self.selected_option + 1) % len(self.options)
        elif action.get('type') == 'pause_menu_select':
            if self.selected_option == 0:
                return {'type': 'resume'}
            elif self.selected_option == 1:
                return {'type': 'quit_to_menu'}
        elif action.get('type') == 'resume':
            return {'type': 'resume'}
        return None
        
    def draw(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        menu_width, menu_height = 300, 200
        menu_x = (SCREEN_WIDTH - menu_width) // 2
        menu_y = (SCREEN_HEIGHT - menu_height) // 2
        
        menu_bg = pygame.Rect(menu_x, menu_y, menu_width, menu_height)
        pygame.draw.rect(self.screen, BLACK, menu_bg)
        pygame.draw.rect(self.screen, WHITE, menu_bg, 3)
        
        title_text = self.font_large.render("PAUSED", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, menu_y + 40))
        self.screen.blit(title_text, title_rect)
        
        for i, option in enumerate(self.options):
            color = BLUE if i == self.selected_option else WHITE
            text = self.font_medium.render(option, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH//2, menu_y + 90 + i * 40))
            self.screen.blit(text, text_rect)
