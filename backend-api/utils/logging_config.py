import logging
import logging.handlers
import os
import uuid
from datetime import datetime
from typing import Optional, Dict
from fastapi import Request
import json

class RequestResponseLoggingMiddleware:
    def __init__(self, app, app_logger):
        self.app = app
        self.app_logger = app_logger

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Create a request-like object
        start_time = datetime.utcnow()
        request_id = str(uuid.uuid4())
        
        # Log request
        request_log = {
            'request_id': request_id,
            'method': scope.get("method", ""),
            'path': scope.get("path", ""),
            'timestamp': start_time.isoformat(),
        }
        
        self.app_logger.info(f"Incoming request: {json.dumps(request_log)}")
        
        try:
            await self.app(scope, receive, send)
            
            # Log completion
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            response_log = {
                'request_id': request_id,
                'duration': duration,
                'timestamp': end_time.isoformat()
            }
            
            self.app_logger.info(f"Request completed: {json.dumps(response_log)}")
            
        except Exception as e:
            self.app_logger.error(f"Request failed: {request_id}", exc_info=True)
            raise

def setup_logging(config: dict) -> logging.Logger:
    """
    Set up application logging with rotation and proper formatting
    """
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger("bandaru_api")
    logger.setLevel(config.get("level", "INFO"))

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File Handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        filename=config.get("file", "logs/app.log"),
        maxBytes=config.get("max_size", 10 * 1024 * 1024),  # 10 MB
        backupCount=config.get("backup_count", 5)
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Error Handler
    error_handler = logging.handlers.RotatingFileHandler(
        filename="logs/error.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n'
        'Path: %(pathname)s\n'
        'Line: %(lineno)d\n'
        'Exception: %(exc_info)s'
    )
    error_handler.setFormatter(error_formatter)
    logger.addHandler(error_handler)

    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance. If name is provided, returns a child logger.
    """
    logger = logging.getLogger("bandaru_api")
    if name:
        return logger.getChild(name)
    return logger
