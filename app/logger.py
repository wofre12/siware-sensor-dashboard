import logging
import os
from logging.handlers import RotatingFileHandler
from .config import LOG_DIR

def setup_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Console Handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # File Handler
    log_file = os.path.join(LOG_DIR, "app.log")
    fh = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    return logger

# Global app logger
logger = setup_logger("SensorDashboard")
