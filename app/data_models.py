from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class SensorReading:
    sensor_name: str
    value: float
    timestamp: datetime
    status: str
    
    @classmethod
    def from_dict(cls, data: dict):
        # Expected format: {"sensor": "...", "value": 0.0, "timestamp": "...", "status": "..."}
        return cls(
            sensor_name=data["sensor"],
            value=float(data["value"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            status=data["status"]
        )

@dataclass
class AlarmEvent:
    timestamp: datetime
    sensor_name: str
    value: float
    alarm_type: str  # "LOW" or "HIGH"
    message: str
