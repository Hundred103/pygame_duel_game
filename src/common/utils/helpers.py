import math
import pygame
import os

def load_image(file_name, scale=1, convert_alpha=True):
    from src.config.settings import IMAGE_DIR
    
    try:
        path = os.path.join(IMAGE_DIR, file_name)
        if convert_alpha:
            img = pygame.image.load(path).convert_alpha()
        else:
            img = pygame.image.load(path).convert()
        
        if scale != 1:
            w, h = img.get_size()
            img = pygame.transform.scale(img, (int(w * scale), int(h * scale)))
        return img
    except pygame.error as e:
        print(f"Error loading image {file_name}: {e}")
        return pygame.Surface((32, 32))

def load_sound(file_name):
    from src.config.settings import SOUND_DIR
    
    try:
        path = os.path.join(SOUND_DIR, file_name)
        return pygame.mixer.Sound(path)
    except pygame.error as e:
        print(f"Error loading sound {file_name}: {e}")
        return None

def calculate_angle(pos1, pos2):
    dx = pos2[0] - pos1[0]
    dy = pos2[1] - pos1[1]
    return math.degrees(math.atan2(-dy, dx)) % 360

def distance(pos1, pos2):
    dx = pos2[0] - pos1[0]
    dy = pos2[1] - pos1[1]
    return math.sqrt(dx**2 + dy**2)

def get_direction_from_angle(angle):
    rad_angle = math.radians(angle)
    return math.cos(rad_angle), -math.sin(rad_angle)

def collision_point_rect(point, rect):
    return rect.collidepoint(point)
