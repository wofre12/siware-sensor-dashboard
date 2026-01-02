import pytest
from datetime import datetime
from app.alarm_manager import AlarmManager
from app.data_models import SensorReading

def test_alarm_trigger_low():
    manager = AlarmManager()
    # Temperature: low=10, high=80
    reading = SensorReading(sensor_name="Temperature", value=5.0, timestamp=datetime.now(), status="OK")
    alarm = manager.check_reading(reading)
    
    assert alarm is not None
    assert alarm.alarm_type == "LOW"
    assert manager.active_alarms["Temperature"] == "LOW"

def test_alarm_deduplication():
    manager = AlarmManager()
    reading = SensorReading(sensor_name="Temperature", value=5.0, timestamp=datetime.now(), status="OK")
    
    # First alarm
    alarm1 = manager.check_reading(reading)
    assert alarm1 is not None
    
    # Second reading still low - should NOT trigger new alarm
    alarm2 = manager.check_reading(reading)
    assert alarm2 is None

def test_alarm_reset():
    manager = AlarmManager()
    reading_low = SensorReading(sensor_name="Temperature", value=5.0, timestamp=datetime.now(), status="OK")
    reading_ok = SensorReading(sensor_name="Temperature", value=25.0, timestamp=datetime.now(), status="OK")
    
    manager.check_reading(reading_low)
    assert manager.active_alarms["Temperature"] == "LOW"
    
    manager.check_reading(reading_ok)
    assert manager.active_alarms["Temperature"] is None

def test_system_status_alarm():
    manager = AlarmManager()
    reading = SensorReading(sensor_name="Temperature", value=90.0, timestamp=datetime.now(), status="OK")
    manager.check_reading(reading)
    
    status = manager.get_system_status({"Temperature": reading})
    assert status == "ALARM"

def test_system_status_degraded():
    manager = AlarmManager()
    reading = SensorReading(sensor_name="Temperature", value=25.0, timestamp=datetime.now(), status="Faulty Sensor")
    
    status = manager.get_system_status({"Temperature": reading})
    assert status == "DEGRADED"
