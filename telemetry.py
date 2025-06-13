import json
import csv
import os
from datetime import datetime
from typing import List, Dict, Any

class TelemetryLogger:
    def __init__(self, log_directory="telemetry_logs"):
        """Initialize the telemetry logger"""
        self.log_directory = log_directory
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create log directory if it doesn't exist
        os.makedirs(self.log_directory, exist_ok=True)
        
        # Initialize log files
        self.csv_filename = os.path.join(self.log_directory, f"traffic_data_{self.session_id}.csv")
        self.json_filename = os.path.join(self.log_directory, f"events_{self.session_id}.json")
        self.summary_filename = os.path.join(self.log_directory, f"summary_{self.session_id}.txt")
        
        # Data storage
        self.frame_count = 0
        self.events = []
        self.session_start_time = datetime.now()
        
        # Initialize CSV file with headers
        self._initialize_csv()
        
        print(f"Telemetry logging initialized - Session ID: {self.session_id}")
    
    def _initialize_csv(self):
        """Initialize CSV file with column headers"""
        headers = [
            'timestamp', 'frame', 'track_type', 'simulation_speed', 'paused',
            'avg_speed', 'flow_percentage', 'num_braking', 'congested',
            'car_id', 'car_position', 'car_speed', 'car_braking'
        ]
        
        with open(self.csv_filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
    
    def log_frame_data(self, simulation_state: Dict[str, Any], cars: List[Any], traffic_stats: Dict[str, Any]):
        """Log data for current frame"""
        timestamp = datetime.now().isoformat()
        self.frame_count += 1
        
        # Log data for each car
        with open(self.csv_filename, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            for car in cars:
                row = [
                    timestamp,
                    self.frame_count,
                    simulation_state['track_type'],
                    simulation_state['time_scale'],
                    simulation_state['paused'],
                    traffic_stats['avg_speed'],
                    traffic_stats['flow_percentage'],
                    traffic_stats['num_braking'],
                    traffic_stats['congested'],
                    car.id,
                    car.position,
                    car.speed,
                    car.braking
                ]
                writer.writerow(row)
    
    def log_event(self, event_type: str, event_data: Dict[str, Any]):
        """Log a specific event (brake event, track switch, etc.)"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'frame': self.frame_count,
            'event_type': event_type,
            'data': event_data
        }
        
        self.events.append(event)
        
        # Write to JSON file
        with open(self.json_filename, 'w') as jsonfile:
            json.dump(self.events, jsonfile, indent=2)
    
    def log_brake_event(self, car_id: int, car_position: float, trigger_type: str):
        """Log a brake event"""
        self.log_event('brake_event', {
            'car_id': car_id,
            'car_position': car_position,
            'trigger_type': trigger_type,
            'frame': self.frame_count
        })
    
    def log_track_switch(self, old_track: str, new_track: str):
        """Log track type change"""
        self.log_event('track_switch', {
            'old_track': old_track,
            'new_track': new_track
        })
    
    def log_simulation_control(self, action: str, value: Any = None):
        """Log simulation control actions (pause, speed change, reset)"""
        self.log_event('simulation_control', {
            'action': action,
            'value': value
        })
    
    def generate_session_summary(self):
        """Generate a summary of the session"""
        session_duration = datetime.now() - self.session_start_time
        
        # Calculate statistics from events
        brake_events = [e for e in self.events if e['event_type'] == 'brake_event']
        track_switches = [e for e in self.events if e['event_type'] == 'track_switch']
        
        summary = f"""
TRAFFIC SIMULATION SESSION SUMMARY
=================================
Session ID: {self.session_id}
Start Time: {self.session_start_time.strftime('%Y-%m-%d %H:%M:%S')}
Duration: {session_duration}
Total Frames: {self.frame_count}
Average FPS: {self.frame_count / session_duration.total_seconds():.1f}

EVENTS SUMMARY
=============
Total Events: {len(self.events)}
Brake Events: {len(brake_events)}
Track Switches: {len(track_switches)}

BRAKE EVENTS BREAKDOWN
=====================
"""
        
        # Analyze brake events
        if brake_events:
            brake_types = {}
            for event in brake_events:
                trigger_type = event['data'].get('trigger_type', 'unknown')
                brake_types[trigger_type] = brake_types.get(trigger_type, 0) + 1
            
            for brake_type, count in brake_types.items():
                summary += f"{brake_type.capitalize()} brakes: {count}\n"
        else:
            summary += "No brake events recorded\n"
        
        # File information
        summary += f"\nFILES GENERATED\n"
        summary += f"===============\n"
        summary += f"Traffic Data CSV: {self.csv_filename}\n"
        summary += f"Events JSON: {self.json_filename}\n"
        summary += f"Summary: {self.summary_filename}\n"
        
        # Write summary to file
        with open(self.summary_filename, 'w') as f:
            f.write(summary)
        
        print(summary)
        return summary
    
    def close_session(self):
        """Close the telemetry session and generate final summary"""
        self.generate_session_summary()
        print(f"Telemetry session closed. Files saved in {self.log_directory}/")
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics"""
        return {
            'session_id': self.session_id,
            'frame_count': self.frame_count,
            'total_events': len(self.events),
            'brake_events': len([e for e in self.events if e['event_type'] == 'brake_event']),
            'session_duration': datetime.now() - self.session_start_time
        } 