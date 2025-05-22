import math
import random
import pygame
from constants import *

def get_car_color(speed, max_speed):
    """Return car color based on speed (Red=slow, Green=fast)"""
    if speed < 0.2 * max_speed:
        return (255, 0, 0)  # Red - very slow
    elif speed < 0.5 * max_speed:
        return (255, 165, 0)  # Orange - slow
    elif speed < 0.8 * max_speed:
        return (255, 255, 0)  # Yellow - moderate
    else:
        return (0, 255, 0)    # Green - fast

class Car:
    def __init__(self, position, angle=0, speed=None):
        self.position = position  # For circular: angle in radians, for straight: x-position
        self.angle = angle
        
        # All cars start at exactly the same speed
        self.speed = speed if speed is not None else SPEED_LIMIT * 0.9
        self.desired_speed = SPEED_LIMIT
        
        self.x = 0  # Will be calculated in update
        self.y = 0  # Will be calculated in update
        self.braking = False
        self.color = get_car_color(self.speed, SPEED_LIMIT)
        self.id = random.randint(100, 999)
        
        # Uniform behavior for all cars
        self.aggressiveness = 1.0
        self.reaction_time = 1.0
        
        # For manual braking events
        self.brake_duration = 0
        self.brake_cooldown = 0
        
    def update(self, cars, track_type, paused, time_scale):
        """Update car position and behavior"""
        # Update brake cooldown
        if self.brake_cooldown > 0:
            self.brake_cooldown -= 1
            
        # Handle braking events
        if self.brake_duration > 0:
            self.brake_duration -= 1
            self.braking = True
        else:
            # Random chance of braking (only if not on cooldown)
            if random.random() < RANDOM_BRAKE_CHANCE and not paused and self.brake_cooldown <= 0:
                self.brake_duration = random.randint(15, 30)
                self.brake_cooldown = 200
                self.braking = True
            else:
                self.braking = False
        
        # Find the car ahead
        next_car = None
        min_distance = float('inf')
        
        if track_type == TRACK_TYPE_CIRCULAR:
            for car in cars:
                if car != self:
                    distance = (car.position - self.position) % (2 * math.pi)
                    if 0 < distance < min_distance:
                        min_distance = distance
                        next_car = car
            
            if next_car:
                min_distance = min_distance * TRACK_RADIUS
        else:  # TRACK_TYPE_STRAIGHT
            for car in cars:
                if car != self:
                    distance = (car.position - self.position) % WIDTH
                    if 0 < distance < min_distance:
                        min_distance = distance
                        next_car = car
        
        # Apply driving behavior
        self._apply_driving_behavior(next_car, min_distance, paused)
        
        # Update position
        self._update_position(cars, track_type, paused, time_scale)
        
        # Update car color based on speed
        self.color = get_car_color(self.speed, SPEED_LIMIT)
    
    def _apply_driving_behavior(self, next_car, min_distance, paused):
        """Apply car following and braking behavior"""
        # Collision prevention - emergency braking if too close
        if next_car and min_distance < MIN_DISTANCE and not paused:
            self.speed = max(0, self.speed - DECELERATION * 3)
            self.braking = True
        # Normal driving behavior
        elif next_car and not paused:
            safe_dist = max(SAFE_DISTANCE, self.speed * 8 / self.aggressiveness)
            
            if min_distance < safe_dist:
                # Too close, slow down
                decel = DECELERATION * (1 + (safe_dist - min_distance) / safe_dist) * self.reaction_time
                self.speed = max(0.1, self.speed - decel)
                self.braking = True
            elif self.speed < self.desired_speed and min_distance > safe_dist * 1.5:
                # Far enough to accelerate
                self.speed = min(self.desired_speed, self.speed + ACCELERATION)
                self.braking = False
        elif not paused:
            # No car ahead, accelerate to desired speed
            if self.speed < self.desired_speed:
                self.speed = min(self.desired_speed, self.speed + ACCELERATION)
            elif self.speed > self.desired_speed:
                self.speed = max(self.desired_speed, self.speed - ACCELERATION / 2)
            self.braking = False
        
        # Force braking if brake duration is active
        if self.brake_duration > 0 and not paused:
            self.speed = max(0.1, self.speed - DECELERATION * 1.5)
    
    def _update_position(self, cars, track_type, paused, time_scale):
        """Update car position with collision checking"""
        # Calculate next position
        next_position = self.position
        if not paused:
            if track_type == TRACK_TYPE_CIRCULAR:
                next_position = (self.position + self.speed / TRACK_RADIUS * time_scale) % (2 * math.pi)
            else:
                next_position = (self.position + self.speed * time_scale) % WIDTH
        
        # Check for collisions
        would_collide = self._would_collide(cars, next_position, track_type)
        
        # Update position if no collision
        if not would_collide and not paused:
            self.position = next_position
        elif would_collide and not paused:
            self.speed = 0
            self.braking = True
        
        # Update screen coordinates
        self._update_screen_coordinates(track_type)
    
    def _would_collide(self, cars, next_position, track_type):
        """Check if moving to next_position would cause a collision"""
        for car in cars:
            if car != self:
                if track_type == TRACK_TYPE_CIRCULAR:
                    next_dist = min(
                        abs((next_position - car.position) % (2 * math.pi)),
                        abs((car.position - next_position) % (2 * math.pi))
                    ) * TRACK_RADIUS
                else:
                    next_dist = min(
                        abs((next_position - car.position) % WIDTH),
                        abs((car.position - next_position) % WIDTH)
                    )
                
                if next_dist < MIN_DISTANCE:
                    return True
        return False
    
    def _update_screen_coordinates(self, track_type):
        """Update x, y coordinates for rendering"""
        if track_type == TRACK_TYPE_CIRCULAR:
            self.x = WIDTH // 2 + math.cos(self.position) * TRACK_RADIUS
            self.y = HEIGHT // 2 + math.sin(self.position) * TRACK_RADIUS
            self.angle = self.position + math.pi / 2
        else:
            self.x = self.position
            self.y = ROAD_CENTER_Y
            self.angle = 0
    
    def trigger_brake_event(self):
        """Manually trigger a brake event"""
        if self.brake_duration == 0 and self.brake_cooldown == 0:
            self.brake_duration = random.randint(30, 45)
            self.brake_cooldown = 120
            self.speed *= 0.3
            return True
        return False