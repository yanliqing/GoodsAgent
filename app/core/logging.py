import logging
import sys
from pathlib import Path
from typing import Dict, Any

from app.core.config import settings


def setup_logging() -> None:
    """Setup application logging configuration"""
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        format=log_format,
        handlers=[
            logging.FileHandler(log_dir / "app.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Configure specific loggers
    loggers = {
        "uvicorn": logging.INFO,
        "sqlalchemy.engine": logging.WARNING,
        "httpx": logging.WARNING,
    }
    
    for logger_name, level in loggers.items():
        logging.getLogger(logger_name).setLevel(level)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)


class StructuredLogger:
    """Structured logging helper"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log_api_request(self, method: str, path: str, user_id: int = None, **kwargs):
        """Log API request"""
        extra_data = {
            "method": method,
            "path": path,
            "user_id": user_id,
            **kwargs
        }
        self.logger.info(f"API Request: {method} {path}", extra=extra_data)
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """Log error with context"""
        context = context or {}
        self.logger.error(
            f"Error: {str(error)}", 
            extra={"error_type": type(error).__name__, "context": context},
            exc_info=True
        )