import pygame
import math
from constants import *

class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont(None, 20)
    
    def draw_straight_road(self):
        """Draw a straight road with lane markings"""
        # Draw road
        pygame.draw.rect(self.screen, ROAD_COLOR, 
                        (0, ROAD_CENTER_Y - ROAD_WIDTH // 2, WIDTH, ROAD_WIDTH))
        
        # Draw center line
        pygame.draw.line(self.screen, LINE_COLOR, 
                        (0, ROAD_CENTER_Y), (WIDTH, ROAD_CENTER_Y), 2)
        
        # Draw dashed side lines
        for i in range(0, WIDTH, 30):
            pygame.draw.line(self.screen, LINE_COLOR, 
                           (i, ROAD_CENTER_Y - ROAD_WIDTH // 4), 
                           (i + 15, ROAD_CENTER_Y - ROAD_WIDTH // 4), 2)
            pygame.draw.line(self.screen, LINE_COLOR, 
                           (i, ROAD_CENTER_Y + ROAD_WIDTH // 4), 
                           (i + 15, ROAD_CENTER_Y + ROAD_WIDTH // 4), 2)

    def draw_circular_road(self):
        """Draw a circular road with lane markings"""
        # Draw outer circle
        pygame.draw.circle(self.screen, ROAD_COLOR, 
                          (WIDTH // 2, HEIGHT // 2), 
                          TRACK_RADIUS + ROAD_WIDTH // 4, ROAD_WIDTH // 2)
        
        # Draw center circle
        pygame.draw.circle(self.screen, LINE_COLOR, 
                          (WIDTH // 2, HEIGHT // 2), TRACK_RADIUS, 2)
        
        # Draw dashed inner and outer circles
        for i in range(0, 360, 10):
            angle_start = math.radians(i)
            angle_end = math.radians(i + 5)
            
            # Inner dashed circle
            inner_start = (
                WIDTH // 2 + math.cos(angle_start) * (TRACK_RADIUS - ROAD_WIDTH // 4),
                HEIGHT // 2 + math.sin(angle_start) * (TRACK_RADIUS - ROAD_WIDTH // 4)
            )
            inner_end = (
                WIDTH // 2 + math.cos(angle_end) * (TRACK_RADIUS - ROAD_WIDTH // 4),
                HEIGHT // 2 + math.sin(angle_end) * (TRACK_RADIUS - ROAD_WIDTH // 4)
            )
            pygame.draw.line(self.screen, LINE_COLOR, inner_start, inner_end, 2)
            
            # Outer dashed circle
            outer_start = (
                WIDTH // 2 + math.cos(angle_start) * (TRACK_RADIUS + ROAD_WIDTH // 4),
                HEIGHT // 2 + math.sin(angle_start) * (TRACK_RADIUS + ROAD_WIDTH // 4)
            )
            outer_end = (
                WIDTH // 2 + math.cos(angle_end) * (TRACK_RADIUS + ROAD_WIDTH // 4),
                HEIGHT // 2 + math.sin(angle_end) * (TRACK_RADIUS + ROAD_WIDTH // 4)
            )
            pygame.draw.line(self.screen, LINE_COLOR, outer_start, outer_end, 2)

    def draw_car(self, car):
        """Draw a car with rotation and brake lights"""
        # Create a car surface
        car_surface = pygame.Surface((CAR_WIDTH, CAR_HEIGHT), pygame.SRCALPHA)
        
        # Draw car body
        pygame.draw.rect(car_surface, car.color, (0, 0, CAR_WIDTH, CAR_HEIGHT), border_radius=3)
        
        # Draw car details (windows, etc.)
        pygame.draw.rect(car_surface, (0, 0, 0), 
                        (CAR_WIDTH - 10, 3, 7, CAR_HEIGHT - 6), border_radius=1)
        
        # Draw brake lights if braking
        if car.braking:
            pygame.draw.rect(car_surface, (255, 0, 0), (0, 3, 4, 4), border_radius=1)
            pygame.draw.rect(car_surface, (255, 0, 0), (0, CAR_HEIGHT - 7, 4, 4), border_radius=1)
        
        # Rotate the car surface
        rotated_car = pygame.transform.rotate(car_surface, -math.degrees(car.angle))
        car_rect = rotated_car.get_rect(center=(car.x, car.y))
        
        # Draw car
        self.screen.blit(rotated_car, car_rect)

    def display_info(self, current_track_type, time_scale, paused):
        """Display controls and current settings"""
        # Display controls
        controls = [
            "Controls:",
            "S - Switch track (Straight/Circular)",
            "Space - Pause/Resume",
            "+/- - Adjust simulation speed",
            "R - Reset simulation",
            "B - Trigger random brake event",
            "Esc - Quit"
        ]
        
        # Create a semi-transparent background
        info_surface = pygame.Surface((250, len(controls) * 22 + 10), pygame.SRCALPHA)
        info_surface.fill((0, 0, 0, 150))
        self.screen.blit(info_surface, (5, 5))
        
        for i, text in enumerate(controls):
            text_surface = self.font.render(text, True, (255, 255, 255))
            self.screen.blit(text_surface, (10, 10 + i * 22))
        
        # Display current settings
        settings = [
            f"Track: {'Circular' if current_track_type == TRACK_TYPE_CIRCULAR else 'Straight'}",
            f"Speed: {time_scale:.1f}x",
            f"Cars: {NUM_CARS}",
            f"Max Speed: {SPEED_LIMIT:.1f}",
            f"Status: {'Paused' if paused else 'Running'}"
        ]
        
        # Create settings background
        settings_surface = pygame.Surface((160, len(settings) * 20 + 10), pygame.SRCALPHA)
        settings_surface.fill((0, 0, 0, 150))
        self.screen.blit(settings_surface, (WIDTH - 165, 5))
        
        for i, text in enumerate(settings):
            text_surface = self.font.render(text, True, (255, 255, 255))
            self.screen.blit(text_surface, (WIDTH - 160, 10 + i * 20))
            
        # Display legend
        self._display_legend()
    
    def _display_legend(self):
        """Display color legend for car speeds"""
        legend = [
            "Color Legend:",
            "Red = Stopped/Very Slow",
            "Orange = Slow",
            "Yellow = Medium Speed",
            "Green = Full Speed"
        ]
        
        # Create legend background
        legend_surface = pygame.Surface((160, len(legend) * 20 + 10), pygame.SRCALPHA)
        legend_surface.fill((0, 0, 0, 150))
        self.screen.blit(legend_surface, (WIDTH - 165, HEIGHT - len(legend) * 20 - 15))
        
        # Legend title
        text_surface = self.font.render(legend[0], True, (255, 255, 255))
        self.screen.blit(text_surface, (WIDTH - 160, HEIGHT - len(legend) * 20 - 5))
        
        # Legend color items
        colors = [(255, 0, 0), (255, 165, 0), (255, 255, 0), (0, 255, 0)]
        for i in range(1, len(legend)):
            # Draw color sample
            pygame.draw.rect(self.screen, colors[i-1], 
                           (WIDTH - 160, HEIGHT - (len(legend) - i) * 20 - 5, 10, 10))
            # Draw text
            text_surface = self.font.render(legend[i], True, (255, 255, 255))
            self.screen.blit(text_surface, (WIDTH - 145, HEIGHT - (len(legend) - i) * 20 - 5))

    def display_brake_alert(self, brake_alert, brake_alert_timer):
        """Display brake event alert"""
        if brake_alert and brake_alert_timer > 0:
            font = pygame.font.SysFont(None, 24)
            alert_surf = font.render(brake_alert, True, (255, 0, 0))
            
            # Create transparent background
            alert_bg = pygame.Surface((alert_surf.get_width() + 20, alert_surf.get_height() + 10), 
                                    pygame.SRCALPHA)
            alert_bg.fill((0, 0, 0, 180))
            
            # Display alert
            self.screen.blit(alert_bg, (WIDTH // 2 - alert_surf.get_width() // 2 - 10, HEIGHT // 4 - 20))
            self.screen.blit(alert_surf, (WIDTH // 2 - alert_surf.get_width() // 2, HEIGHT // 4 - 15))