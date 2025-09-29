"""
Utility functions and classes for the RSS to Kobo application.
"""

# This file makes the utils directory a Python package

# Import key utilities to make them available at the package level
from .logging_utils import setup_logger, log_execution_time
from .general import (
    clean_html,
    format_date,
    get_output_path,
    load_feeds_config
)

__all__ = [
    # Logging utilities
    'setup_logger',
    'log_execution_time',
    
    # General utilities
    'clean_html',
    'format_date',
    'get_output_path',
    'load_feeds_config',
]
