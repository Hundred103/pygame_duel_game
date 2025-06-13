import socket
import threading
import json
import time
import random
import string
import os

class GameServer:
    def __init__(self, host=None, port=0):
        if host is None:
            local_ip = self._get_local_ip_for_binding()
            self.host = '0.0.0.0' if local_ip and local_ip != '127.0.0.1' else 'localhost'
        else:
            self.host = host
        self.port = port
        self.socket = None
        self.running = False
        self.clients = {}
        self.client_counter = 0
        self.game_state = {'players': {}, 'projectiles': [], 'game_status': 'waiting'}
        self.server_code = None
        self.players_ready = False
        self.registry_file = "/tmp/duel_game_servers.json"
        
    def _get_local_ip_for_binding(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return '127.0.0.1'
        
    def _generate_server_code(self):
        actual_ip = self._get_local_ip()
        if actual_ip and actual_ip != '127.0.0.1':
            return self._encode_ip_to_code(actual_ip, self.port or 12345)
        else:
            return 'LOCL'
    
    def _get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return 'localhost'
    
    def _encode_ip_to_code(self, ip_address, port):
        try:
            print(f"Encoding IP: {ip_address}:{port}")
            if ip_address in ['localhost', '127.0.0.1']:
                print("Using LOCL for localhost")
                return 'LOCL'
            parts = ip_address.split('.')
            if len(parts) != 4:
                print("Invalid IP format, using LOCL")
                return 'LOCL'
            
            third_octet = int(parts[2])
            fourth_octet = int(parts[3])
            
            combined = (third_octet << 16) | (fourth_octet << 8) | (port & 0xFF)
            
            print(f"Combined value: {combined}")
            
            chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            code = ""
            temp = combined
            for _ in range(4):
                code = chars[temp % 36] + code
                temp //= 36
            print(f"Generated code: {code}")
            return code
        except Exception as e:
            print(f"Error encoding IP: {e}")
            return 'LOCL'
    def start(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind((self.host, self.port))
            if self.port == 0:
                self.port = self.socket.getsockname()[1]
            self.server_code = self._generate_server_code()
            self.running = True
            print(f"UDP Game server started on {self.host}:{self.port}")
            print(f"Server code: {self.server_code}")
            self._register_server()
            self._listen_for_messages()
        except Exception as e:
            print(f"Failed to start server: {e}")
            return False
            
    def _listen_for_messages(self):
        receive_thread = threading.Thread(target=self._receive_loop)
        receive_thread.daemon = True
        receive_thread.start()
        cleanup_thread = threading.Thread(target=self._cleanup_loop)
        cleanup_thread.daemon = True
        cleanup_thread.start()
        
    def _receive_loop(self):
        print("Server receive loop started")
        while self.running:
            try:
                self.socket.settimeout(1.0)
                data, address = self.socket.recvfrom(1024)
                print(f"Server received data from {address}: {data}")
                try:
                    message = json.loads(data.decode('utf-8'))
                    print(f"Server parsed message: {message}")
                    self._handle_message(message, address)
                except json.JSONDecodeError:
                    print(f"Server: Invalid JSON from {address}: {data}")
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Server receive error: {e}")
        print("Server receive loop ended")
        
    def _cleanup_loop(self):
        while self.running:
            current_time = time.time()
            inactive_clients = []
            for client_id, (address, last_seen) in self.clients.items():
                if current_time - last_seen > 10.0:
                    inactive_clients.append(client_id)
            for client_id in inactive_clients:
                self._disconnect_client(client_id)
            time.sleep(5.0)
    def _handle_message(self, message, address):
        msg_type = message.get('type')
        current_time = time.time()
        client_id = None
        for cid, (addr, _) in self.clients.items():
            if addr == address:
                client_id = cid
                break
        if msg_type == 'connect':
            if client_id is None and len(self.clients) < 2:
                client_id = self.client_counter
                self.client_counter += 1
                self.clients[client_id] = (address, current_time)
                print(f"Client {client_id} connected from {address}")
                welcome_msg = {'type': 'welcome', 'player_id': client_id, 'server_code': self.server_code}
                self._send_to_address(address, welcome_msg)
                if len(self.clients) == 2 and not self.players_ready:
                    self.players_ready = True
                    self.game_state['game_status'] = 'playing'
                    self._broadcast({'type': 'game_start'})
            elif client_id is not None:
                self.clients[client_id] = (address, current_time)
        elif client_id is not None:
            self.clients[client_id] = (address, current_time)
            if msg_type == 'player_update':
                self.game_state['players'][client_id] = message.get('data', {})
                self._broadcast_to_others(client_id, message)
            elif msg_type in ['player_input', 'game_state_update', 'countdown_start', 'countdown_cancel', 'restart_request', 'return_to_lobby', 'return_to_main_menu', 'ready_ping', 'ready_pong']:
                self._broadcast(message)
            elif msg_type == 'shoot':
                self._broadcast_to_others(client_id, message)
            elif msg_type == 'ping':
                self._send_to_address(address, {'type': 'pong'})
    def _send_to_address(self, address, message):
        try:
            data = json.dumps(message).encode('utf-8')
            bytes_sent = self.socket.sendto(data, address)
            print(f"Server sent {bytes_sent} bytes to {address}: {message.get('type', 'unknown')}")
            print(f"Message content: {message}")
        except Exception as e:
            print(f"Error sending to {address}: {e}")
            
    def _broadcast(self, message):
        for client_id, (address, _) in list(self.clients.items()):
            self._send_to_address(address, message)
            
    def _broadcast_to_others(self, sender_id, message):
        for client_id, (address, _) in list(self.clients.items()):
            if client_id != sender_id:
                self._send_to_address(address, message)
                
    def _disconnect_client(self, client_id):
        if client_id in self.clients:
            address = self.clients[client_id][0]
            del self.clients[client_id]
            print(f"Client {client_id} at {address} disconnected due to timeout")
            if self.players_ready:
                self.players_ready = False
                self.game_state['game_status'] = 'waiting'
                print("Game state reset due to client disconnection")
            self._broadcast({'type': 'player_disconnected', 'player_id': client_id, 'reason': 'timeout'})
            print(f"Remaining clients: {len(self.clients)}")
            
    def stop(self):
        self.running = False
        self._unregister_server()
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        print("UDP Server stopped")
    def _register_server(self):
        try:
            registry = {}
            if os.path.exists(self.registry_file):
                try:
                    with open(self.registry_file, 'r') as f:
                        registry = json.load(f)
                except:
                    registry = {}
            actual_ip = self._get_local_ip()
            registry_host = actual_ip if actual_ip != 'localhost' else 'localhost'
            registry[self.server_code] = {'host': registry_host, 'port': self.port, 'timestamp': time.time()}
            os.makedirs(os.path.dirname(self.registry_file), exist_ok=True)
            with open(self.registry_file, 'w') as f:
                json.dump(registry, f)
            print(f"Server registered with code {self.server_code} on {registry_host}:{self.port}")
        except Exception as e:
            print(f"Failed to register server: {e}")
            
    def _unregister_server(self):
        try:
            if os.path.exists(self.registry_file):
                with open(self.registry_file, 'r') as f:
                    registry = json.load(f)
                if self.server_code in registry:
                    del registry[self.server_code]
                    with open(self.registry_file, 'w') as f:
                        json.dump(registry, f)
        except Exception as e:
            print(f"Failed to unregister server: {e}")
        
    def get_server_info(self):
        actual_ip = self._get_local_ip()
        return {'host': actual_ip if actual_ip != 'localhost' else self.host, 'port': self.port, 'code': self.server_code, 'clients': len(self.clients), 'ready': self.players_ready}
        
    def is_game_ready(self):
        return len(self.clients) >= 2
