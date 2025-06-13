SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TITLE = "Duel Game"
FPS = 120

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

TILE_SIZE = 32

PLAYER_SPEED = 180
PLAYER_HEALTH = 100

PROJECTILE_SPEED = 420
PROJECTILE_LIFETIME = 2000
PROJECTILE_DAMAGE = 10
FIRE_COOLDOWN = 500

MAP_1 = [
    "WWWWWWWWWWWWWWWWWWWWWWWWW",
    "W.......................W",
    "W.P...B.................W",
    "WB......................W",
    "W........WWW............W",
    "W........W..............W",
    "W........W..............W",
    "W.......................W",
    "W.......................W",
    "W.......................W",
    "W.............B.........W",
    "W.......................W",
    "W...........WW..........W",
    "W...........WW..........W",
    "W.......................W",
    "W.....B................BW",
    "W....................O..W",
    "W.......................W",
    "WWWWWWWWWWWWWWWWWWWWWWWWW",
]

ASSET_DIR = "assets"
IMAGE_DIR = f"{ASSET_DIR}/images"
SOUND_DIR = f"{ASSET_DIR}/sounds"
FONT_DIR = f"{ASSET_DIR}/fonts"

MENU = 0
PLAYING = 1
GAME_OVER = 2

POINTS_TO_WIN = 10
POINTS_PER_ELIMINATION = 1

RESPAWN_DELAY = 3000
MIN_SPAWN_DISTANCE_FROM_WALLS = 2
MIN_SPAWN_DISTANCE_FROM_ENEMY = 10

GAME_TIMER_DURATION = 1000

MAX_PLAYERS = 2
PLAYER_BLUE = 0
PLAYER_RED = 1
