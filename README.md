# Duel Game - LAN Multiplayer 2D Shooter

A real-time multiplayer 2D top-down shooter game built with Pygame featuring LAN multiplayer support, automatic IP encoding, and synchronized gameplay.

## 🚀 Features

- **LAN Multiplayer**: Automatic IP address encoding into 4-character codes for easy connection
- **Real-time Gameplay**: UDP-based networking with 30 FPS synchronization
- **Game Timer**: 5-minute countdown timer with automatic score-based winner determination
- **Pause System**: Synchronized pause/resume functionality between host and client
- **Ready Check**: 1-second connection validation before game start
- **Clean Architecture**: Minimized codebase with 35-45% line reduction while maintaining full functionality

## 🎮 How to Play

### Host a Game
1. Run `python main.py`
2. Select "Host Game"
3. Share the 4-character code with another player
4. Wait for player to connect, then press SPACE to start

### Join a Game
1. Run `python main.py`
2. Select "Join Game"
3. Enter the 4-character code from the host
4. Wait for the game to start

### Game Controls
- **WASD**: Move player
- **Arrow Keys**: Rotate/aim
- **SPACE**: Shoot
- **P**: Pause (both players can pause)
- **ESC**: Toggle pause menu

## 🛠️ Installation

### Prerequisites
- Python 3.7+
- pygame

### Setup
1. Clone the repository
```bash
git clone https://github.com/yourusername/duel-game.git
cd duel-game
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Run the game
```bash
python main.py
```

## 🌐 Network Features

### IP Encoding System
- **Localhost**: Uses code `LOCL`
- **LAN IPs**: Automatically encoded into 4-character alphanumeric codes
- **Auto-detection**: Server automatically detects local IP and binds appropriately

### Connection Codes
- Share the 4-character code displayed when hosting
- Codes automatically resolve to correct IP addresses on the same network
- Supports common router IP ranges (192.168.x.x, 10.0.x.x, etc.)

## 🏗️ Project Structure
├── assets/           # Game assets
│   ├── images/       # Game sprites, backgrounds, etc.
│   ├── sounds/       # Sound effects and music
│   └── fonts/        # Font files
├── src/              # Source code
│   ├── client/       # Client-specific code
│   │   ├── graphics/ # Client-side rendering code
│   │   └── input/    # Player input handling
│   ├── server/       # Host-specific code
│   │   └── game_logic/ # Game rules and mechanics
│   ├── network/      # Network communication code (UDP)
│   ├── common/       # Shared code between client and server
│   │   ├── entities/ # Game entities (players, bullets, etc.)
│   │   └── utils/    # Utility functions
│   └── config/       # Configuration files
└── tests/            # Test files
```

## Game Overview

This is a 2D topdown shooter game where two players can play against each other. One player acts as the host, and the other connects as a client. The game uses UDP for network communication.

## Requirements

- Python 3.x
- Pygame

## How to Run

*Instructions for running the game will be provided in future updates.*
