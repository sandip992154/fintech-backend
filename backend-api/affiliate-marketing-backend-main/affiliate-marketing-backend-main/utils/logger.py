import logging
import sys
from datetime import datetime
import os

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Configure logging
def setup_logging():
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create file handler
    file_handler = logging.FileHandler(f'logs/app_{datetime.now().strftime("%Y%m%d")}.log')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Initialize logger
app_logger = setup_logging()

def log_api_request(endpoint: str, params: dict = None, user_ip: str = None):
    """Log API requests"""
    app_logger.info(f"API Request: {endpoint} | Params: {params} | IP: {user_ip}")

def log_api_error(endpoint: str, error: Exception, params: dict = None):
    """Log API errors"""
    app_logger.error(f"API Error: {endpoint} | Error: {str(error)} | Params: {params}")

def log_scraper_activity(scraper_name: str, action: str, details: str = None):
    """Log scraper activities"""
    app_logger.info(f"Scraper: {scraper_name} | Action: {action} | Details: {details}")

def log_database_operation(operation: str, collection: str, details: str = None):
    """Log database operations"""
    app_logger.info(f"DB Operation: {operation} | Collection: {collection} | Details: {details}")

def log_performance(operation: str, duration: float, details: str = None):
    """Log performance metrics"""
    app_logger.info(f"Performance: {operation} | Duration: {duration:.2f}s | Details: {details}")