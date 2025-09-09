"""
Centralized logging configuration for ParseStudio.

This module provides a consistent logging setup across all ParseStudio components.
Users can control logging behavior through environment variables.
"""

import logging
import os
from typing import Optional


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger for ParseStudio components.
    
    Args:
        name (str): Logger name, typically the module name (e.g., 'parsers.anthropic')
        
    Returns:
        logging.Logger: Configured logger instance
        
    Environment Variables:
        PARSESTUDIO_LOG_LEVEL: Set logging level (DEBUG, INFO, WARNING, ERROR)
        PARSESTUDIO_LOG_FORMAT: Set custom log format (optional)
        PARSESTUDIO_LOG_FILE: Set log file path (optional)
        
    Examples:
        >>> logger = get_logger('parsers.anthropic')
        >>> logger.info("Starting PDF parsing")
        >>> logger.error("Failed to parse file", extra={"file_path": "test.pdf"})
    """
    logger_name = f"parsestudio.{name}"
    logger = logging.getLogger(logger_name)
    
    # Configure only if not already configured (prevents duplicate handlers)
    if not logger.handlers:
        # Get log level from environment, default to INFO
        level_str = os.environ.get("PARSESTUDIO_LOG_LEVEL", "INFO").upper()
        level = getattr(logging, level_str, logging.INFO)
        
        # Get custom format from environment or use default
        log_format = os.environ.get(
            "PARSESTUDIO_LOG_FORMAT",
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        formatter = logging.Formatter(log_format)
        
        # Console handler (always present)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Optional file handler
        log_file = os.environ.get("PARSESTUDIO_LOG_FILE")
        if log_file:
            try:
                file_handler = logging.FileHandler(log_file)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except (IOError, OSError) as e:
                # If file handler fails, log to console
                logger.warning(f"Failed to create log file {log_file}: {e}")
        
        logger.setLevel(level)
        logger.propagate = False  # Prevent duplicate logs from parent loggers
    
    return logger


def configure_root_logger(level: Optional[str] = None) -> None:
    """
    Configure the root ParseStudio logger.
    
    This is useful for setting up logging at the package level.
    
    Args:
        level (Optional[str]): Log level to set. If None, uses environment variable.
    """
    root_logger = logging.getLogger("parsestudio")
    
    if level is None:
        level = os.environ.get("PARSESTUDIO_LOG_LEVEL", "INFO").upper()
    
    root_logger.setLevel(getattr(logging, level, logging.INFO))


def set_log_level(level: str) -> None:
    """
    Set log level for all ParseStudio loggers.
    
    Args:
        level (str): Log level (DEBUG, INFO, WARNING, ERROR)
    """
    level_obj = getattr(logging, level.upper(), logging.INFO)
    
    # Update all existing parsestudio loggers
    for logger_name in logging.Logger.manager.loggerDict:
        if logger_name.startswith("parsestudio"):
            logger = logging.getLogger(logger_name)
            logger.setLevel(level_obj)