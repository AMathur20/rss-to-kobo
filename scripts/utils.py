"""
Utility functions for RSS to Kobo pipeline.
"""
import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import yaml
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_logger(name: str, log_level: int = logging.INFO) -> logging.Logger:
    """Create and configure a logger with the specified name."""
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    return logger

def load_feeds_config(user: str) -> Dict[str, Any]:
    """
    Load feed configuration for a specific user.
    
    Args:
        user: Username to load feeds for
        
    Returns:
        Dictionary containing feed configuration
    """
    config_path = Path(__file__).parent.parent / 'feeds' / f'{user}_feeds.yaml'
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"Feed config not found for user: {user}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML config for {user}: {e}")
        raise

def get_output_path(user: str) -> Path:
    """
    Get the output path for a user's EPUB file.
    
    Args:
        user: Username
        
    Returns:
        Path object for the output EPUB file
    """
    output_dir = Path(__file__).parent.parent / 'output'
    output_dir.mkdir(exist_ok=True)
    
    # Format: output/username_YYYY-MM-DD.epub
    date_str = datetime.now().strftime('%Y-%m-%d')
    return output_dir / f'{user}_Daily-RSS_{date_str}.epub'

def clean_html(html_content: str) -> str:
    """
    Clean HTML content for better EPUB display.
    
    Args:
        html_content: Raw HTML content
        
    Returns:
        Cleaned HTML content
    """
    # TODO: Implement HTML cleaning with beautifulsoup4
    # This is a placeholder - will be implemented in a future update
    return html_content

def format_date(date_str: Optional[str] = None) -> str:
    """
    Format a date string for display in the EPUB.
    
    Args:
        date_str: Optional date string to format. If None, uses current date.
        
    Returns:
        Formatted date string
    """
    if date_str:
        # Try to parse the input date string
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%B %d, %Y %H:%M')
        except (ValueError, AttributeError):
            pass
    
    # Default to current date if parsing fails or no date provided
    return datetime.now().strftime('%B %d, %Y')
