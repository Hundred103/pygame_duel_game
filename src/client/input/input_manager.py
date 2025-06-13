import pygame
from src.server.game_logic.game_state import GameStateType

class InputManager:
    def __init__(self):
        self.key_bindings = {
            'move_up': pygame.K_w,
            'move_down': pygame.K_s,
            'move_left': pygame.K_a,
            'move_right': pygame.K_d,
            'rotate_up': pygame.K_UP,
            'rotate_down': pygame.K_DOWN,
            'rotate_left': pygame.K_LEFT,
            'rotate_right': pygame.K_RIGHT,
            'shoot': pygame.K_SPACE,
            'restart': pygame.K_r,
            'pause': pygame.K_p,
            'quit': pygame.K_ESCAPE,
            'quit_to_menu': pygame.K_q
        }
        
    def process_input(self, game_state, controllable_player, events=None):
        actions = []
        keys = pygame.key.get_pressed()
        
        if events is not None:
            for event in events:
                action = self._process_event(event, game_state)
                if action:
                    actions.append(action)
        else:
            for event in pygame.event.get():
                action = self._process_event(event, game_state)
                if action:
                    actions.append(action)
        
        if game_state.is_playing() and controllable_player and controllable_player.is_alive:
            continuous_actions = self._process_continuous_input(keys, controllable_player)
            actions.extend(continuous_actions)
            
        return actions
        
    def _process_event(self, event, game_state):
        if event.type == pygame.QUIT:
            return {'type': 'quit'}
            
        if event.type == pygame.KEYDOWN:
            if game_state.current_state == GameStateType.GAME_OVER:
                if event.key == self.key_bindings['restart']:
                    return {'type': 'restart'}
                elif event.key == self.key_bindings['quit_to_menu']:
                    return {'type': 'quit_to_menu'}
            elif event.key == self.key_bindings['quit']:
                if game_state.current_state == GameStateType.PAUSED:
                    return {'type': 'resume'}
                elif game_state.current_state == GameStateType.PLAYING:
                    return {'type': 'pause'}
                else:
                    return {'type': 'quit'}
            elif event.key == self.key_bindings['pause'] and game_state.is_playing():
                return {'type': 'pause'}
            elif game_state.current_state == GameStateType.PAUSED:
                if event.key == pygame.K_UP:
                    return {'type': 'pause_menu_up'}
                elif event.key == pygame.K_DOWN:
                    return {'type': 'pause_menu_down'}
                elif event.key == pygame.K_RETURN:
                    return {'type': 'pause_menu_select'}
                    
        return None
        
    def _process_continuous_input(self, keys, player):
        actions = []
        
        dx, dy = 0, 0
        if keys[self.key_bindings['move_left']]:
            dx -= 1
        if keys[self.key_bindings['move_right']]:
            dx += 1
        if keys[self.key_bindings['move_up']]:
            dy -= 1
        if keys[self.key_bindings['move_down']]:
            dy += 1
            
        actions.append({
            'type': 'move',
            'player': player,
            'dx': dx,
            'dy': dy
        })
            
        rot_dx, rot_dy = 0, 0
        if keys[self.key_bindings['rotate_left']]:
            rot_dx -= 1
        if keys[self.key_bindings['rotate_right']]:
            rot_dx += 1
        if keys[self.key_bindings['rotate_up']]:
            rot_dy -= 1
        if keys[self.key_bindings['rotate_down']]:
            rot_dy += 1
            
        if rot_dx != 0 or rot_dy != 0:
            actions.append({
                'type': 'rotate',
                'player': player,
                'dx': rot_dx,
                'dy': rot_dy
            })
            
        if keys[self.key_bindings['shoot']] and player.can_shoot:
            actions.append({
                'type': 'shoot',
                'player': player
            })
            
        return actions
        
    def get_key_binding(self, action):
        return self.key_bindings.get(action)
        
    def set_key_binding(self, action, key):
        self.key_bindings[action] = key
