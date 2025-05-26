import cv2
import numpy as np
import pygame
import os
from datetime import datetime

class SimplePhantomDetector:
    def __init__(self):
        # Create output directory
        os.makedirs("phantom_screenshots", exist_ok=True)
        
        # Detection state
        self.baseline_established = False
        self.car_positions = []
        self.car_speeds = []
        self.baseline_speed = 0
        self.frames_analyzed = 0
        self.detection_made = False
        self.track_type = "unknown"
        
        # Improved parameters
        self.min_frames_for_baseline = 90   # 1.5 seconds for baseline
        self.speed_drop_threshold = 0.6     # Must drop to 60% of baseline (more sensitive)
        self.min_baseline_speed = 1.0       # Lower minimum speed requirement
        self.stable_frames_needed = 10      # Only 10 frames (0.16 seconds) of slow speed
        
        # Track car stability
        self.car_stability_count = {}
        
        print("Simple Phantom Detector initialized")
    
    def detect(self, screen_surface):
        """Main detection function - analyzes screen for phantom traffic"""
        if self.detection_made:
            return None
            
        # Convert pygame surface to opencv
        frame = self._pygame_to_cv2(screen_surface)
        
        # Find yellow cars
        cars = self._find_cars(frame)
        
        if len(cars) < 5:  # Need enough cars for reliable detection
            return None
        
        # Determine track type
        self.track_type = self._determine_track_type(cars, frame)
        
        # Calculate car speeds
        if len(self.car_positions) > 0:
            speeds = self._calculate_speeds(cars, self.car_positions[-1])
        else:
            speeds = [0] * len(cars)
        
        self.car_positions.append(cars)
        self.car_speeds.append(speeds)
        self.frames_analyzed += 1
        
        # Keep only recent history
        if len(self.car_positions) > 20:
            self.car_positions.pop(0)
            self.car_speeds.pop(0)
        
        # Establish baseline after enough frames
        if not self.baseline_established and self.frames_analyzed >= self.min_frames_for_baseline:
            self.baseline_speed = self._calculate_baseline_speed()
            if self.baseline_speed >= self.min_baseline_speed:
                self.baseline_established = True
                print(f"Baseline established: {self.baseline_speed:.2f} pixels/frame on {self.track_type} track")
            else:
                print(f"Baseline too low ({self.baseline_speed:.2f}), waiting for cars to move...")
            return None
        
        if not self.baseline_established:
            return None
        
        # Check for phantom traffic with improved logic
        phantom_car = self._detect_phantom_car_improved(speeds, cars)
        
        if phantom_car is not None:
            self._save_detection(frame, phantom_car, self.track_type)
            self.detection_made = True
            return phantom_car
        
        return None
    
    def _pygame_to_cv2(self, pygame_surface):
        """Convert pygame surface to opencv format"""
        w, h = pygame_surface.get_size()
        raw = pygame.image.tostring(pygame_surface, 'RGB')
        image = np.frombuffer(raw, dtype=np.uint8).reshape((h, w, 3))
        return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    
    def _find_cars(self, frame):
        """Find yellow cars in the frame"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Broader yellow color range for better detection
        lower_yellow = np.array([15, 80, 80])
        upper_yellow = np.array([35, 255, 255])
        
        mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
        
        # Clean up the mask
        kernel = np.ones((3,3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        cars = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if 150 < area < 3000:  # Broader area range
                x, y, w, h = cv2.boundingRect(contour)
                center_x = x + w // 2
                center_y = y + h // 2
                cars.append((center_x, center_y, area))
        
        # Sort cars by position for consistent tracking
        if self.track_type == "circular":
            # Sort by angle from center
            center_x, center_y = frame.shape[1] // 2, frame.shape[0] // 2
            cars.sort(key=lambda car: np.arctan2(car[1] - center_y, car[0] - center_x))
        else:
            # Sort by x position for linear
            cars.sort(key=lambda car: car[0])
        
        return cars
    
    def _determine_track_type(self, cars, frame):
        """Determine if track is circular or linear based on car positions"""
        if len(cars) < 5:
            return self.track_type  # Keep previous type if not enough cars
        
        # Check if cars form a circle
        center_x, center_y = frame.shape[1] // 2, frame.shape[0] // 2
        distances = []
        
        for car_x, car_y, _ in cars:
            dist = ((car_x - center_x) ** 2 + (car_y - center_y) ** 2) ** 0.5
            distances.append(dist)
        
        if len(distances) > 0:
            avg_dist = sum(distances) / len(distances)
            variance = sum((d - avg_dist) ** 2 for d in distances) / len(distances)
            
            # Check if cars are roughly equidistant from center
            if variance < 2000 and avg_dist > 100:  # Circular pattern
                return "circular"
        
        # Check if cars are in a line (linear track)
        y_positions = [car[1] for car in cars]
        y_variance = np.var(y_positions)
        
        if y_variance < 500:  # Cars are roughly on same horizontal line
            return "linear"
        
        return "unknown"
    
    def _calculate_speeds(self, current_cars, previous_cars):
        """Calculate speed of each car between frames with better matching"""
        speeds = []
        
        for i, curr_car in enumerate(current_cars):
            curr_x, curr_y, _ = curr_car
            
            # For circular track, look for car in similar position
            if self.track_type == "circular":
                # Match by index (cars maintain relative positions)
                if i < len(previous_cars):
                    prev_x, prev_y, _ = previous_cars[i]
                    # Calculate arc distance for circular movement
                    dx = curr_x - prev_x
                    dy = curr_y - prev_y
                    speed = (dx ** 2 + dy ** 2) ** 0.5
                    speeds.append(speed)
                else:
                    speeds.append(0)
            else:
                # For linear track, match by proximity
                min_dist = float('inf')
                matched_speed = 0
                
                for prev_car in previous_cars:
                    prev_x, prev_y, _ = prev_car
                    dist = ((curr_x - prev_x) ** 2 + (curr_y - prev_y) ** 2) ** 0.5
                    if dist < min_dist and dist < 100:  # Reasonable matching distance
                        min_dist = dist
                        matched_speed = abs(curr_x - prev_x)  # Horizontal movement for linear
                
                speeds.append(matched_speed)
        
        return speeds
    
    def _calculate_baseline_speed(self):
        """Calculate the normal speed of cars with outlier filtering"""
        all_speeds = []
        
        # Collect speeds from last half of baseline period
        start_idx = max(0, len(self.car_speeds) - 60)
        for frame_speeds in self.car_speeds[start_idx:]:
            for speed in frame_speeds:
                if speed > 0.5:  # Ignore very slow speeds (noise)
                    all_speeds.append(speed)
        
        if len(all_speeds) < 10:
            return 0
        
        # Remove outliers (speeds that are too high or too low)
        all_speeds.sort()
        # Remove top and bottom 20%
        start = int(len(all_speeds) * 0.2)
        end = int(len(all_speeds) * 0.8)
        filtered_speeds = all_speeds[start:end]
        
        if len(filtered_speeds) > 0:
            return sum(filtered_speeds) / len(filtered_speeds)
        return 0
    
    def _detect_phantom_car_improved(self, current_speeds, current_cars):
        """Improved phantom car detection with stability checks"""
        
        # Debug: print current speeds vs baseline
        if self.frames_analyzed % 60 == 0:  # Every second
            avg_current = sum(s for s in current_speeds if s > 0) / max(1, len([s for s in current_speeds if s > 0]))
            print(f"Debug: Current avg speed: {avg_current:.2f}, Baseline: {self.baseline_speed:.2f}")
        
        for i, speed in enumerate(current_speeds):
            if speed <= 0:  # Skip stationary cars
                continue
                
            # Calculate speed ratio compared to baseline
            speed_ratio = speed / self.baseline_speed if self.baseline_speed > 0 else 1
            
            # Check if car is significantly slower than baseline
            if speed_ratio < self.speed_drop_threshold:
                car_id = f"car_{i}"
                
                # Track stability - car must be slow for multiple frames
                if car_id not in self.car_stability_count:
                    self.car_stability_count[car_id] = 0
                
                self.car_stability_count[car_id] += 1
                
                # Debug: print when car is detected as slow
                if self.car_stability_count[car_id] == 1:
                    print(f"Debug: Car {i} slow - Speed: {speed:.2f}, Ratio: {speed_ratio:.2f}, Threshold: {self.speed_drop_threshold}")
                
                # Only detect if car has been slow for enough frames
                if self.car_stability_count[car_id] >= self.stable_frames_needed:
                    car_x, car_y, _ = current_cars[i]
                    print(f"DETECTION TRIGGERED: Car {i} has been slow for {self.car_stability_count[car_id]} frames")
                    return {
                        'car_index': i,
                        'position': (car_x, car_y),
                        'speed': speed,
                        'baseline_speed': self.baseline_speed,
                        'speed_ratio': speed_ratio,
                        'stability_frames': self.car_stability_count[car_id]
                    }
            else:
                # Reset stability counter if car speeds up
                car_id = f"car_{i}"
                if car_id in self.car_stability_count and self.car_stability_count[car_id] > 0:
                    print(f"Debug: Car {i} sped up, resetting counter")
                    self.car_stability_count[car_id] = 0
        
        return None
    
    def _save_detection(self, frame, phantom_car, track_type):
        """Save screenshot and log the detection"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Draw circle around phantom car
        car_x, car_y = phantom_car['position']
        cv2.circle(frame, (car_x, car_y), 50, (0, 0, 255), 3)
        cv2.putText(frame, "PHANTOM TRAFFIC", (car_x - 80, car_y - 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Add detection info
        info_text = f"Speed: {phantom_car['speed']:.1f} | Baseline: {phantom_car['baseline_speed']:.1f}"
        cv2.putText(frame, info_text, (car_x - 100, car_y + 80), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Save screenshot
        filename = f"phantom_screenshots/phantom_{track_type}_{timestamp}.png"
        cv2.imwrite(filename, frame)
        
        # Log detection
        log_message = f"""
PHANTOM TRAFFIC DETECTED!
Timestamp: {timestamp}
Track Type: {track_type}
Car Position: ({car_x}, {car_y})
Car Speed: {phantom_car['speed']:.2f} pixels/frame
Baseline Speed: {phantom_car['baseline_speed']:.2f} pixels/frame
Speed Ratio: {phantom_car['speed_ratio']:.2f} (should be > 0.3)
Stability Frames: {phantom_car['stability_frames']}
Screenshot: {filename}
        """
        
        print(log_message)
        
        # Save to log file
        with open("phantom_screenshots/detection_log.txt", "a") as f:
            f.write(log_message + "\n" + "="*50 + "\n")
    
    def reset(self):
        """Reset detector for new simulation"""
        self.baseline_established = False
        self.car_positions = []
        self.car_speeds = []
        self.baseline_speed = 0
        self.frames_analyzed = 0
        self.detection_made = False
        self.track_type = "unknown"
        self.car_stability_count = {}
        print("Detector reset")