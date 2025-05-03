import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from app.config import settings

def setup_logging():
    """Configure logging for the application"""
    # Create logs directory if it doesn't exist
    if not os.path.exists(settings.LOG_FOLDER):
        os.makedirs(settings.LOG_FOLDER)
    
    # Set up rotating file handler
    file_handler = RotatingFileHandler(
        filename=os.path.join(settings.LOG_FOLDER, 'app.log'),
        maxBytes=10485760,  # 10 MB
        backupCount=5,
        encoding='utf-8'  # Thêm encoding utf-8
    )
    
    # Log formatting
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    
    # Create error log file
    error_handler = RotatingFileHandler(
        filename=os.path.join(settings.LOG_FOLDER, 'error.log'),
        maxBytes=10485760,  # 10 MB
        backupCount=5,
        encoding='utf-8'  # Thêm encoding utf-8
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    
    # Create console handler for terminal output
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)  # Set level for console output
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(console_handler)  # Add console handler

def get_logger(name):
    """Get a logger for a specific module"""
    return logging.getLogger(name)
