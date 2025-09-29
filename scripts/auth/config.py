"""
Configuration and environment variable handling for RSS to Kobo.
"""
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Module version
__version__ = "0.2.0"

# Load environment variables from .env file if it exists
load_dotenv()

# Base directory of the project
BASE_DIR = Path(__file__).parent.parent.parent

# Default values for configuration
DEFAULT_OAUTH_REDIRECT_PORT = 5000
DEFAULT_TOKEN_EXPIRY_BUFFER = 300  # 5 minutes in seconds


def get_env_variable(name: str, default: Optional[str] = None) -> str:
    """Get environment variable or raise an error if not found and no default provided."""
    value = os.getenv(name, default)
    if value is None:
        raise ValueError(f"Required environment variable {name} is not set")
    return value


def get_oauth_config() -> dict:
    """Get OAuth configuration from environment variables."""
    return {
        "app_key": get_env_variable("DROPBOX_APP_KEY"),
        "app_secret": get_env_variable("DROPBOX_APP_SECRET"),
        "redirect_port": int(
            os.getenv("OAUTH_REDIRECT_PORT", DEFAULT_OAUTH_REDIRECT_PORT)
        ),
        "token_expiry_buffer": DEFAULT_TOKEN_EXPIRY_BUFFER,
    }


def get_token_path(username: str) -> Path:
    """Get the path to store tokens for a given username.
    
    On Windows: ~/.rss-to-kobo/tokens/username
    On Unix: ~/.local/share/rss-to-kobo/tokens/username
    """
    if os.name == 'nt':  # Windows
        tokens_dir = Path.home() / '.rss-to-kobo' / 'tokens'
    else:  # Unix-like
        tokens_dir = Path.home() / '.local' / 'share' / 'rss-to-kobo' / 'tokens'
        
    tokens_dir.mkdir(parents=True, exist_ok=True, mode=0o700)  # Secure directory permissions
    return tokens_dir / username


def is_debug() -> bool:
    """Check if debug mode is enabled."""
    return os.getenv("DEBUG", "false").lower() == "true"
