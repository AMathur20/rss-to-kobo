"""
OAuth 2.0 handler for Dropbox authentication.
"""
import logging
import os
import webbrowser
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Union, Tuple, List, Type, TypeVar, cast

from dropbox import DropboxOAuth2FlowNoRedirect, Dropbox
from requests.exceptions import RequestException

from . import config, exceptions
from .secure_storage import SecureTokenStorage
from ..utils.logging_utils import log_execution_time

# Get logger for this module
logger = logging.getLogger(__name__)

# OAuth 2.0 scopes required by the application
SCOPES = [
    'files.content.write',
    'files.content.read',
    'account_info.read',
]

# Constants
DEFAULT_TOKEN_EXPIRY_BUFFER = 300  # 5 minutes in seconds

class OAuthHandler:
    """Handle OAuth 2.0 authentication flow and token management."""
    
    def __init__(self, username: str, password: Optional[str] = None) -> None:
        """Initialize the OAuth handler for a user.
        
        Args:
            username: The username to associate with the tokens
            password: Optional password for encrypting tokens. If not provided, a default will be used.
        """
        self.username = username
        self.oauth_flow = None
        self._client = None
        self.storage = SecureTokenStorage(username, password=password)
        logger.debug(f"Initialized OAuthHandler for user: {username}")
        
    @log_execution_time(logger)
    def _get_auth_flow(self) -> 'DropboxOAuth2FlowNoRedirect':
        """Get an OAuth 2.0 flow instance."""
        if self.oauth_flow is None:
            logger.debug("Initializing new OAuth flow")
            oauth_config = config.get_oauth_config()
            self.oauth_flow = DropboxOAuth2FlowNoRedirect(
                oauth_config['app_key'],
                oauth_config['app_secret'],
                token_access_type='offline',
                scope=SCOPES,
            )
            logger.debug("OAuth flow initialized with scopes: %s", SCOPES)
        else:
            logger.debug("Using existing OAuth flow")
            
        return self.oauth_flow
        
    @log_execution_time(logger)
    def _exchange_code_for_token(self, code: str) -> Dict[str, Optional[Union[str, int]]]:
        """Exchange an authorization code for an access token."""
        logger.debug("Exchanging authorization code for tokens")
        flow = self._get_auth_flow()
        try:
            # Use the flow's finish method to exchange the code for a token
            logger.debug("Calling OAuth flow.finish() with code")
            oauth_result = flow.finish(code)
            
            # Log token metadata (without sensitive values)
            token_data = {
                'access_token': '***' + (oauth_result.access_token[-6:] if oauth_result.access_token else ''),
                'has_refresh_token': bool(getattr(oauth_result, 'refresh_token', None)),
                'expires_in': getattr(oauth_result, 'expires_in', None),
                'token_type': getattr(oauth_result, 'token_type', 'bearer'),
                'account_id': getattr(oauth_result, 'account_id', ''),
                'uid': getattr(oauth_result, 'user_id', ''),
            }
            logger.debug("Successfully obtained OAuth tokens: %s", 
                        {k: v for k, v in token_data.items() if k != 'access_token'})
            
            # Return actual token data
            return {
                'access_token': oauth_result.access_token,
                'refresh_token': getattr(oauth_result, 'refresh_token', None),
                'expires_in': getattr(oauth_result, 'expires_in', None),
                'token_type': getattr(oauth_result, 'token_type', 'bearer'),
                'account_id': getattr(oauth_result, 'account_id', ''),
                'uid': getattr(oauth_result, 'user_id', ''),
            }
        except Exception as e:
            logger.error(f"Token exchange failed: {e}")
            raise exceptions.AuthorizationError("Failed to exchange authorization code for token") from e
    
    def get_authorization_url(self) -> str:
        """Get the authorization URL for the OAuth flow.
        
        Returns:
            The authorization URL to direct the user to
            
        Raises:
            exceptions.AuthenticationError: If there's an error generating the URL
        """
        try:
            flow = self._get_auth_flow()
            auth_url = flow.start()
            logger.debug(f"Generated authorization URL: {auth_url}")
            return auth_url
        except Exception as e:
            logger.error(f"Failed to get authorization URL: {e}")
            raise exceptions.AuthenticationError(f"Failed to generate authorization URL: {e}") from e
    
    def finish_authorization(self, authorization_code: str) -> Dict[str, str]:
        """Complete the OAuth flow with the authorization code.
        
        Args:
            authorization_code: The authorization code from Dropbox
            
        Returns:
            Dictionary containing the access token and related information
            
        Raises:
            exceptions.AuthorizationError: If authorization is denied or fails
            exceptions.TokenStorageError: If tokens cannot be stored
        """
        try:
            # Exchange the authorization code for tokens
            token_data = self._exchange_code_for_token(authorization_code)
            
            # Prepare the tokens for storage
            tokens = {
                'access_token': token_data['access_token'],
                'refresh_token': token_data.get('refresh_token'),
                'token_type': token_data.get('token_type', 'bearer'),
                'account_id': token_data.get('account_id', ''),
                'uid': token_data.get('uid', ''),
                'created_at': int(datetime.utcnow().timestamp())
            }
            
            # Add expiration if available
            if 'expires_in' in token_data and token_data['expires_in']:
                expires_at = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])
                tokens['expires_at'] = int(expires_at.timestamp())
            
            # Store the tokens
            logger.info(f"Saving tokens to: {self.storage.token_path}")
            if not self.storage.save_tokens(tokens):
                logger.error("Failed to save tokens")
                raise exceptions.TokenStorageError("Failed to store tokens")
            
            # Verify the tokens were saved
            if not self.storage.load_tokens():
                logger.error("Tokens were not saved correctly")
                raise exceptions.TokenStorageError("Failed to verify token storage")
                
            logger.info("Successfully saved tokens")
            
        except Exception as e:
            logger.error(f"Authorization error: {str(e)}", exc_info=True)
            raise exceptions.AuthorizationError(f"Authorization failed: {str(e)}") from e
    
    @log_execution_time(logger)
    def get_authenticated_client(self) -> 'Dropbox':
        """Get an authenticated Dropbox client.
        
        Returns:
            An authenticated Dropbox client instance
            
        Raises:
            exceptions.AuthenticationError: If authentication fails
        """
        logger.debug("Getting authenticated Dropbox client")
        tokens = self.get_valid_tokens()
        
        if not tokens:
            error_msg = "No tokens available for authentication"
            logger.error(f"{error_msg}: {self.storage.token_path}")
            raise exceptions.AuthenticationError(error_msg)
            
        if 'access_token' not in tokens:
            error_msg = "No access token in the token data"
            logger.error(f"{error_msg}: {self.storage.token_path}")
            raise exceptions.AuthenticationError(error_msg)
        
        logger.debug("Creating Dropbox client with access token")
        client = Dropbox(
            oauth2_access_token=tokens['access_token'],
            user_agent=f"RSS-to-Kobo/{getattr(config, '__version__', 'unknown')}"
        )
        
        logger.debug("Successfully created authenticated Dropbox client")
        return client
    
    def get_valid_tokens(self) -> Optional[Dict[str, Optional[Union[str, int]]]]:
        """Get valid tokens, refreshing if necessary.
        
        Returns:
{{ ... }}
            
        Raises:
            exceptions.TokenRefreshError: If token refresh fails
        """
        tokens = self.storage.load_tokens()
        if not tokens:
            return None
            
        # Check if token is expired or about to expire
        if self._is_token_expired(tokens):
            if 'refresh_token' not in tokens:
                logger.warning("Token expired and no refresh token available")
                return None
                
            logger.info("Access token expired, attempting to refresh...")
            try:
                tokens = self.refresh_tokens(tokens['refresh_token'])
            except exceptions.TokenRefreshError as e:
                logger.error(f"Failed to refresh token: {e}")
                raise
                
        return tokens
    
    @log_execution_time(logger)
    def refresh_tokens(self, refresh_token: str) -> Dict[str, Optional[Union[str, int]]]:
        """Refresh access tokens using a refresh token.
        
        Args:
            refresh_token: The refresh token to use
            
        Returns:
            New tokens including the new access token
            
        Raises:
            exceptions.TokenRefreshError: If token refresh fails
        """
        logger.info("Attempting to refresh access token")
        try:
            oauth_config = config.get_oauth_config()
            logger.debug("Using OAuth config with app key: %s", 
                        oauth_config['app_key'][:4] + '...' + oauth_config['app_key'][-2:] 
                        if oauth_config['app_key'] else 'None')
            
            # Use the refresh token to get a new access token
            logger.debug("Initializing Dropbox client with refresh token")
            dbx = Dropbox(
                oauth2_refresh_token=refresh_token,
                app_key=oauth_config['app_key'],
                app_secret=oauth_config['app_secret'],
            )
            
            # This will automatically refresh the token if needed
            logger.debug("Calling users_get_current_account to validate/refresh token")
            dbx.users_get_current_account()
            
            # Get the new access token from the client
            oauth2_access_token = dbx._oauth2_access_token
            logger.debug("Successfully obtained new access token")
            
            # Update tokens
            tokens = {
                'access_token': oauth2_access_token,
                'refresh_token': refresh_token,  # Refresh token remains the same
                'token_type': 'bearer',
                'refreshed_at': int(datetime.utcnow().timestamp())
            }
            
            # Store the new tokens
            logger.debug("Saving refreshed tokens to secure storage")
            if not self.storage.save_tokens(tokens):
                error_msg = "Failed to store refreshed tokens"
                logger.error(error_msg)
                raise exceptions.TokenStorageError(error_msg)
                
            logger.info("Successfully refreshed and stored new access token")
            return tokens
            
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise exceptions.TokenRefreshError("Failed to refresh access token") from e
    
    def _is_token_expired(self, tokens: Dict[str, Any]) -> bool:
        """Check if the access token is expired or about to expire.
        
        Args:
            tokens: Dictionary containing token information
            
        Returns:
            bool: True if token is expired or about to expire, False otherwise
        """
        if 'expires_at' not in tokens:
            # If we don't have an expiration, assume it's a long-lived token
            return False
            
        expiry_buffer = config.get_oauth_config().get('token_expiry_buffer', DEFAULT_TOKEN_EXPIRY_BUFFER)
        expiry_time = tokens['expires_at'] - expiry_buffer
        
        return datetime.utcnow().timestamp() >= expiry_time
    
    @log_execution_time(logger)
    def is_authenticated(self) -> bool:
        """Check if the user is authenticated with valid tokens.
        
        Returns:
            bool: True if authenticated, False otherwise
            
        Raises:
            exceptions.AuthenticationError: If there's an error during authentication check
        """
        logger.debug("Checking if user is authenticated")
        try:
            tokens = self.get_valid_tokens()
            if not tokens:
                logger.info("No valid tokens found - not authenticated")
                return False
                
            logger.debug("Tokens found, verifying with Dropbox API")
            # Verify the token works by making a simple API call
            client = self.get_authenticated_client()
            account = client.users_get_current_account()
            
            # Log successful authentication
            logger.info("Successfully authenticated with Dropbox as %s (%s)", 
                       account.name.display_name, account.email)
            
            # Save any updated tokens (e.g., if they were refreshed)
            if not self.storage.save_tokens(tokens):
                logger.warning("Failed to save updated tokens after refresh")
            else:
                logger.debug("Successfully saved updated tokens")
                
            return True
            
        except Exception as e:
            logger.error("Authentication check failed: %s", str(e), exc_info=logger.isEnabledFor(logging.DEBUG))
            return False
    
    def logout(self) -> bool:
        """Log out the user by removing their tokens and cleaning up the client.
        
        Returns:
            bool: True if logout was successful, False otherwise
        """
        try:
            if hasattr(self, '_client'):
                self._client = None
            return self.storage.delete_tokens()
        except Exception as e:
            logger.error(f"Logout failed: {e}")
            return False
