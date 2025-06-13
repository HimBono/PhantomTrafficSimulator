# Constants for the traffic simulation
import pygame

# Screen dimensions
WIDTH, HEIGHT = 900, 700

# Road properties
ROAD_WIDTH = 200  
ROAD_CENTER_Y = HEIGHT // 2
TRACK_RADIUS = min(WIDTH, HEIGHT) // 3

# Car properties
CAR_WIDTH = 30
CAR_HEIGHT = 15  
NUM_CARS = 15  

# Colors
BACKGROUND_COLOR = (20, 80, 20)  
ROAD_COLOR = (50, 50, 50)
LINE_COLOR = (255, 255, 255)

# Physics
SPEED_LIMIT = 2.0  
# Circular road distances
CIRCULAR_SAFE_DISTANCE = 50
CIRCULAR_MIN_DISTANCE = 40
# Linear road distances
LINEAR_SAFE_DISTANCE = 35
LINEAR_MIN_DISTANCE = 25
ACCELERATION = 0.02  
DECELERATION = 0.08  
RANDOM_BRAKE_CHANCE = 0.0

# Track types
TRACK_TYPE_CIRCULAR = "circular"
TRACK_TYPE_STRAIGHT = "straight"

# Pygame keys for easy reference
CONTROLS = {
    'QUIT': pygame.K_ESCAPE,
    'SWITCH_TRACK': pygame.K_s,
    'TOGGLE_SPEED_INDICATOR': pygame.K_i,
    'TOGGLE_CAR_INFO': pygame.K_d,
    'PAUSE': pygame.K_SPACE,
    'SPEED_UP': [pygame.K_PLUS, pygame.K_EQUALS],
    'SPEED_DOWN': pygame.K_MINUS,
    'RESET': pygame.K_r,
    'BRAKE_EVENT': pygame.K_b
}