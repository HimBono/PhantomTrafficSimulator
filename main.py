import pygame
import sys
import os
from pygame.locals import *

from constants import *
from simulation import TrafficSimulation
from renderer import Renderer
from telemetry import TelemetryLogger

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
    
    # Initialize telemetry logger
    telemetry = TelemetryLogger()
    
    # Log initial session start
    telemetry.log_event('session_start', {
        'num_cars': NUM_CARS,
        'speed_limit': SPEED_LIMIT,
        'initial_track': simulation.current_track_type
    })
    
    # Initialize simple detector
    detector = SimplePhantomDetector() if DETECTOR_AVAILABLE else None
    
    running = True
    frame_count = 0
    
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                running = handle_keydown(event, simulation, telemetry, detector, running)
        
        # Update simulation
        simulation.update()
        
        # Get traffic stats
        traffic_stats = simulation.get_traffic_stats()
        
        # Log telemetry data every frame
        simulation_state = {
            'track_type': simulation.current_track_type,
            'time_scale': simulation.time_scale,
            'paused': simulation.paused,
            'speed_limit': SPEED_LIMIT
        }
        telemetry.log_frame_data(simulation_state, simulation.cars, traffic_stats)
        
        # Render everything
        render_frame(screen, renderer, simulation, telemetry)
        
        frame_count += 1
        
        # Run simple detection
        if detector and not simulation.paused:
            result = detector.detect(screen)
            if result:
                print(f"PHANTOM TRAFFIC DETECTED! Check phantom_screenshots/ folder")
        
        # Cap the frame rate
        clock.tick(60)
    
    # Close telemetry session
    telemetry.close_session()
    
    pygame.quit()
    sys.exit()

def handle_keydown(event, simulation, telemetry, detector, running):
    """Handle keyboard input with telemetry logging"""
    if event.key == CONTROLS['QUIT']:
        return False
    elif event.key == CONTROLS['SWITCH_TRACK']:
        old_track = simulation.current_track_type
        simulation.switch_track_type()
        telemetry.log_track_switch(old_track, simulation.current_track_type)
        if detector:
            detector.reset()  # Reset detector when switching tracks
    elif event.key == CONTROLS['PAUSE']:
        simulation.toggle_pause()
        telemetry.log_simulation_control('pause' if simulation.paused else 'resume')
    elif event.key in CONTROLS['SPEED_UP']:
        old_speed = simulation.time_scale
        simulation.adjust_speed(0.1)
        telemetry.log_simulation_control('speed_increase', {
            'old_speed': old_speed,
            'new_speed': simulation.time_scale
        })
    elif event.key == CONTROLS['SPEED_DOWN']:
        old_speed = simulation.time_scale
        simulation.adjust_speed(-0.1)
        telemetry.log_simulation_control('speed_decrease', {
            'old_speed': old_speed,
            'new_speed': simulation.time_scale
        })
    elif event.key == CONTROLS['RESET']:
        simulation.reset_simulation()
        telemetry.log_simulation_control('reset')
        if detector:
            detector.reset()  # Reset detector when resetting
    elif event.key == CONTROLS['BRAKE_EVENT']:
        car_id = simulation.trigger_random_brake_event()
        if car_id:
            # Find the car that braked to get its position
            braking_car = next((car for car in simulation.cars if car.id == car_id), None)
            if braking_car:
                telemetry.log_brake_event(car_id, braking_car.position, 'manual')
    
    return running

def render_frame(screen, renderer, simulation, telemetry):
    """Render a complete frame with telemetry info"""
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
    
    # Display information including telemetry stats
    renderer.display_info(simulation.current_track_type, simulation.time_scale, 
                         simulation.paused, telemetry.get_session_stats())
    
    # Update the display
    pygame.display.flip()

if __name__ == "__main__":
    main()