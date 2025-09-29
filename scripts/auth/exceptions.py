"""
Custom exceptions for the OAuth 2.0 implementation.
"""

class OAuthError(Exception):
    """Base exception for OAuth-related errors."""
    pass


class AuthenticationError(OAuthError):
    """Raised when authentication fails."""
    pass


class TokenRefreshError(OAuthError):
    """Raised when token refresh fails."""
    pass


class TokenStorageError(OAuthError):
    """Raised when there's an error accessing or modifying token storage."""
    pass


class ConfigurationError(OAuthError):
    """Raised when there's a configuration error."""
    pass


class AuthorizationError(OAuthError):
    """Raised when authorization is denied or fails."""
    pass
