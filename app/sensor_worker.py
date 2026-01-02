import socket
import json
import time
import os
import asyncio
import threading
from PySide6.QtCore import QThread, Signal
try:
    from .data_models import SensorReading
    from .logger import logger
    from .config import HOST
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app.data_models import SensorReading
    from app.logger import logger
    from app.config import HOST

class SensorWorker(QThread):
    """
    Worker thread that maintains a TCP connection to a single sensor simulator.
    Emits a signal whenever new data is received and parsed.
    """
    data_received = Signal(SensorReading)
    connection_status = Signal(str, bool)  # sensor_name, is_connected

    def __init__(self, sensor_name: str, port: int):
        super().__init__()
        self.sensor_name = sensor_name
        self.port = port
        self.running = True

    def run(self):
        while self.running:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(5.0)
                    logger.info(f"Attempting to connect to {self.sensor_name} on port {self.port}...")
                    s.connect((HOST, self.port))
                    self.connection_status.emit(self.sensor_name, True)
                    logger.info(f"Connected to {self.sensor_name}")

                    buffer = ""
                    while self.running:
                        data = s.recv(1024).decode('utf-8')
                        if not data:
                            break
                        
                        buffer += data
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            if not line.strip():
                                continue
                            try:
                                payload = json.loads(line)
                                reading = SensorReading.from_dict(payload)
                                self.data_received.emit(reading)
                            except (json.JSONDecodeError, KeyError, ValueError) as e:
                                logger.error(f"Error parsing data from {self.sensor_name}: {e}")

            except (socket.error, socket.timeout):
                self.connection_status.emit(self.sensor_name, False)
                logger.warning(f"Connection lost/failed for {self.sensor_name}. Retrying in 2s...")
                # Responsive sleep
                for _ in range(20):
                    if not self.running: break
                    time.sleep(0.1)
            except Exception as e:
                logger.error(f"Unexpected error in {self.sensor_name} worker: {e}")
                for _ in range(20):
                    if not self.running: break
                    time.sleep(0.1)

    def stop(self):
        self.running = False
        self.wait()

class LogTailer(QThread):
    """
    Background worker that 'tails' the application log file.
    Emits lines to the GUI.
    """
    new_log_line = Signal(str)

    def __init__(self, log_path: str):
        super().__init__()
        self.log_path = log_path
        self.running = True

    def run(self):
        last_size = 0
        if os.path.exists(self.log_path):
            last_size = os.path.getsize(self.log_path)

        while self.running:
            try:
                if not os.path.exists(self.log_path):
                    time.sleep(1)
                    continue

                current_size = os.path.getsize(self.log_path)
                
                # Check for rotation
                if current_size < last_size:
                    last_size = 0

                if current_size > last_size:
                    with open(self.log_path, 'r', encoding='utf-8', errors='ignore') as f:
                        f.seek(last_size)
                        new_data = f.read()
                        if new_data:
                            for line in new_data.splitlines():
                                if line.strip():
                                    self.new_log_line.emit(line.strip())
                    last_size = current_size
                
                time.sleep(0.5) # Poll interval
            except Exception as e:
                # Log to console only to avoid infinite loops if logging fails
                print(f"LogTailer error: {e}")
                time.sleep(1)

    def stop(self):
        self.running = False
        self.wait()

class WebSocketServer(threading.Thread):
    """
    Simple WebSocket server to stream sensor data and events.
    Uses 'websockets' library if available, else logs a warning.
    """
    def __init__(self, host, port):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self.clients = set()
        self.loop = None

    async def register(self, websocket):
        self.clients.add(websocket)
        try:
            await websocket.wait_closed()
        finally:
            self.clients.remove(websocket)

    async def main(self):
        try:
            import websockets
            async with websockets.serve(self.handler, self.host, self.port):
                await asyncio.Future()  # run forever
        except ImportError:
            logger.error("Websockets library not found. WS server disabled.")

    async def handler(self, websocket):
        await self.register(websocket)

    def broadcast(self, message):
        """Thread-safe way to send messages to all WS clients."""
        if self.loop:
            asyncio.run_coroutine_threadsafe(self._broadcast_coro(message), self.loop)

    async def _broadcast_coro(self, message):
        if not self.clients:
            return
        msg_json = json.dumps(message)
        await asyncio.gather(*[client.send(msg_json) for client in self.clients], return_exceptions=True)

    def run(self):
        try:
            import websockets
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self.main())
        except ImportError:
            pass
