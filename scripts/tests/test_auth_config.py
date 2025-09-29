""
Tests for the authentication configuration module.
"""
import os
from unittest import TestCase, mock
from pathlib import Path

from scripts.auth import config


class TestConfig(TestCase):
    """Test configuration handling."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_env = {
            "DROPBOX_APP_KEY": "test_app_key",
            "DROPBOX_APP_SECRET": "test_app_secret",
            "OAUTH_REDIRECT_PORT": "1234",
            "DEBUG": "true"
        }
        
    @mock.patch.dict(os.environ, {"DROPBOX_APP_KEY": "test_key", "DROPBOX_APP_SECRET": "test_secret"})
    def test_get_oauth_config(self):
        """Test getting OAuth configuration."""
        config_data = config.get_oauth_config()
        self.assertEqual(config_data["app_key"], "test_key")
        self.assertEqual(config_data["app_secret"], "test_secret")
        self.assertEqual(config_data["redirect_port"], config.DEFAULT_OAUTH_REDIRECT_PORT)
    
    @mock.patch.dict(os.environ, {})
    def test_get_oauth_config_missing_required(self):
        """Test that missing required environment variables raise an error."""
        with self.assertRaises(ValueError):
            config.get_oauth_config()
    
    def test_get_token_path(self):
        """Test getting token path for a user."""
        username = "testuser"
        token_path = config.get_token_path(username)
        self.assertIn(username, str(token_path))
        self.assertTrue(str(token_path).endswith(".json"))
    
    @mock.patch.dict(os.environ, {"DEBUG": "true"})
    def test_is_debug_true(self):
        """Test debug mode detection when enabled."""
        self.assertTrue(config.is_debug())
    
    @mock.patch.dict(os.environ, {"DEBUG": "false"})
    def test_is_debug_false(self):
        """Test debug mode detection when disabled."""
        self.assertFalse(config.is_debug())
    
    @mock.patch.dict(os.environ, {})
    def test_is_debug_default(self):
        """Test debug mode default value."""
        self.assertFalse(config.is_debug())
