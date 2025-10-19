import logging
from pythonjsonlogger import jsonlogger
import os

# --- Define Project Root for a reliable path ----
# This assumes this file is in src/utils/
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG_FILE_PATH = os.path.join(PROJECT_ROOT, "audit_log.jsonl")

def setup_logger():
    logger = logging.getLogger("audit_logger")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    
    # Use a relative path that works in the Space environment
    log_file_path = "audit_log.jsonl"
    
    logHandler = logging.FileHandler(log_file_path, mode='a')
    
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    logHandler.setFormatter(formatter)
    
    if not logger.handlers:
        logger.addHandler(logHandler)
        
    return logger

# Create a logger instance to be imported by other modules
audit_log = setup_logger()
