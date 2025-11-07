"""
Centralized logging utility for the application
Provides structured logging with different levels
"""
import logging
import sys
from typing import Optional, Any
from datetime import datetime


class Logger:
    """
    Centralized logger for the application
    Provides structured logging with different levels
    """
    
    _initialized = False
    _logger: Optional[logging.Logger] = None
    
    @classmethod
    def setup(cls, level: str = "INFO", log_file: Optional[str] = None):
        """
        Setup the logger with configuration
        
        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional file path to write logs to
        """
        if cls._initialized:
            return
        
        # Create logger
        cls._logger = logging.getLogger('granjas_del_carmen')
        cls._logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        
        # Prevent duplicate handlers
        if cls._logger.handlers:
            return
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        console_handler.setFormatter(formatter)
        cls._logger.addHandler(console_handler)
        
        # File handler (if specified)
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
            file_handler.setFormatter(formatter)
            cls._logger.addHandler(file_handler)
        
        cls._initialized = True
    
    @classmethod
    def _ensure_initialized(cls):
        """Ensure logger is initialized"""
        if not cls._initialized:
            cls.setup()
    
    @classmethod
    def debug(cls, message: str, **kwargs):
        """Log debug message"""
        cls._ensure_initialized()
        if cls._logger:
            cls._logger.debug(message, extra=kwargs)
    
    @classmethod
    def info(cls, message: str, **kwargs):
        """Log info message"""
        cls._ensure_initialized()
        if cls._logger:
            cls._logger.info(message, extra=kwargs)
    
    @classmethod
    def warning(cls, message: str, **kwargs):
        """Log warning message"""
        cls._ensure_initialized()
        if cls._logger:
            cls._logger.warning(message, extra=kwargs)
    
    @classmethod
    def error(cls, message: str, exc_info: Optional[Any] = None, **kwargs):
        """
        Log error message
        
        Args:
            message: Error message
            exc_info: Exception info (from sys.exc_info() or exception object)
            **kwargs: Additional context
        """
        cls._ensure_initialized()
        if cls._logger:
            cls._logger.error(message, exc_info=exc_info, extra=kwargs)
    
    @classmethod
    def critical(cls, message: str, exc_info: Optional[Any] = None, **kwargs):
        """
        Log critical message
        
        Args:
            message: Critical message
            exc_info: Exception info (from sys.exc_info() or exception object)
            **kwargs: Additional context
        """
        cls._ensure_initialized()
        if cls._logger:
            cls._logger.critical(message, exc_info=exc_info, extra=kwargs)
    
    @classmethod
    def exception(cls, message: str, **kwargs):
        """
        Log exception with traceback
        
        Args:
            message: Exception message
            **kwargs: Additional context
        """
        cls._ensure_initialized()
        if cls._logger:
            cls._logger.exception(message, extra=kwargs)


# Initialize logger on import
Logger.setup()

