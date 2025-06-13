import pygame
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.client.graphics.game_renderer import GameRenderer
from src.client.input.input_manager import InputManager
from src.client.ui.main_menu import MainMenu
from src.server.game_logic.multiplayer_game import MultiplayerGame
from src.config.settings import FPS

def main():
    pygame.init()
    
    renderer = GameRenderer()
    input_manager = InputManager()
    main_menu = MainMenu(renderer.screen)
    
    current_state = 'menu'
    game = None
    
    running = True
    while running:
        events = []
        for event in pygame.event.get():
            events.append(event)
            if event.type == pygame.QUIT:
                running = False
                break
                
            if current_state == 'menu':
                menu_result = main_menu.handle_event(event)
                if menu_result == 'quit':
                    running = False
                elif isinstance(menu_result, dict) and menu_result.get('type') == 'start_game':
                    mode = menu_result.get('mode')
                    server = menu_result.get('server')
                    client = menu_result.get('client')
                    
                    game = MultiplayerGame(mode=mode, server=server, client=client)
                    game.set_pause_menu(renderer.screen)
                    current_state = 'game'
                    
        if not running:
            break
            
        if current_state == 'menu':
            menu_result = main_menu.update()
            if isinstance(menu_result, dict) and menu_result.get('type') == 'start_game':
                mode = menu_result.get('mode')
                server = menu_result.get('server')
                client = menu_result.get('client')
                
                game = MultiplayerGame(mode=mode, server=server, client=client)
                game.set_pause_menu(renderer.screen)
                current_state = 'game'
            else:
                main_menu.draw()
                pygame.display.flip()
                
        elif current_state == 'game' and game:
            actions = input_manager.process_input(game.game_state, game.get_controllable_player(), events)
            
            for action in actions:
                if action.get('type') == 'quit':
                    game.cleanup()
                    game = None
                    current_state = 'menu'
                    break
                else:
                    game.process_action(action)
            
            if current_state == 'game':
                if hasattr(game, 'should_return_to_menu') and game.should_return_to_menu:
                    restart_requested = getattr(game, 'restart_requested', False)
                    quit_to_main_menu = getattr(game, 'quit_to_main_menu', False)
                    server = getattr(game, 'server', None)
                    client = getattr(game, 'client', None)
                    game_mode = getattr(game, 'mode', None)
                    
                    game.cleanup()
                    game = None
                    current_state = 'menu'
                    
                    if quit_to_main_menu:
                        main_menu.server = None
                        main_menu.client = None
                        main_menu.state = 'main'
                    elif restart_requested and server and game_mode == 'host':
                        main_menu.server = server
                        main_menu.client = client
                        main_menu.state = 'host_waiting'
                    elif restart_requested and client and game_mode == 'client':
                        main_menu.server = None
                        main_menu.client = client
                        main_menu.state = 'client_waiting'
                else:
                    game.update()
                    game_mode = getattr(game, 'mode', None)
                    renderer.render_frame(game.game_state, game.get_pause_menu(), game_mode)
        
        renderer.tick(FPS)
    
    if game:
        game.cleanup()
    main_menu.cleanup()
    renderer.cleanup()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
