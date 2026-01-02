import pytest
import json
from datetime import datetime
from app.data_models import SensorReading

def test_parsing_valid_json():
    raw = '{"sensor": "Pressure", "value": 10.5, "timestamp": "2023-10-27T10:00:00.000", "status": "OK"}'
    data = json.loads(raw)
    reading = SensorReading.from_dict(data)
    
    assert reading.sensor_name == "Pressure"
    assert reading.value == 10.5
    assert reading.status == "OK"
    assert isinstance(reading.timestamp, datetime)

def test_parsing_invalid_json():
    with pytest.raises(json.JSONDecodeError):
        json.loads('{"invalid": json')

def test_parsing_missing_keys():
    raw = '{"sensor": "Pressure"}' # missing value, timestamp, status
    data = json.loads(raw)
    with pytest.raises(KeyError):
        SensorReading.from_dict(data)
