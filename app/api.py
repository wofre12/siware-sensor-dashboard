import threading
from flask import Flask, jsonify
try:
    from .config import API_PORT, SENSORS_CONFIG
    from .logger import logger
except ImportError:
    import sys
    import os
    # Add parent directory to path to allow direct execution
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app.config import API_PORT, SENSORS_CONFIG
    from app.logger import logger

# Global state to be updated by the main app
latest_data = {}
system_status = "UNKNOWN"

app = Flask(__name__)

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({
        "status": system_status,
        "sensors": latest_data
    })

def run_api():
    try:
        # Disable Flask's default logging to keep console clean
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        
        logger.info(f"Starting API server on port {API_PORT}...")
        app.run(host='0.0.0.0', port=API_PORT, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"API server failed to start: {e}")

def start_api_thread():
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    return api_thread
