import socket
import threading
import json
import time

class GameClient:
    def __init__(self):
        self.socket = None
        self.connected = False
        self.running = False
        self.player_id = None
        self.server_code = None
        self.server_address = None
        self.message_handlers = {}
        self.receive_thread = None
        self.last_ping = 0
        self.last_pong = 0
        self.connection_timeout = 10.0 
        self.connection_lost = False
        self.enable_timeout_check = False
        
    def connect(self, host, port):
        try:
            print(f"Client attempting to connect to {host}:{port}")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.server_address = (host, port)
            self.running = True
            self.connected = False
            
            bind_host = '0.0.0.0'
            
            self.socket.bind((bind_host, 0))
            client_port = self.socket.getsockname()[1]
            print(f"Client bound to {bind_host}:{client_port}")
            
            self.receive_thread = threading.Thread(target=self._receive_loop)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            print("Client sending connect message")
            self.send_message({'type': 'connect'})
            
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < 5.0:
                time.sleep(0.1)
            
            if self.connected:
                print("Client successfully connected to server")
                ping_thread = threading.Thread(target=self._ping_loop)
                ping_thread.daemon = True
                ping_thread.start()
                return True
            else:
                print("Client connection timeout")
                self.running = False
                return False
            
        except Exception as e:
            print(f"Client connection error: {e}")
            self.running = False
            return False
            
    def _receive_loop(self):
        print("Client receive loop started")
        while self.running:
            try:
                self.socket.settimeout(1.0)
                data, address = self.socket.recvfrom(1024)
                print(f"Client received data from {address}: {data}")
                
                def normalize_address(addr):
                    if addr in ['localhost', '127.0.0.1']:
                        return '127.0.0.1'
                    return addr
                
                server_addr = normalize_address(self.server_address[0])
                from_addr = normalize_address(address[0])
                
                if ((from_addr == server_addr or 
                     (server_addr == 'localhost' and from_addr == '127.0.0.1') or
                     (server_addr == '127.0.0.1' and from_addr == 'localhost')) and
                    address[1] == self.server_address[1]):
                    try:
                        message = json.loads(data.decode('utf-8'))
                        print(f"Client parsed message: {message}")
                        self._handle_message(message)
                    except json.JSONDecodeError:
                        print(f"Client: Invalid JSON from {address}: {data}")
                        
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Client receive error: {e}")
                    self._handle_connection_lost()
                break
                
        print("Client receive loop ended")
        self.connected = False
        
    def _handle_connection_lost(self):
        if not self.connection_lost:
            print("Client connection lost detected")
            self.connection_lost = True
            self.connected = False
            self.running = False
            
            if 'connection_lost' in self.message_handlers:
                self.message_handlers['connection_lost']({
                    'type': 'connection_lost',
                    'reason': 'timeout'
                })
        
    def _ping_loop(self):
        while self.running and self.connected:
            current_time = time.time()
            
            if current_time - self.last_ping >= 5.0:
                if self.send_message({'type': 'ping'}):
                    self.last_ping = current_time
                else:
                    self._handle_connection_lost()
                    break
            
            if self.enable_timeout_check and self.last_pong > 0 and current_time - self.last_pong > self.connection_timeout:
                self._handle_connection_lost()
                break
                
            time.sleep(1.0)
            
    def _handle_message(self, message):
        msg_type = message.get('type')
        print(f"Client handling message type: {msg_type}")
        
        if msg_type == 'welcome':
            self.player_id = message.get('player_id')
            self.server_code = message.get('server_code')
            self.connected = True
            self.last_pong = time.time()
            print(f"Client received welcome, assigned player_id: {self.player_id}")
        elif msg_type == 'pong':
            self.last_pong = time.time()
            print("Client received pong")
            
        if msg_type in self.message_handlers:
            self.message_handlers[msg_type](message)
            
    def send_message(self, message):
        if self.socket and self.server_address:
            try:
                data = json.dumps(message).encode('utf-8')
                
                send_address = list(self.server_address)
                if send_address[0] in ['localhost', '127.0.0.1']:
                    send_address[0] = '127.0.0.1'
                
                bytes_sent = self.socket.sendto(data, tuple(send_address))
                print(f"Client sent {bytes_sent} bytes to server: {message.get('type', 'unknown')}")
                return True
            except Exception as e:
                print(f"Client send error: {e}")
                return False
        return False
        
    def register_handler(self, message_type, handler):
        self.message_handlers[message_type] = handler
        
    def disconnect(self):
        print("Client disconnecting")
        self.running = False
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
    def send_player_update(self, player_data):
        self.send_message({
            'type': 'player_update',
            'data': player_data
        })
        
    def send_shoot(self, projectile_data):
        self.send_message({
            'type': 'shoot',
            'data': projectile_data
        })
        
    def is_connection_healthy(self):
        if not self.connected or not self.running:
            return False
            
        if self.enable_timeout_check:
            current_time = time.time()
            if self.last_pong > 0 and current_time - self.last_pong > self.connection_timeout:
                return False
            
        return True
        
    def check_connection_timeout(self):
        if not self.is_connection_healthy() and not self.connection_lost:
            print("Client connection timeout detected")
            self._handle_connection_lost()
            
    def enable_timeout_checking(self):
        self.enable_timeout_check = True
        
    def disable_timeout_checking(self):
        self.enable_timeout_check = False
