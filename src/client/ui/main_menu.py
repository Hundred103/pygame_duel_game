import pygame
import threading
import time
from src.config.settings import SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, WHITE, BLUE, RED
from src.network.socket_server import GameServer
from src.network.socket_client import GameClient

class MainMenu:
    def __init__(self, screen):
        self.screen = screen
        self.font_large = pygame.font.SysFont(None, 48)
        self.font_medium = pygame.font.SysFont(None, 36)
        self.font_small = pygame.font.SysFont(None, 24)
        
        self.state = 'main'
        self.selected_option = 0
        self.server = None
        self.client = None
        self.join_code_input = ""
        self.error_message = ""
        self.connection_result = None
        self.ready_check_pending = False
        self.ready_check_start_time = 0
        self.ready_check_pending = False
        
        self.countdown_start_time = 0
        self.countdown_duration = 3.0
        
        self.known_servers = {
            'TEST': ('127.0.0.1', 12345),
            'DEMO': ('127.0.0.1', 12346) 
        }
        
    def handle_event(self, event):
        if self.state == 'main':
            return self._handle_main_menu_event(event)
        elif self.state == 'host_waiting':
            return self._handle_host_waiting_event(event)
        elif self.state == 'join_input':
            return self._handle_join_input_event(event)
        elif self.state == 'connecting':
            return self._handle_connecting_event(event)
        elif self.state == 'countdown':
            return self._handle_countdown_event(event)
        elif self.state == 'client_waiting':
            return self._handle_client_waiting_event(event)
            
        return None
        
    def _handle_main_menu_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % 3
            elif event.key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % 3
            elif event.key == pygame.K_RETURN:
                if self.selected_option == 0:
                    return self._start_host()
                elif self.selected_option == 1:
                    self.state = 'join_input'
                    self.join_code_input = ""
                    self.error_message = ""
                elif self.selected_option == 2:
                    return 'quit'
        return None
        
    def _handle_host_waiting_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._stop_host()
                self.state = 'main'
            elif event.key == pygame.K_SPACE:
                if self.server:
                    info = self.server.get_server_info()
                    if info['clients'] >= 2:
                        if self.client and self.client.is_connection_healthy():
                            if not self.ready_check_pending:
                                self.ready_check_pending = True
                                self.ready_check_start_time = time.time()
                                print("Sending ready check ping...")
                                self.client.send_message({'type': 'ready_ping'})
                                self.error_message = "Checking client connection..."
                        else:
                            self.error_message = "Connection lost - cannot start game"
        
        return None
        
    def _handle_join_input_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state = 'main'
                self.error_message = ""
            elif event.key == pygame.K_RETURN:
                if len(self.join_code_input) == 6:
                    return self._connect_to_server()
                else:
                    self.error_message = "Code must be 6 characters"
            elif event.key == pygame.K_BACKSPACE:
                self.join_code_input = self.join_code_input[:-1]
            else:
                if len(self.join_code_input) < 6 and event.unicode.isalnum():
                    self.join_code_input += event.unicode.upper()
        return None
        
    def _handle_connecting_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.client:
                    self.client.disconnect()
                    self.client = None
                self.state = 'main'
                self.error_message = ""
        return None

    def _handle_countdown_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.client:
                    self.client.send_message({'type': 'countdown_cancel'})
                self.state = 'host_waiting'
        return None

    def _handle_client_waiting_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.client:
                    self.client.disconnect()
                    self.client = None
                self.state = 'main'
                self.error_message = ""
        return None
        
    def _start_host(self):
        try:
            self.server = GameServer()
            
            server_thread = threading.Thread(target=self.server.start)
            server_thread.daemon = True
            server_thread.start()
            
            threading.Event().wait(0.5)
            
            self.client = GameClient()

            server_info = self.server.get_server_info()
            connect_host = '127.0.0.1' if server_info['host'] in ['0.0.0.0', 'localhost', '127.0.0.1'] else server_info['host']
            
            connect_port = 12345 if server_info['code'] == 'LOCALL' else server_info['port']
            print(f"Connecting to host as client: {connect_host}:{connect_port}")
            
            if self.client.connect(connect_host, connect_port):
                self.client.register_handler('connection_lost', self._handle_host_connection_lost)
                self.client.register_handler('connection_check_ok', self._handle_connection_check_ok)
                self.client.register_handler('connection_check_failed', self._handle_connection_check_failed)
                self.client.register_handler('ready_pong', self._handle_ready_pong)
                self.client.disable_timeout_checking()
            else:
                self.server.stop()
                self.server = None
                self.error_message = "Failed to connect host to server"
                return None
            
            self.state = 'host_waiting'
            self._game_starting = False
            self._last_client_count = 1
            return None
            
        except Exception as e:
            self.error_message = f"Failed to start server: {e}"
            return None
            
    def _connect_to_server(self):
        self.state = 'connecting'
        self.error_message = ""
        
        decoded_ip, decoded_port = self._decode_ip_from_code(self.join_code_input)
        
        if decoded_ip:
            host, port = decoded_ip, decoded_port
        else:
            code_servers = {
                'TEST': ('127.0.0.1', 12345),
                'DEMO': ('127.0.0.1', 12346), 
            }
            
            if self.join_code_input in code_servers:
                host, port = code_servers[self.join_code_input]
            else:
                self.error_message = f"Server with code '{self.join_code_input}' not found"
                self.state = 'join_input'
                return None
        
        connect_thread = threading.Thread(
            target=self._try_connect, 
            args=(host, port)
        )
        connect_thread.daemon = True
        connect_thread.start()
        
        return None
        
    def _encode_ip_to_code(self, ip_address, port):
        """Encode IP and port into 6-character code - SYMMETRICAL"""
        try:
            if ip_address in ['localhost', '127.0.0.1']:
                # Always use LOCALL for localhost
                return 'LOCALL'
            
            parts = ip_address.split('.')
            if len(parts) != 4:
                return None
                
            third_octet = int(parts[2])
            fourth_octet = int(parts[3])
            
            port_encoded = port
            
            combined = (third_octet << 24) | (fourth_octet << 16) | port_encoded
            
            if combined >= 36**6:
                return None
            
            chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            code = ""
            temp = combined
            for _ in range(6):
                code = chars[temp % 36] + code
                temp //= 36
                
            return code
            
        except Exception:
            return None
    
    def _decode_ip_from_code(self, code):
        """Decode 6-character code back to IP and port - SYMMETRICAL"""
        try:
            print(f"Decoding code: {code}")
            
            if code == 'LOCALL':
                print("Code is LOCALL, returning 127.0.0.1:12345")
                return '127.0.0.1', 12345

            chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            combined = 0
            for char in code:
                if char not in chars:
                    print(f"Invalid character: {char}")
                    return None, None
                combined = combined * 36 + chars.index(char)
            
            port = combined & 0xFFFF
            fourth_octet = (combined >> 16) & 0xFF
            third_octet = (combined >> 24) & 0xFF
            
            ip = f"192.168.{third_octet}.{fourth_octet}"
            
            print(f"DEBUG: Decoded IP={ip} Socket={ip}:{port}")
            return ip, port
            
        except Exception as e:
            print(f"Error decoding: {e}")
            return None, None
        
    def _try_connect(self, host, port):
        try:
            print(f"Attempting to connect to {host}:{port}")
            self.client = GameClient()
            if self.client.connect(host, port):
                time.sleep(1.0)
                if self.client.connected:
                    print(f"Successfully connected to {host}:{port}")
                    self.client.register_handler('countdown_start', self._handle_client_countdown_start)
                    self.client.register_handler('countdown_cancel', self._handle_client_countdown_cancel)
                    self.client.register_handler('connection_lost', self._handle_client_connection_lost)
                    self.client.register_handler('player_disconnected', self._handle_player_disconnected_client)
                    self.client.register_handler('connection_check_ok', self._handle_connection_check_ok)
                    self.client.register_handler('connection_check_failed', self._handle_connection_check_failed)
                    self.client.register_handler('ready_ping', self._handle_ready_ping)
                    self.client.enable_timeout_checking()
                    self.connection_result = 'connected'
                else:
                    print(f"Failed to establish stable connection to {host}:{port}")
                    self.connection_result = 'failed'
            else:
                print(f"Failed to connect to {host}:{port}")
                self.connection_result = 'failed'
        except Exception as e:
            print(f"Connection error to {host}:{port}: {e}")
            self.connection_result = 'failed'
            
    def _handle_client_countdown_start(self, message):
        self.countdown_start_time = time.time()
        self.countdown_duration = message.get('duration', 3.0)
        self.state = 'countdown'
        
    def _handle_client_countdown_cancel(self, message):
        if self.state == 'countdown':
            self.state = 'client_waiting'

    def _handle_client_connection_lost(self, message):
        if self.client:
            self.client.disconnect()
            self.client = None
        self.state = 'main'
        self.error_message = "Connection to server lost"
        
    def _handle_player_disconnected_client(self, message):
        disconnected_player = message.get('player_id')
        if disconnected_player == 0:
            if self.client:
                self.client.disconnect()
                self.client = None
            self.state = 'main'
            self.error_message = "Host disconnected"
        
    def _handle_host_connection_lost(self, message):
        self._stop_host()
        self.state = 'main'
        self.error_message = "Server connection lost"

    def _stop_host(self):
        if self.server:
            self.server.stop()
            self.server = None

    def _start_countdown(self):
        if self.client:
            self.client.send_message({
                'type': 'countdown_start',
                'duration': self.countdown_duration
            })
        
        self.countdown_start_time = time.time()
        self.state = 'countdown'
        self._game_starting = False
        return None
            
    def update(self):
        if self.state in ['host_waiting', 'client_waiting'] and self.client:
            self.client.check_connection_timeout()
            if self.client.connection_lost:
                if self.state == 'host_waiting':
                    self._handle_host_connection_lost({'reason': 'timeout'})
                elif self.state == 'client_waiting':
                    self._handle_client_connection_lost({'reason': 'timeout'})
                return None
        
        if self.state == 'host_waiting' and self.server:
            info = self.server.get_server_info()
            if info['clients'] < 2 and hasattr(self, '_last_client_count'):
                if self._last_client_count >= 2:
                    if hasattr(self.server, 'players_ready'):
                        self.server.players_ready = False
                        self.server.game_state['game_status'] = 'waiting'
            self._last_client_count = info['clients']
            
            if self.ready_check_pending:
                if time.time() - self.ready_check_start_time > 1.0:
                    print("Ready check timeout - client not responding")
                    self.ready_check_pending = False
                    self.error_message = "Client not responding - check connection"
        
        if self.state == 'connecting' and self.connection_result:
            if self.connection_result == 'failed':
                self.error_message = "Failed to connect to server"
                self.state = 'join_input'
                self.connection_result = None
            elif self.connection_result == 'connected':
                self.state = 'client_waiting'
                self.connection_result = None
            else:
                return self.connection_result
        
        if self.state == 'countdown':
            elapsed = time.time() - self.countdown_start_time
            if elapsed >= self.countdown_duration:
                if self.client:
                    self.client.enable_timeout_checking()
                    
                if self.server:
                    return {
                        'type': 'start_game',
                        'mode': 'host',
                        'server': self.server,
                        'client': self.client
                    }
                elif self.client:
                    return {
                        'type': 'start_game',
                        'mode': 'client',
                        'client': self.client
                    }
                
        return None
        
    def draw(self):
        self.screen.fill(BLACK)
        
        if self.state == 'main':
            self._draw_main_menu()
        elif self.state == 'host_waiting':
            self._draw_host_waiting()
        elif self.state == 'join_input':
            self._draw_join_input()
        elif self.state == 'connecting':
            self._draw_connecting()
        elif self.state == 'countdown':
            self._draw_countdown()
        elif self.state == 'client_waiting':
            self._draw_client_waiting()
            
    def _draw_main_menu(self):
        title_text = self.font_large.render("DUEL GAME", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 150))
        self.screen.blit(title_text, title_rect)
        
        options = ["Host Game", "Join Game", "Quit"]
        for i, option in enumerate(options):
            color = WHITE if i == self.selected_option else (128, 128, 128)
            text = self.font_medium.render(option, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH//2, 250 + i * 60))
            self.screen.blit(text, text_rect)
            
        instructions = "Use UP/DOWN to navigate, ENTER to select"
        inst_text = self.font_small.render(instructions, True, (200, 200, 200))
        inst_rect = inst_text.get_rect(center=(SCREEN_WIDTH//2, 450))
        self.screen.blit(inst_text, inst_rect)
        
        if self.error_message:
            error_text = self.font_small.render(self.error_message, True, RED)
            error_rect = error_text.get_rect(center=(SCREEN_WIDTH//2, 500))
            self.screen.blit(error_text, error_rect)
            
    def _draw_host_waiting(self):
        title_text = self.font_large.render("HOSTING GAME", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 150))
        self.screen.blit(title_text, title_rect)
        
        if self.server:
            info = self.server.get_server_info()
            code_text = self.font_medium.render(f"Server Code: {info['code']}", True, BLUE)
            code_rect = code_text.get_rect(center=(SCREEN_WIDTH//2, 220))
            self.screen.blit(code_text, code_rect)
            
            port_text = self.font_small.render(f"Port: {info['port']}", True, WHITE)
            port_rect = port_text.get_rect(center=(SCREEN_WIDTH//2, 260))
            self.screen.blit(port_text, port_rect)
            
            actual_players = 1 + max(0, info['clients'] - 1)
            clients_text = self.font_medium.render(f"Players: {actual_players}/2", True, WHITE)
            clients_rect = clients_text.get_rect(center=(SCREEN_WIDTH//2, 320))
            self.screen.blit(clients_text, clients_rect)
            
            if info.get('ready', False):
                ready_text = self.font_medium.render("Game Ready! Starting...", True, (0, 255, 0))
                ready_rect = ready_text.get_rect(center=(SCREEN_WIDTH//2, 370))
                self.screen.blit(ready_text, ready_rect)
                
                # Add the press space instruction below
                space_text = self.font_small.render("Press SPACE to begin", True, (0, 255, 0))
                space_rect = space_text.get_rect(center=(SCREEN_WIDTH//2, 400))
                self.screen.blit(space_text, space_rect)
            elif self.ready_check_pending:
                ready_text = self.font_medium.render("Checking client readiness...", True, (255, 255, 0))
                ready_rect = ready_text.get_rect(center=(SCREEN_WIDTH//2, 380))
                self.screen.blit(ready_text, ready_rect)
            elif info['clients'] >= 2:
                ready_text = self.font_medium.render("Second player connected!", True, (0, 255, 0))
                ready_rect = ready_text.get_rect(center=(SCREEN_WIDTH//2, 370))
                self.screen.blit(ready_text, ready_rect)
                
                space_text = self.font_medium.render("Press SPACE to start game", True, (0, 255, 0))
                space_rect = space_text.get_rect(center=(SCREEN_WIDTH//2, 400))
                self.screen.blit(space_text, space_rect)
            else:
                waiting_text = self.font_medium.render("Waiting for one more player...", True, (200, 200, 200))
                waiting_rect = waiting_text.get_rect(center=(SCREEN_WIDTH//2, 380))
                self.screen.blit(waiting_text, waiting_rect)
                
                share_text = self.font_small.render("Share the code with another player", True, (150, 150, 150))
                share_rect = share_text.get_rect(center=(SCREEN_WIDTH//2, 410))
                self.screen.blit(share_text, share_rect)
        
        esc_text = self.font_small.render("Press ESC to cancel", True, (200, 200, 200))
        esc_rect = esc_text.get_rect(center=(SCREEN_WIDTH//2, 450))
        self.screen.blit(esc_text, esc_rect)
        
        if self.error_message:
            error_text = self.font_small.render(self.error_message, True, RED)
            error_rect = error_text.get_rect(center=(SCREEN_WIDTH//2, 480))
            self.screen.blit(error_text, error_rect)
        
    def _draw_join_input(self):
        title_text = self.font_large.render("JOIN GAME", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 150))
        self.screen.blit(title_text, title_rect)
        
        prompt_text = self.font_medium.render("Enter Server Code:", True, WHITE)
        prompt_rect = prompt_text.get_rect(center=(SCREEN_WIDTH//2, 220))
        self.screen.blit(prompt_text, prompt_rect)
        
        input_bg = pygame.Rect(SCREEN_WIDTH//2 - 100, 260, 200, 40)
        pygame.draw.rect(self.screen, WHITE, input_bg)
        pygame.draw.rect(self.screen, BLACK, input_bg, 2)
        
        input_text = self.font_medium.render(self.join_code_input, True, BLACK)
        input_rect = input_text.get_rect(center=input_bg.center)
        self.screen.blit(input_text, input_rect)
        
        inst_text = self.font_small.render("Enter 6-character code, then press ENTER", True, (200, 200, 200))
        inst_rect = inst_text.get_rect(center=(SCREEN_WIDTH//2, 350))
        self.screen.blit(inst_text, inst_rect)
        
        demo_text = self.font_small.render("LOCALL = localhost, other codes = LAN servers", True, (150, 150, 150))
        demo_rect = demo_text.get_rect(center=(SCREEN_WIDTH//2, 380))
        self.screen.blit(demo_text, demo_rect)
        
        esc_text = self.font_small.render("Press ESC to go back", True, (200, 200, 200))
        esc_rect = esc_text.get_rect(center=(SCREEN_WIDTH//2, 450))
        self.screen.blit(esc_text, esc_rect)
        
        if self.error_message:
            error_text = self.font_small.render(self.error_message, True, RED)
            error_rect = error_text.get_rect(center=(SCREEN_WIDTH//2, 500))
            self.screen.blit(error_text, error_rect)
            
    def _draw_connecting(self):
        title_text = self.font_large.render("CONNECTING...", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 200))
        self.screen.blit(title_text, title_rect)
        
        msg_text = self.font_medium.render(f"Connecting to: {self.join_code_input}", True, (200, 200, 200))
        msg_rect = msg_text.get_rect(center=(SCREEN_WIDTH//2, 280))
        self.screen.blit(msg_text, msg_rect)
        
        esc_text = self.font_small.render("Press ESC to cancel", True, (200, 200, 200))
        esc_rect = esc_text.get_rect(center=(SCREEN_WIDTH//2, 450))
        self.screen.blit(esc_text, esc_rect)
        
    def _draw_countdown(self):
        elapsed = time.time() - self.countdown_start_time
        remaining = max(0, self.countdown_duration - elapsed)
        countdown_number = int(remaining) + 1 if remaining > 0 else 0
        
        title_text = self.font_large.render("STARTING GAME", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 150))
        self.screen.blit(title_text, title_rect)
        
        if countdown_number > 0:
            countdown_font = pygame.font.SysFont(None, 120)
            countdown_text = countdown_font.render(str(countdown_number), True, (0, 255, 0))
            countdown_rect = countdown_text.get_rect(center=(SCREEN_WIDTH//2, 300))
            self.screen.blit(countdown_text, countdown_rect)
        else:
            go_font = pygame.font.SysFont(None, 120)
            go_text = go_font.render("GO!", True, (255, 255, 0))
            go_rect = go_text.get_rect(center=(SCREEN_WIDTH//2, 300))
            self.screen.blit(go_text, go_rect)
        
        esc_text = self.font_small.render("Press ESC to cancel", True, (200, 200, 200))
        esc_rect = esc_text.get_rect(center=(SCREEN_WIDTH//2, 450))
        self.screen.blit(esc_text, esc_rect)

    def _draw_client_waiting(self):
        title_text = self.font_large.render("CONNECTED!", True, (0, 255, 0))
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 200))
        self.screen.blit(title_text, title_rect)
        
        waiting_text = self.font_medium.render("Waiting for the host to start the game...", True, WHITE)
        waiting_rect = waiting_text.get_rect(center=(SCREEN_WIDTH//2, 280))
        self.screen.blit(waiting_text, waiting_rect)
        
        escape_text = self.font_small.render("Press ESC to disconnect", True, (128, 128, 128))
        escape_rect = escape_text.get_rect(center=(SCREEN_WIDTH//2, 400))
        self.screen.blit(escape_text, escape_rect)

    def _handle_connection_check_ok(self, message):
        pass
        
    def _handle_connection_check_failed(self, message):
        self.error_message = "Connection to server lost"
        self._reset_to_main_menu()

    def _handle_ready_ping(self, message):
        print("Received ready ping, sending pong...")
        if self.client:
            self.client.send_message({'type': 'ready_pong'})

    def _handle_ready_pong(self, message):
        print("Received ready pong - client is ready!")
        self.ready_check_pending = False
        self.error_message = ""
        return self._start_countdown()

    def _reset_to_main_menu(self):
        if self.client:
            self.client.disconnect()
            self.client = None
        self._stop_host()
        self.state = 'main'

    def cleanup(self):
        self._stop_host()
        if self.client:
            self.client.disconnect()
            self.client = None
