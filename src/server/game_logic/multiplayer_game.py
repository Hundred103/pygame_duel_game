import pygame
import threading
from src.common.entities.player import Player
from src.common.entities.map import Map
from src.server.game_logic.game_state import GameState, GameStateType
from src.config.settings import FPS, PLAYER_BLUE, PLAYER_RED
from src.client.ui.pause_menu import PauseMenu

class MultiplayerGame:
    def __init__(self, mode='host', server=None, client=None):
        self.mode = mode
        self.server = server
        self.client = client
        self.running = True
        self.should_return_to_menu = False
        self.restart_requested = False
        self.quit_to_main_menu = False
        self.game_state = GameState()
        self.game_state.set_state(GameStateType.PLAYING)
        self.game_state.game_map = Map()
        self.pause_menu = None
        self.network_lock = threading.Lock()
        self.last_network_update = 0
        self.network_update_interval = 1/30
        self.interpolation_enabled = (mode == 'client')
        self.interpolation_targets = {}
        self.interpolation_duration = 1/30
        self.projectile_interpolation = {}
        self.projectile_id_counter = 0
        self._initialize_players()
        if self.client:
            self._setup_client_handlers()
        if self.server and self.mode == 'host':
            self._setup_server_handlers()
        if self.mode == 'host' and self.client:
            self.client.enable_timeout_checking()
        self.last_time = pygame.time.get_ticks()
        self.game_state.start_timer(self.last_time)
        
    def _initialize_players(self):
        blue_spawn = self.game_state.game_map.get_spawn_position(PLAYER_BLUE)
        red_spawn = self.game_state.game_map.get_spawn_position(PLAYER_RED)
        if self.mode == 'host':
            self.local_player = Player(blue_spawn[0], blue_spawn[1], "player_blue.png", PLAYER_BLUE)
            self.remote_player = Player(red_spawn[0], red_spawn[1], "player_red.png", PLAYER_RED)
            self.local_player_id = PLAYER_BLUE
            self.remote_player_id = PLAYER_RED
        else:
            self.local_player = Player(red_spawn[0], red_spawn[1], "player_blue.png", PLAYER_RED)
            self.remote_player = Player(blue_spawn[0], blue_spawn[1], "player_red.png", PLAYER_BLUE)
            self.local_player_id = PLAYER_RED
            self.remote_player_id = PLAYER_BLUE
        self.game_state.add_player(self.local_player)
        self.game_state.add_player(self.remote_player)
        if self.interpolation_enabled:
            self.interpolation_targets[self.local_player_id] = None
            self.interpolation_targets[self.remote_player_id] = None
        
    def _setup_server_handlers(self):
        if self.client:
            self.client.register_handler('player_input', self._handle_player_input)
            self.client.register_handler('restart_request', self._handle_restart_request)
        
    def _handle_player_input(self, message):
        if self.mode != 'host':
            return
        data = message.get('data', {})
        player_id = data.get('player_id')
        input_type = data.get('type')
        if input_type == 'pause':
            if self.game_state.current_state == GameStateType.PLAYING:
                self.game_state.set_state(GameStateType.PAUSED)
            elif self.game_state.current_state == GameStateType.PAUSED:
                self.game_state.set_state(GameStateType.PLAYING)
            return
        if input_type == 'resume':
            if self.game_state.current_state == GameStateType.PAUSED:
                self.game_state.set_state(GameStateType.PLAYING)
            return
        if input_type == 'quit_to_menu':
            self.client.send_message({'type': 'return_to_main_menu'})
            self.should_return_to_menu = True
            self.quit_to_main_menu = True
            return
        if player_id == self.remote_player_id and self.remote_player:
            if input_type == 'move':
                dx, dy = data.get('dx', 0), data.get('dy', 0)
                self.remote_player.move(dx, dy)
            elif input_type == 'rotate':
                dx, dy = data.get('dx', 0), data.get('dy', 0)
                self.remote_player.rotate(dx, dy)
            elif input_type == 'shoot':
                if self.remote_player.can_shoot:
                    projectile = self.remote_player.shoot()
                    if projectile:
                        projectile.projectile_id = self.projectile_id_counter
                        self.projectile_id_counter += 1
                        self.game_state.add_projectile(projectile)

    def _handle_restart_request(self, message):
        if self.mode == 'host' and self.game_state.current_state == GameStateType.GAME_OVER:
            self.should_return_to_menu = True
            self.restart_requested = True

    def _setup_client_handlers(self):
        self.client.register_handler('game_start', self._handle_game_start)
        self.client.register_handler('player_disconnected', self._handle_player_disconnected)
        self.client.register_handler('game_state_update', self._handle_game_state_update)
        self.client.register_handler('return_to_lobby', self._handle_return_to_lobby)
        self.client.register_handler('return_to_main_menu', self._handle_return_to_main_menu)
        self.client.register_handler('connection_lost', self._handle_connection_lost)
            
    def _handle_game_start(self, message):
        self.game_state.set_state(GameStateType.PLAYING)
        if self.client:
            self.client.enable_timeout_checking()
        
    def _handle_player_disconnected(self, message):
        self.should_return_to_menu = True
        
    def _handle_game_state_update(self, message):
        if self.mode != 'client':
            return
        with self.network_lock:
            data = message.get('data', {})
            if 'game_status' in data:
                new_state = GameStateType(data['game_status'])
                current_state = self.game_state.current_state
                if not (current_state == GameStateType.PLAYING and new_state == GameStateType.WAITING):
                    self.game_state.current_state = new_state
            if 'timer_remaining' in data and 'timer_active' in data:
                if data['timer_active']:
                    current_time = pygame.time.get_ticks()
                    server_remaining = data['timer_remaining']
                    self.game_state.timer_start_time = current_time - (self.game_state.timer_duration - server_remaining)
                    self.game_state.timer_active = True
                else:
                    self.game_state.timer_active = False
            if data.get('winner') is not None:
                winner_id = data['winner']
                for player in self.game_state.players:
                    if player.player_id == winner_id:
                        self.game_state.winner = player
                        break
            if 'players' in data:
                for player_data in data['players']:
                    player_id = player_data.get('id')
                    if player_id == self.local_player_id and self.local_player:
                        old_angle = self.local_player.angle
                        new_x = player_data.get('x', self.local_player.x)
                        new_y = player_data.get('y', self.local_player.y)
                        new_angle = player_data.get('angle', self.local_player.angle)
                        if self.interpolation_enabled:
                            current_time = pygame.time.get_ticks() / 1000.0
                            self._start_interpolation(player_id, (self.local_player.x, self.local_player.y), (new_x, new_y), current_time)
                            self.local_player.angle = new_angle
                        else:
                            self.local_player.x = new_x
                            self.local_player.y = new_y
                            self.local_player.angle = new_angle
                            self.local_player.rect.x = int(self.local_player.x)
                            self.local_player.rect.y = int(self.local_player.y)
                        self.local_player.health = player_data.get('health', self.local_player.health)
                        self.local_player.is_alive = player_data.get('is_alive', self.local_player.is_alive)
                        self.local_player.score = player_data.get('score', self.local_player.score)
                        self.local_player.is_respawning = player_data.get('is_respawning', self.local_player.is_respawning)
                        if self.local_player.is_respawning and 'respawn_time_remaining' in player_data:
                            self.local_player.respawn_time_remaining_override = player_data['respawn_time_remaining']
                        else:
                            self.local_player.respawn_time_remaining_override = None
                        if 'spawn_x' in player_data and 'spawn_y' in player_data:
                            self.local_player.spawn_x = player_data['spawn_x']
                            self.local_player.spawn_y = player_data['spawn_y']
                        if old_angle != self.local_player.angle:
                            self._update_player_visual_rotation(self.local_player)
                    elif player_id == self.remote_player_id and self.remote_player:
                        old_angle = self.remote_player.angle
                        new_x = player_data.get('x', self.remote_player.x)
                        new_y = player_data.get('y', self.remote_player.y)
                        new_angle = player_data.get('angle', self.remote_player.angle)
                        if self.interpolation_enabled:
                            current_time = pygame.time.get_ticks() / 1000.0
                            self._start_interpolation(player_id, (self.remote_player.x, self.remote_player.y), (new_x, new_y), current_time)
                            self.remote_player.angle = new_angle
                        else:
                            self.remote_player.x = new_x
                            self.remote_player.y = new_y
                            self.remote_player.angle = new_angle
                            self.remote_player.rect.x = int(self.remote_player.x)
                            self.remote_player.rect.y = int(self.remote_player.y)
                        self.remote_player.health = player_data.get('health', self.remote_player.health)
                        self.remote_player.is_alive = player_data.get('is_alive', self.remote_player.is_alive)
                        self.remote_player.score = player_data.get('score', self.remote_player.score)
                        self.remote_player.is_respawning = player_data.get('is_respawning', self.remote_player.is_respawning)
                        if self.remote_player.is_respawning and 'respawn_time_remaining' in player_data:
                            self.remote_player.respawn_time_remaining_override = player_data['respawn_time_remaining']
                        else:
                            self.remote_player.respawn_time_remaining_override = None
                        if 'spawn_x' in player_data and 'spawn_y' in player_data:
                            self.remote_player.spawn_x = player_data['spawn_x']
                            self.remote_player.spawn_y = player_data['spawn_y']
                        if old_angle != self.remote_player.angle:
                            self._update_player_visual_rotation(self.remote_player)
            if 'projectiles' in data:
                self._sync_projectiles_from_server(data['projectiles'])

    def _handle_return_to_lobby(self, message):
        if self.client:
            self.client.disable_timeout_checking()
        self.should_return_to_menu = True
        self.restart_requested = True

    def _handle_return_to_main_menu(self, message):
        self.should_return_to_menu = True
        self.quit_to_main_menu = True
        
    def _handle_connection_lost(self, message):
        self.should_return_to_menu = True
        self.quit_to_main_menu = True

    def set_pause_menu(self, screen):
        self.pause_menu = PauseMenu(screen)
        
    def process_action(self, action):
        action_type = action.get('type')
        
        if self.game_state.current_state == GameStateType.PAUSED and self.pause_menu:
            menu_result = self.pause_menu.handle_input(action)
            if menu_result:
                if menu_result.get('type') == 'resume':
                    if self.mode == 'host':
                        self.game_state.set_state(GameStateType.PLAYING)
                    else:
                        self._send_input_to_host({'type': 'resume'})
                elif menu_result.get('type') == 'quit_to_menu':
                    if self.mode == 'host':
                        if self.client:
                            self.client.send_message({'type': 'return_to_main_menu'})
                        self.should_return_to_menu = True
                        self.quit_to_main_menu = True
                    else:
                        self._send_input_to_host({'type': 'quit_to_menu'})
            return
            
        if action_type in ['pause', 'resume']:
            if self.mode == 'host':
                if action_type == 'pause':
                    if self.game_state.current_state == GameStateType.PLAYING:
                        self.game_state.set_state(GameStateType.PAUSED)
                    elif self.game_state.current_state == GameStateType.PAUSED:
                        self.game_state.set_state(GameStateType.PLAYING)
                elif action_type == 'resume':
                    if self.game_state.current_state == GameStateType.PAUSED:
                        self.game_state.set_state(GameStateType.PLAYING)
            else:
                self._send_input_to_host(action)
            return
        if self.game_state.current_state == GameStateType.GAME_OVER:
            if action_type == 'restart' and self.mode == 'host':
                if self.client:
                    self.client.send_message({'type': 'return_to_lobby'})
                self.should_return_to_menu = True
                self.restart_requested = True
                return
            elif action_type == 'quit_to_menu':
                if self.mode == 'host' and self.client:
                    self.client.send_message({'type': 'return_to_main_menu'})
                self.should_return_to_menu = True
                self.quit_to_main_menu = True
                return
            else:
                return
        if self.game_state.current_state != GameStateType.PLAYING:
            return
        if self.mode == 'host':
            if action_type == 'move':
                player = action.get('player')
                if player == self.local_player:
                    dx, dy = action.get('dx', 0), action.get('dy', 0)
                    player.move(dx, dy)
            elif action_type == 'rotate':
                player = action.get('player')
                if player == self.local_player:
                    dx, dy = action.get('dx', 0), action.get('dy', 0)
                    player.rotate(dx, dy)
            elif action_type == 'shoot':
                player = action.get('player')
                if player == self.local_player and player.can_shoot:
                    projectile = player.shoot()
                    if projectile:
                        projectile.projectile_id = self.projectile_id_counter
                        self.projectile_id_counter += 1
                        self.game_state.add_projectile(projectile)
            elif action_type == 'restart':
                self.restart()
        else:
            if action_type in ['move', 'rotate', 'shoot', 'pause', 'resume']:
                self._send_input_to_host(action)
            elif action_type == 'restart' and self.game_state.current_state == GameStateType.GAME_OVER:
                self._send_restart_request_to_host()
            
    def _send_input_to_host(self, action):
        if self.client:
            input_data = {
                'type': action.get('type'),
                'player_id': self.local_player_id
            }
            if action.get('type') in ['move', 'rotate']:
                input_data['dx'] = action.get('dx', 0)
                input_data['dy'] = action.get('dy', 0)
            self.client.send_message({
                'type': 'player_input',
                'data': input_data
            })
    
    def _send_restart_request_to_host(self):
        if self.client:
            self.client.send_message({
                'type': 'restart_request'
            })
            
    def _send_shoot_action(self, projectile):
        if self.client:
            shoot_data = {
                'x': projectile.x,
                'y': projectile.y,
                'angle': projectile.angle,
                'vel_x': projectile.vel_x,
                'vel_y': projectile.vel_y
            }
            self.client.send_shoot(shoot_data)
            
    def update(self):
        if self.mode == 'host':
            self._update_host()
        else:
            self._update_client()
            
    def _update_host(self):
        current_time = pygame.time.get_ticks()
        dt = (current_time - self.last_time) / 1000.0
        dt = min(dt, 0.1)
        self.last_time = current_time
        if self.server:
            server_info = self.server.get_server_info()
            if server_info['clients'] < 2:
                pass
        if self.client and self.game_state.current_state == GameStateType.PLAYING:
            self.client.check_connection_timeout()
            if self.client.connection_lost:
                self.should_return_to_menu = True
                self.quit_to_main_menu = True
                return
        if self.game_state.current_state == GameStateType.PLAYING:
            with self.network_lock:
                for player in self.game_state.players:
                    player.update(dt, self.game_state.game_map.walls)
            self.game_state.projectiles = [
                p for p in self.game_state.projectiles 
                if p.update(dt, self.game_state.game_map.walls, self.game_state.players)
            ]
            self.game_state.handle_respawn_logic()
            self.game_state.check_win_condition()
        self._send_network_update()
        
    def _update_client(self):
        current_time = pygame.time.get_ticks()
        dt = (current_time - self.last_time) / 1000.0
        self.last_time = current_time
        if self.client and self.game_state.current_state == GameStateType.PLAYING:
            self.client.check_connection_timeout()
            if self.client.connection_lost:
                self.should_return_to_menu = True
                self.quit_to_main_menu = True
                return
        if self.interpolation_enabled:
            self._update_interpolation(current_time / 1000.0)
        self._send_network_update()
        
    def _send_network_update(self):
        current_time = pygame.time.get_ticks() / 1000.0
        if current_time - self.last_network_update >= self.network_update_interval:
            self.last_network_update = current_time
            if self.client:
                if self.mode == 'host':
                    game_state_data = self._serialize_game_state()
                    self.client.send_message({
                        'type': 'game_state_update',
                        'data': game_state_data
                    })
                
    def _serialize_game_state(self):
        game_state = {
            'players': [],
            'projectiles': [],
            'game_status': self.game_state.current_state.value,
            'winner': self.game_state.winner.player_id if self.game_state.winner else None,
            'timer_remaining': self.game_state.get_remaining_time(),
            'timer_active': self.game_state.timer_active
        }
        for player in self.game_state.players:
            respawn_time_remaining = 0
            if player.is_respawning and player.death_time > 0:
                current_time = pygame.time.get_ticks()
                elapsed = current_time - player.death_time
                from src.config.settings import RESPAWN_DELAY
                respawn_time_remaining = max(0, RESPAWN_DELAY - elapsed)
            player_data = {
                'id': player.player_id,
                'x': player.x,
                'y': player.y,
                'angle': player.angle,
                'health': player.health,
                'is_alive': player.is_alive,
                'score': player.score,
                'is_respawning': player.is_respawning,
                'respawn_time_remaining': respawn_time_remaining,
                'spawn_x': player.spawn_x,
                'spawn_y': player.spawn_y
            }
            game_state['players'].append(player_data)
        for proj in self.game_state.projectiles:
            proj_data = {
                'id': proj.projectile_id,
                'x': proj.x,
                'y': proj.y,
                'angle': proj.angle,
                'owner_id': proj.owner.player_id if proj.owner else None
            }
            game_state['projectiles'].append(proj_data)
        return game_state
    
    def restart(self):
        self.game_state.reset()
        blue_spawn = self.game_state.game_map.get_spawn_position(PLAYER_BLUE)
        red_spawn = self.game_state.game_map.get_spawn_position(PLAYER_RED)
        if self.mode == 'host':
            self.local_player.set_position(blue_spawn[0], blue_spawn[1])
            self.remote_player.set_position(red_spawn[0], red_spawn[1])
        else:
            self.local_player.set_position(red_spawn[0], red_spawn[1])
            self.remote_player.set_position(blue_spawn[0], blue_spawn[1])
        for player in self.game_state.players:
            player.health = player.max_health
            player.is_alive = True
        self.game_state.start_timer(pygame.time.get_ticks())
            
    def cleanup(self):
        if self.server and getattr(self, 'quit_to_main_menu', False):
            self.server.stop()
        elif self.server and not getattr(self, 'restart_requested', False):
            self.server.stop()
        if self.client and getattr(self, 'quit_to_main_menu', False):
            self.client.disconnect()
            
    def get_controllable_player(self):
        return self.local_player
        
    def get_pause_menu(self):
        return self.pause_menu

    def _sync_projectiles_from_server(self, projectile_data_list):
        from src.common.entities.projectile import Projectile
        existing_projectiles = {}
        for proj in self.game_state.projectiles:
            if hasattr(proj, 'projectile_id') and proj.projectile_id is not None:
                existing_projectiles[proj.projectile_id] = proj
        self.game_state.projectiles.clear()
        current_time = pygame.time.get_ticks() / 1000.0
        for proj_data in projectile_data_list:
            proj_id = proj_data.get('id')
            owner_id = proj_data.get('owner_id')
            new_x = proj_data.get('x', 0)
            new_y = proj_data.get('y', 0)
            owner = None
            if self.local_player_id == owner_id:
                owner = self.local_player
            elif self.remote_player_id == owner_id:
                owner = self.remote_player
            projectile = Projectile(
                x=new_x,
                y=new_y,
                angle=proj_data.get('angle', 0),
                owner=owner,
                projectile_id=proj_id,
                play_sound=False
            )
            if self.interpolation_enabled and proj_id in existing_projectiles:
                old_proj = existing_projectiles[proj_id]
                self._start_projectile_interpolation(
                    proj_id, 
                    (old_proj.x, old_proj.y), 
                    (new_x, new_y), 
                    current_time
                )
                projectile.x = old_proj.x
                projectile.y = old_proj.y
                projectile.rect.x = int(old_proj.x)
                projectile.rect.y = int(old_proj.y)
            self.game_state.add_projectile(projectile)

    def _update_player_visual_rotation(self, player):
        old_center = player.rect.center
        temp_image = player.original_image.copy()
        temp_image = pygame.transform.flip(temp_image, False, True)
        rotated_image = pygame.transform.rotate(temp_image, player.angle)
        rotated_rect = rotated_image.get_rect()
        crop_x = max(0, (rotated_rect.width - 48) // 2)
        crop_y = max(0, (rotated_rect.height - 48) // 2)
        player.image = pygame.Surface((48, 48), pygame.SRCALPHA)
        source_rect = pygame.Rect(crop_x, crop_y, 48, 48)
        if rotated_rect.width < 48 or rotated_rect.height < 48:
            dest_x = (48 - rotated_rect.width) // 2
            dest_y = (48 - rotated_rect.height) // 2
            player.image.blit(rotated_image, (dest_x, dest_y))
        else:
            player.image.blit(rotated_image, (0, 0), source_rect)
        player.rect = pygame.Rect(0, 0, 48, 48)
        player.rect.center = old_center

    def _update_interpolation(self, current_time):
        for player_id, interp_data in self.interpolation_targets.items():
            if interp_data is None:
                continue
            elapsed = current_time - interp_data['start_time']
            progress = min(elapsed / interp_data['duration'], 1.0)
            player = None
            if player_id == self.local_player_id:
                player = self.local_player
            elif player_id == self.remote_player_id:
                player = self.remote_player
            if player is None:
                continue
            start_x, start_y = interp_data['start_pos']
            target_x, target_y = interp_data['target_pos']
            smooth_progress = self._ease_out_cubic(progress)
            new_x = start_x + (target_x - start_x) * smooth_progress
            new_y = start_y + (target_y - start_y) * smooth_progress
            player.x = new_x
            player.y = new_y
            player.rect.x = int(new_x)
            player.rect.y = int(new_y)
            if progress >= 1.0:
                self.interpolation_targets[player_id] = None
        completed_projectiles = []
        for proj_id, interp_data in self.projectile_interpolation.items():
            if interp_data is None:
                continue
            elapsed = current_time - interp_data['start_time']
            progress = min(elapsed / interp_data['duration'], 1.0)
            projectile = None
            for proj in self.game_state.projectiles:
                if hasattr(proj, 'projectile_id') and proj.projectile_id == proj_id:
                    projectile = proj
                    break
            if projectile is None:
                completed_projectiles.append(proj_id)
                continue
            start_x, start_y = interp_data['start_pos']
            target_x, target_y = interp_data['target_pos']
            new_x = start_x + (target_x - start_x) * progress
            new_y = start_y + (target_y - start_y) * progress
            projectile.x = new_x
            projectile.y = new_y
            projectile.rect.x = int(new_x)
            projectile.rect.y = int(new_y)
            if progress >= 1.0:
                completed_projectiles.append(proj_id)
        for proj_id in completed_projectiles:
            del self.projectile_interpolation[proj_id]
    
    def _ease_out_cubic(self, t):
        return 1 - pow(1 - t, 3)
    
    def _start_interpolation(self, player_id, start_pos, target_pos, current_time):
        self.interpolation_targets[player_id] = {
            'start_pos': start_pos,
            'target_pos': target_pos,
            'start_time': current_time,
            'duration': self.interpolation_duration
        }
    
    def _start_projectile_interpolation(self, proj_id, start_pos, target_pos, current_time):
        self.projectile_interpolation[proj_id] = {
            'start_pos': start_pos,
            'target_pos': target_pos,
            'start_time': current_time,
            'duration': self.interpolation_duration
        }
