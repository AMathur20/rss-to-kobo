""
Tests for the OAuth handler module.
"""
import json
import time
from datetime import datetime, timedelta
from unittest import TestCase, mock

import pytest
from dropbox.oauth import OAuth2FlowNoRedirectResult

from scripts.auth.oauth_handler import OAuthHandler
from scripts.auth import exceptions
from scripts.auth.secure_storage import SecureTokenStorage


class TestOAuthHandler(TestCase):
    """Test OAuth handler functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.username = "testuser"
        self.handler = OAuthHandler(self.username)
        self.test_tokens = {
            'access_token': 'test_access_token',
            'refresh_token': 'test_refresh_token',
            'token_type': 'bearer',
            'expires_at': int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
            'account_id': 'test_account_id',
            'user_id': 'test_user_id',
        }
        
        # Mock the secure storage
        self.mock_storage = mock.Mock(spec=SecureTokenStorage)
        self.handler.storage = self.mock_storage
    
    @mock.patch('scripts.auth.oauth_handler.DropboxOAuth2FlowNoRedirect')
    def test_get_authorization_url(self, mock_flow):
        """Test getting authorization URL."""
        # Mock the flow
        mock_flow.return_value.start.return_value = "http://example.com/auth"
        
        url = self.handler.get_authorization_url()
        self.assertEqual(url, "http://example.com/auth")
        mock_flow.return_value.start.assert_called_once()
    
    @mock.patch('scripts.auth.oauth_handler.DropboxOAuth2FlowNoRedirect')
    def test_finish_authorization_success(self, mock_flow):
        """Test successful authorization flow completion."""
        # Mock the flow result
        mock_result = mock.Mock(spec=OAuth2FlowNoRedirectResult)
        mock_result.access_token = 'test_token'
        mock_result.refresh_token = 'test_refresh_token'
        mock_result.token_type = 'bearer'
        mock_result.account_id = 'test_account_id'
        mock_result.user_id = 'test_user_id'
        mock_result.expires_in = 14400  # 4 hours
        
        mock_flow.return_value.finish.return_value = mock_result
        
        # Mock storage
        self.mock_storage.save_tokens.return_value = True
        
        # Call the method
        result = self.handler.finish_authorization("http://example.com/callback?code=test_code")
        
        # Verify the result
        self.assertEqual(result['access_token'], 'test_token')
        self.assertEqual(result['refresh_token'], 'test_refresh_token')
        self.assertIn('expires_at', result)
        self.mock_storage.save_tokens.assert_called_once()
    
    def test_is_token_expired(self):
        """Test token expiration check."""
        # Token expires in 1 hour
        future_time = int((datetime.utcnow() + timedelta(hours=1)).timestamp())
        self.assertFalse(self.handler._is_token_expired({'expires_at': future_time}))
        
        # Token expired 1 hour ago
        past_time = int((datetime.utcnow() - timedelta(hours=1)).timestamp())
        self.assertTrue(self.handler._is_token_expired({'expires_at': past_time}))
        
        # No expiration time (long-lived token)
        self.assertFalse(self.handler._is_token_expired({}))
    
    @mock.patch('scripts.auth.oauth_handler.Dropbox')
    def test_refresh_tokens_success(self, mock_dropbox):
        """Test successful token refresh."""
        # Mock the Dropbox client
        mock_client = mock.Mock()
        mock_client._oauth2_access_token = 'new_access_token'
        mock_dropbox.return_value = mock_client
        
        # Mock storage
        self.mock_storage.save_tokens.return_value = True
        
        # Call the method
        result = self.handler.refresh_tokens('test_refresh_token')
        
        # Verify the result
        self.assertEqual(result['access_token'], 'new_access_token')
        self.assertEqual(result['refresh_token'], 'test_refresh_token')
        self.mock_storage.save_tokens.assert_called_once()
    
    @mock.patch('scripts.auth.oauth_handler.Dropbox')
    def test_get_authenticated_client(self, mock_dropbox):
        """Test getting an authenticated client."""
        # Mock get_valid_tokens
        self.handler.get_valid_tokens = mock.Mock(return_value={'access_token': 'test_token'})
        
        # Call the method
        client = self.handler.get_authenticated_client()
        
        # Verify the client was created with the correct token
        self.assertIsNotNone(client)
        mock_dropbox.assert_called_once_with(
            oauth2_access_token='test_token',
            user_agent=mock.ANY
        )
    
    @mock.patch('scripts.auth.oauth_handler.Dropbox')
    def test_is_authenticated_success(self, mock_dropbox):
        """Test successful authentication check."""
        # Mock get_valid_tokens to return valid tokens
        self.handler.get_valid_tokens = mock.Mock(return_value={'access_token': 'test_token'})
        
        # Mock the Dropbox client
        mock_client = mock.Mock()
        mock_dropbox.return_value = mock_client
        
        # Call the method
        result = self.handler.is_authenticated()
        
        # Verify the result
        self.assertTrue(result)
        mock_client.users_get_current_account.assert_called_once()
    
    def test_logout(self):
        """Test logging out."""
        # Mock storage
        self.mock_storage.clear_tokens.return_value = True
        
        # Call the method
        result = self.handler.logout()
        
        # Verify the result
        self.assertTrue(result)
        self.mock_storage.clear_tokens.assert_called_once()


if __name__ == "__main__":
    pytest.main()
