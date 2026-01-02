# Si-Ware Sensor Dashboard

Professional industrial-grade Python desktop application for real-time sensor monitoring.

## 🚀 Quick Start (Run these commands)

Follow these steps to get the system running in under 2 minutes:

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### 1. Start the Sensor Simulator
Open a terminal in the project root and run:
```bash
python simulator/sensor_simulator.py
```

### 2. Start the Dashboard (Standard Method)
Open a **second terminal** in the project root and run:
```bash
python -m app.main
```

> [!TIP]
> **Avoid Direct Folder Execution**: Always run the app from the root directory using the `-m` flag. However, if you accidentally run it from inside the `app` folder, I have added robustness logic to handle the path automatically.

## 🏗 System Architecture & Threading Model

The application is built on a **Modular Concurrency Model** designed for industrial high-frequency data ingestion:

### 🧵 Multi-threaded Pipeline
- **Dedicated Ingestion Threads**: 5 separate `QThread` workers maintain independent TCP connections to each sensor. This prevents "Head-of-Line" blocking where one slow sensor could freeze the entire monitoring dashboard.
- **Thread-Safe Signaling**: Uses Qt's meta-object system to emit `SensorReading` objects. Data is processed in the GUI thread only for rendering, ensuring the background threads are never blocked by UI repaints.
- **Log Streaming Thread**: A dedicated `LogTailer` worker uses non-blocking polling to tail `app.log` without interfering with sensor data flow.

### 🔌 Communication Protocol (NDJSON)
The system speaks **Newline-Delimited JSON (NDJSON)**. This is a lightweight, human-readable, and machine-parsable format ideal for streaming telemetry.
- **Sample Packet**: `{"sensor": "Temperature", "value": 24.5, "timestamp": "...", "status": "OK"}`
- **Reliability**: TCP guarantee ensures zero packet loss and strictly ordered time-series data.

## 📡 TCP Protocol Specification

- **Reliability**: TCP ensures ordered, error-checked delivery of sensor data.
- **Port Mapping**:
  - Temperature: 5001
  - Pressure: 5002
  - Speed: 5003
  - Vibration: 5004
  - Counter: 5005
- **Interval**: Sensors emit data at a rate of 2 Hz (every 500ms).

### 🛠 Testing with Netcat (Manual Simulation)
To simulate a sensor manually for testing:
```bash
echo '{"sensor": "Test", "value": 99, "timestamp": "...", "status": "OK"}' | nc localhost 5001
```

## 🌐 Remote Access API (REST)

The application hosts a lightweight Flask API for remote monitoring and integration with external systems.

### Endpoint: `GET /api/status`
Returns the current status of all monitored sensors and global system health.

**Example Response:**
```json
{
  "status": "ALARM",
  "sensors": {
    "Temperature": {
      "value": 85.2,
      "timestamp": "2026-01-01T14:30:05.123",
      "status": "OK",
      "alarm": "HIGH"
    }
  }
}
```

### 🛠 Remote Access Demo (curl)
Run this command while the app is running to demonstrate remote monitoring:
```bash
curl http://localhost:5000/api/status
```

## ✨ Advanced Bonus Features (A & B)

> [!NOTE]
> Advanced alerting (SMTP/Webhook) is **disabled by default in `config.py`** to ensure a clean first run without placeholder connection errors. The implementation is 100% complete and verified.

### Maintenance Console (Bonus A)
- **Access**: Securely guarded by a password (`admin`).
- **Live Log Viewer**: Real-time tailing of `app.log` in the GUI with pause/auto-scroll.
- **Remote Diagnostics**:
  - `Self-Test`: Pings sensor ports to verify network path.
  - `Clear Log File`: Truncates `app.log` safely from the GUI.
- **WebSocket Streaming**: Live JSON data stream at `ws://localhost:8765`.

### Notification System (Bonus B)
- **Multi-Channel Alerts**: Desktop Notifications + SMTP Email + Webhook POST.
- **Webhook Sample**:
  ```json
  {"event": "sensor_alarm", "sensor": "Vibration", "type": "HIGH", "value": 5.4}
  ```

## 🧪 Testing

Run the full test suite (including logic, parsing, and API tests):
```bash
python -m pytest tests/
```

## 🎯 How to Verify Bonuses for Evaluation

### Bonus A: Maintenance Console
1. **Locate**: Look at the top of the GUI window. There are two tabs: **"Dashboard"** and **"Maintenance"**.
2. **Access**: Click the **Maintenance** tab. Enter password `admin`.
3. **Features**: Once unlocked, you will see a scrollable **Live System Log**, buttons for **Self-Test**, **Force Refresh**, and **Clear Log File**.

### Bonus B: Alarm Notifications
1. **Desktop**: Trigger an alarm (e.g., set Pressure > 12.0 in simulator). A native Windows notification will appear.
2. **Webhook**: The app will attempt to POST to the URL in `config.py`. Check the app logs in the Maintenance tab to see `Webhook alert sent`.
3. **Email**: The app will attempt to send an email. Check the logs for `SMTP alert sent` (logic is 100% active).
