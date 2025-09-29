"""
Logging configuration for the RSS to Kobo application.

This module provides default logging configuration and utilities.
"""
import os
from pathlib import Path
from typing import Dict, Any

# Base directory for logs
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Default log file paths
DEFAULT_LOG_FILE = LOG_DIR / "rss_to_kobo.log"
ERROR_LOG_FILE = LOG_DIR / "rss_to_kobo_errors.log"

# Logging configuration
def get_logging_config(debug: bool = False) -> Dict[str, Any]:
    """
    Get logging configuration dictionary.
    
    Args:
        debug: Whether to enable debug logging
        
    Returns:
        Dictionary with logging configuration
    """
    log_level = "DEBUG" if debug else os.getenv("LOG_LEVEL", "INFO")
    
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "standard",
                "stream": "ext://sys.stdout"
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "standard",
                "filename": str(DEFAULT_LOG_FILE.absolute()),
                "maxBytes": 10 * 1024 * 1024,  # 10 MB
                "backupCount": 5,
                "encoding": "utf8"
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": str(ERROR_LOG_FILE.absolute()),
                "maxBytes": 10 * 1024 * 1024,  # 10 MB
                "backupCount": 5,
                "encoding": "utf8"
            }
        },
        "loggers": {
            "": {  # root logger
                "handlers": ["console", "file", "error_file"],
                "level": log_level,
                "propagate": True
            },
            "__main__": {
                "handlers": ["console", "file"],
                "level": log_level,
                "propagate": False
            },
            "scripts": {
                "handlers": ["console", "file"],
                "level": log_level,
                "propagate": False
            },
            "urllib3": {
                "level": "WARNING"  # Reduce verbosity of urllib3
            },
            "dropbox": {
                "level": "INFO"  # Control dropbox SDK verbosity
            }
        }
    }
