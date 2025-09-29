"""
Authentication and authorization module for RSS to Kobo.

This module handles OAuth 2.0 authentication with Dropbox,
token management, and secure credential storage.
"""

# Core components
from .config import get_oauth_config, get_token_path, is_debug
from .exceptions import (
    OAuthError,
    AuthenticationError,
    TokenRefreshError,
    TokenStorageError,
    ConfigurationError,
    AuthorizationError
)
from .oauth_handler import OAuthHandler
from .secure_storage import SecureTokenStorage

# CLI interface
from .cli import run_oauth_flow, check_auth, logout_user

__version__ = "0.2.0"

__all__ = [
    # Core components
    'OAuthHandler',
    'SecureTokenStorage',
    
    # Configuration
    'get_oauth_config',
    'get_token_path',
    'is_debug',
    
    # CLI functions
    'run_oauth_flow',
    'check_auth',
    'logout_user',
    
    # Exceptions
    'OAuthError',
    'AuthenticationError',
    'TokenRefreshError',
    'TokenStorageError',
    'ConfigurationError',
    'AuthorizationError',
]

