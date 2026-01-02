import socket
import json
import time
import random
import threading
from datetime import datetime

# Local config copy to avoid dependency on app package for the standalone simulator
SENSORS = {
    "Temperature": {"port": 5001, "base": 25.0, "jitter": 2.0, "spike_chance": 0.05, "spike_val": 60.0},
    "Pressure":    {"port": 5002, "base": 5.0,  "jitter": 0.5, "spike_chance": 0.05, "spike_val": 8.0},
    "Speed":       {"port": 5003, "base": 1500, "jitter": 50,  "spike_chance": 0.05, "spike_val": 1600},
    "Vibration":   {"port": 5004, "base": 1.0,  "jitter": 0.2, "spike_chance": 0.10, "spike_val": 4.5}, # High noise
    "Counter":     {"port": 5005, "base": 0,    "jitter": 1,   "spike_chance": 0.0,  "spike_val": 0}
}

class SensorInstance:
    def __init__(self, name, config):
        self.name = name
        self.config = config
        self.current_val = config["base"]
        self.is_running = True

    def generate_reading(self):
        # Faulty sensor simulation (3% chance)
        status = "OK"
        if random.random() < 0.03:
            status = "Faulty Sensor"
            
        # Value oscillation
        if self.name == "Counter":
            self.current_val += 1
        else:
            # Add random walk / jitter
            self.current_val += random.uniform(-self.config["jitter"], self.config["jitter"])
            
            # Artificial spikes for alarm testing
            if random.random() < self.config["spike_chance"]:
                self.current_val += self.config["spike_val"]

        return {
            "sensor": self.name,
            "value": round(self.current_val, 2),
            "timestamp": datetime.now().isoformat(),
            "status": status
        }

    def start_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(('127.0.0.1', self.config["port"]))
                s.listen()
                print(f"Simulator: {self.name} listening on port {self.config['port']}...")
                
                while self.is_running:
                    conn, addr = s.accept()
                    with conn:
                        print(f"Simulator: {self.name} connected to {addr}")
                        while self.is_running:
                            reading = self.generate_reading()
                            msg = json.dumps(reading) + "\n"
                            try:
                                conn.sendall(msg.encode('utf-8'))
                            except (BrokenPipeError, ConnectionResetError, socket.error):
                                print(f"Simulator: {self.name} connection lost.")
                                break
                            time.sleep(0.5) # Send 2 times per second
            except Exception as e:
                print(f"Simulator error in {self.name}: {e}")

def run_simulator():
    threads = []
    for name, config in SENSORS.items():
        sensor = SensorInstance(name, config)
        t = threading.Thread(target=sensor.start_server, daemon=True)
        t.start()
        threads.append(t)
    
    print("All simulators started. Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping simulators...")

if __name__ == "__main__":
    run_simulator()
