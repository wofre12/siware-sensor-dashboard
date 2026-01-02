import os

# Networking Configuration
HOST = "127.0.0.1"
SENSORS_CONFIG = {
    "Temperature": {"port": 5001, "low": 10.0, "high": 80.0, "unit": "°C"},
    "Pressure":    {"port": 5002, "low": 0.5,  "high": 12.0, "unit": "bar"},
    "Speed":       {"port": 5003, "low": 0,    "high": 3000, "unit": "RPM"},
    "Vibration":   {"port": 5004, "low": 0,    "high": 5.0,  "unit": "mm/s"},
    "Counter":     {"port": 5005, "low": None, "high": None, "unit": "pcs"} # Counter usually has no limits
}

# SMTP Configuration
# SET TO True to test implemented SMTP alert logic.
# Feature is fully integrated but disabled by default to prevent "connection failed" logs with placeholders.
SMTP_ENABLED = False
SMTP_SERVER = "smtp.example.com"
SMTP_PORT = 587
SMTP_USER = "alerts@example.com"
SMTP_PASS = "securepassword"
ALERT_RECIPIENT = "engineer@example.com"

# Webhook Configuration
# SET TO True to test implemented Webhook POST logic.
WEBHOOK_ENABLED = False
WEBHOOK_URL = "https://hooks.example.com/sensor-alerts"

# Desktop Notifications
DESKTOP_NOTIFICATIONS_ENABLED = True

# WebSocket Monitoring
WS_PORT = 8765
WS_HOST = "0.0.0.0"

# Maintenance Configuration
MAINTENANCE_PASSWORD = "admin"

# UI Configuration
UPDATE_INTERVAL_MS = 200  # 5 times per second
PLOT_HISTORY_SECONDS = 20
UI_REFRESH_RATE = 2       # Desired Hz for data consumption

# API Configuration
API_PORT = 5000

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Status strings
STATUS_OK = "OK"
STATUS_FAULTY = "Faulty Sensor"
STATUS_ALARM = "ALARM"
STATUS_DEGRADED = "DEGRADED"
