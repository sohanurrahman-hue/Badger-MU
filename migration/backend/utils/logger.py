"""
Logging configuration for Badge Engine
"""
import logging
import sys
import os
from pythonjsonlogger import jsonlogger


def setup_logging():
    """
    Configure application logging
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_format = os.getenv("LOG_FORMAT", "json")  # json or text
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level))
    
    # Remove existing handlers
    logger.handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level))
    
    if log_format == "json":
        # JSON formatter
        json_formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s',
            rename_fields={"asctime": "timestamp", "levelname": "level"}
        )
        console_handler.setFormatter(json_formatter)
    else:
        # Text formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    # File handler for errors
    error_file_handler = logging.FileHandler('logs/error.log')
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    logger.addHandler(error_file_handler)
    
    # Migration errors log
    migration_handler = logging.FileHandler('logs/migration_errors.log')
    migration_handler.setLevel(logging.ERROR)
    migration_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    )
    
    migration_logger = logging.getLogger('migration')
    migration_logger.addHandler(migration_handler)
    
    return logger

