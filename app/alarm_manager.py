from datetime import datetime
from typing import Dict, Optional, List
from .data_models import SensorReading, AlarmEvent
from .config import SENSORS_CONFIG

class AlarmManager:
    def __init__(self):
        # Tracks the current alarm state for each sensor: None, "LOW", or "HIGH"
        self.active_alarms: Dict[str, Optional[str]] = {name: None for name in SENSORS_CONFIG}
        
    def check_reading(self, reading: SensorReading) -> Optional[AlarmEvent]:
        sensor_name = reading.sensor_name
        if sensor_name not in SENSORS_CONFIG:
            return None
            
        # Priority: Faulty sensors should not trigger alarm events (Red), 
        # they are handled as Yellow in the UI based on reading.status
        if reading.status != "OK":
            self.active_alarms[sensor_name] = "FAULTY"
            return None
            
        config = SENSORS_CONFIG[sensor_name]
        low_limit = config.get("low")
        high_limit = config.get("high")
        
        current_state = self.active_alarms.get(sensor_name)
        new_state = None
        
        if low_limit is not None and reading.value < low_limit:
            new_state = "ALARM_LOW"
        elif high_limit is not None and reading.value > high_limit:
            new_state = "ALARM_HIGH"
            
        # Trigger AlarmEvent only for actual breaches
        if new_state and "ALARM" in new_state and new_state != current_state:
            self.active_alarms[sensor_name] = new_state
            msg = f"{sensor_name} {new_state.split('_')[1]} limit violation: {reading.value:.2f} {config['unit']}"
            return AlarmEvent(
                timestamp=datetime.now(),
                sensor_name=sensor_name,
                value=reading.value,
                alarm_type=new_state.split('_')[1],
                message=msg
            )
            
        self.active_alarms[sensor_name] = new_state
        return None

    def get_system_status(self, all_readings: Dict[str, SensorReading]) -> str:
        """
        Calculates global status with strict priority:
        1. ALARM (Red): any active limit violation
        2. DEGRADED (Yellow): any sensor reporting 'Faulty' or non-OK status
        3. OK (Green): everything is perfect
        """
        states = self.active_alarms.values()
        
        if any(state and "ALARM" in state for state in states):
            return "ALARM"
            
        if any(r.status != "OK" for r in all_readings.values()):
            return "DEGRADED"
            
        return "OK"
