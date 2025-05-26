import pygame
import sys
import os
from pygame.locals import *

from constants import *
from simulation import TrafficSimulation
from renderer import Renderer

# Import the simple detector
try:
    from detector import SimplePhantomDetector
    DETECTOR_AVAILABLE = True
except ImportError:
    DETECTOR_AVAILABLE = False
    print("Install opencv-python for phantom detection")

def main():
    # Initialize pygame
    pygame.init()
    
    # Center the window on screen
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    
    # Set up the display
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Phantom Traffic Wave Simulator")
    clock = pygame.time.Clock()
    
    # Initialize simulation and renderer
    simulation = TrafficSimulation()
    renderer = Renderer(screen)
    
    # Initialize simple detector
    detector = SimplePhantomDetector() if DETECTOR_AVAILABLE else None
    
    running = True
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                running = handle_keydown(event, simulation, detector, running)
        
        # Update simulation
        simulation.update()
        
        # Render everything
        render_frame(screen, renderer, simulation)
        
        # Run simple detection
        if detector and not simulation.paused:
            result = detector.detect(screen)
            if result:
                print(f"PHANTOM TRAFFIC DETECTED! Check phantom_screenshots/ folder")
        
        # Cap the frame rate
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

def handle_keydown(event, simulation, detector, running):
    """Handle keyboard input"""
    if event.key == CONTROLS['QUIT']:
        return False
    elif event.key == CONTROLS['SWITCH_TRACK']:
        simulation.switch_track_type()
        if detector:
            detector.reset()  # Reset detector when switching tracks
    elif event.key == CONTROLS['PAUSE']:
        simulation.toggle_pause()
    elif event.key in CONTROLS['SPEED_UP']:
        simulation.adjust_speed(0.1)
    elif event.key == CONTROLS['SPEED_DOWN']:
        simulation.adjust_speed(-0.1)
    elif event.key == CONTROLS['RESET']:
        simulation.reset_simulation()
        if detector:
            detector.reset()  # Reset detector when resetting
    elif event.key == CONTROLS['BRAKE_EVENT']:
        simulation.trigger_random_brake_event()
    
    return running

def render_frame(screen, renderer, simulation):
    """Render a complete frame"""
    # Fill the background
    screen.fill(BACKGROUND_COLOR)
    
    # Draw the appropriate road
    if simulation.current_track_type == TRACK_TYPE_CIRCULAR:
        renderer.draw_circular_road()
    else:
        renderer.draw_straight_road()
    
    # Draw all cars in proper order
    sorted_cars = simulation.get_sorted_cars()
    for car in sorted_cars:
        renderer.draw_car(car)
    
    # Display brake alert if active
    renderer.display_brake_alert(simulation.brake_alert, simulation.brake_alert_timer)
    
    # Display information
    renderer.display_info(simulation.current_track_type, simulation.time_scale, simulation.paused)
    
    # Update the display
    pygame.display.flip()

if __name__ == "__main__":
    main()