# Duel Game - 2D Topdown Shooter

A multiplayer 2D topdown shooter game built with Pygame using a host-client architecture over UDP.

## Project Structure

```
duel_game/
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
