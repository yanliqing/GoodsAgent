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
    
    # Configure logging format with more detailed information
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    
    # Set log level to DEBUG to capture all our debug logs
    log_level = logging.DEBUG if settings.DEBUG or settings.is_development else getattr(logging, settings.LOG_LEVEL.upper())
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.FileHandler(log_dir / "app.log", encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Configure specific loggers
    loggers = {
        "uvicorn": logging.INFO,
        "sqlalchemy.engine": logging.WARNING,
        "httpx": logging.WARNING,
        # Enable our application loggers
        "app.services.taobao.api": logging.DEBUG,
        "app.services.agent": logging.DEBUG,
        "app.services.chat": logging.DEBUG,
        "app.api.endpoints": logging.DEBUG,
    }
    
    for logger_name, level in loggers.items():
        logging.getLogger(logger_name).setLevel(level)
    
    # Log the current configuration
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Level: {logging.getLevelName(log_level)}, Debug: {settings.DEBUG}")


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