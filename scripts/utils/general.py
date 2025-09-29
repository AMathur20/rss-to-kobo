"""
General utility functions for RSS to Kobo pipeline.
"""
import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import yaml
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

def load_feeds_config(user: str) -> Dict[str, Any]:
    """
    Load feed configuration for a specific user.
    
    Args:
        user: Username to load feeds for
        
    Returns:
        Dictionary containing feed configuration
        
    Raises:
        FileNotFoundError: If the config file doesn't exist
        yaml.YAMLError: If there's an error parsing the YAML
    """
    # Look for config in both the current directory and one level up
    possible_paths = [
        Path("config") / "feeds" / f"{user}.yaml",  # Current directory
        Path("..") / "config" / "feeds" / f"{user}.yaml",  # One level up
        Path("..") / ".." / "config" / "feeds" / f"{user}.yaml"  # Two levels up (for scripts/ directory)
    ]
    
    config_path = None
    for path in possible_paths:
        if path.exists():
            config_path = path
            break
    
    if not config_path:
        error_msg = f"Config file not found. Tried: {[str(p) for p in possible_paths]}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    try:
        logger.info(f"Loading configuration from: {config_path}")
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f) or {}
            
        # Ensure required fields exist
        if not config_data.get('feeds'):
            logger.warning("No 'feeds' section found in configuration")
            config_data['feeds'] = []
            
        # Set default output settings if not specified
        if 'output' not in config_data:
            config_data['output'] = {}
            
        config_data['output'].setdefault('title', "Daily RSS Digest")
        config_data['output'].setdefault('author', "RSS to Kobo")
        config_data['output'].setdefault('language', "en")
        
        # Set default Dropbox settings if not specified
        if 'dropbox' not in config_data:
            config_data['dropbox'] = {}
            
        config_data['dropbox'].setdefault('target_folder', "/RSS Feeds")
        config_data['dropbox'].setdefault('filename', "Daily-RSS.epub")
        
        return config_data
        
    except yaml.YAMLError as e:
        error_msg = f"Error parsing YAML config at {config_path}: {e}"
        logger.error(error_msg)
        raise yaml.YAMLError(error_msg) from e

def get_output_path(user: str) -> Path:
    """
    Get the output path for a user's EPUB file.
    
    Args:
        user: Username
        
    Returns:
        Path object for the output EPUB file
    """
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return output_dir / f"{user}_rss_{timestamp}.epub"

def clean_html(html_content: str) -> str:
    """
    Clean HTML content for better EPUB display.
    
    Args:
        html_content: Raw HTML content
        
    Returns:
        Cleaned HTML content
    """
    # Basic HTML cleaning can be added here
    return html_content.strip()

def format_date(date_str: Optional[str] = None) -> str:
    """
    Format a date string for display in the EPUB.
    
    Args:
        date_str: Optional date string to format. If None, uses current date.
        
    Returns:
        Formatted date string
    """
    if date_str:
        try:
            # Try to parse the input date string
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            date_obj = datetime.now()
    else:
        date_obj = datetime.now()
        
    return date_obj.strftime("%B %d, %Y at %I:%M %p")
