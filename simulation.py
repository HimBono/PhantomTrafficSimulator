import random
import math
from car import Car
from constants import *

class TrafficSimulation:
    def __init__(self):
        self.cars = []
        self.current_track_type = TRACK_TYPE_CIRCULAR
        self.paused = False
        self.time_scale = 1.0
        self.avg_speed_history = []
        self.brake_alert = None
        self.brake_alert_timer = 0
        
        # Initialize cars
        self.reset_simulation()
    
    def init_cars(self, track_type):
        """Initialize cars based on track type"""
        cars = []
        
        if track_type == TRACK_TYPE_CIRCULAR:
            # Place cars evenly around the circle
            for i in range(NUM_CARS):
                position = i * (2 * math.pi / NUM_CARS)
                initial_speed = SPEED_LIMIT * 0.6
                cars.append(Car(position, speed=initial_speed))
        else:  # TRACK_TYPE_STRAIGHT
            # Place cars evenly along the road
            for i in range(NUM_CARS):
                position = i * (WIDTH / NUM_CARS)
                initial_speed = SPEED_LIMIT * 0.6
                cars.append(Car(position, angle=0, speed=initial_speed))
        
        return cars
    
    def reset_simulation(self):
        """Reset the simulation to initial state"""
        self.cars = self.init_cars(self.current_track_type)
        self.paused = False
        self.time_scale = 1.0
        self.avg_speed_history = []
        self.brake_alert = None
        self.brake_alert_timer = 0
    
    def switch_track_type(self):
        """Switch between circular and straight track"""
        self.current_track_type = (TRACK_TYPE_STRAIGHT if self.current_track_type == TRACK_TYPE_CIRCULAR 
                                  else TRACK_TYPE_CIRCULAR)
        self.cars = self.init_cars(self.current_track_type)
        self.brake_alert = None
    
    def toggle_pause(self):
        """Pause/Resume simulation"""
        self.paused = not self.paused
    
    def adjust_speed(self, delta):
        """Adjust simulation speed"""
        self.time_scale = max(0.1, min(3.0, self.time_scale + delta))
    
    def trigger_random_brake_event(self):
        """Trigger a random brake event on an available car"""
        if self.cars:
            # Find cars that aren't already braking and don't have active cooldowns
            available_cars = [car for car in self.cars 
                            if car.brake_duration == 0 and car.brake_cooldown == 0]
            if available_cars:
                # Choose a random car
                brake_car = random.choice(available_cars)
                if brake_car.trigger_brake_event():
                    print(f"Car {brake_car.id} is braking")
                    # Could add brake alert here if desired
                    # self.brake_alert = f"Car {brake_car.id} braked suddenly!"
                    # self.brake_alert_timer = 180
                    return brake_car.id
        return None
    
    def update(self):
        """Update the simulation state"""
        # Update brake alert timer
        if self.brake_alert_timer > 0:
            self.brake_alert_timer -= 1
            if self.brake_alert_timer <= 0:
                self.brake_alert = None
        
        # Update all cars
        for car in self.cars:
            car.update(self.cars, self.current_track_type, self.paused, self.time_scale)
        
        # Track average speed for analysis
        if not self.paused and len(self.cars) > 0:
            avg_speed = sum(car.speed for car in self.cars) / len(self.cars)
            self.avg_speed_history.append(avg_speed)
            # Keep history to a reasonable size
            if len(self.avg_speed_history) > 500:
                self.avg_speed_history.pop(0)
    
    def get_sorted_cars(self):
        """Get cars sorted by position for proper drawing order"""
        if self.current_track_type == TRACK_TYPE_STRAIGHT:
            return sorted(self.cars, key=lambda c: c.position)
        else:
            return sorted(self.cars, key=lambda c: c.position)
    
    def get_traffic_stats(self):
        """Get current traffic statistics"""
        if not self.cars:
            return None
        
        avg_speed = sum(car.speed for car in self.cars) / len(self.cars)
        flow_percentage = (avg_speed / SPEED_LIMIT) * 100
        
        return {
            'avg_speed': avg_speed,
            'flow_percentage': flow_percentage,
            'num_braking': sum(1 for car in self.cars if car.braking),
            'congested': flow_percentage < 85
        }