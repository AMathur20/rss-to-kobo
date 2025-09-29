""
Tests for the secure token storage module.
"""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.auth.secure_storage import SecureTokenStorage
from scripts.auth.exceptions import TokenStorageError


class TestSecureTokenStorage(unittest.TestCase):
    """Test secure token storage functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.username = "testuser"
        self.password = "testpassword123"
        self.test_tokens = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_at": 1234567890
        }
        
    def test_save_and_load_tokens(self):
        """Test saving and loading tokens with encryption."""
        storage = SecureTokenStorage(self.username, self.password)
        
        # Mock the token path to use our test directory
        with mock.patch('scripts.auth.secure_storage.get_token_path') as mock_path:
            test_path = Path(self.test_dir) / f"{self.username}_token.json"
            mock_path.return_value = test_path
            
            # Save tokens
            self.assertTrue(storage.save_tokens(self.test_tokens))
            self.assertTrue(test_path.exists())
            
            # Load tokens
            loaded_tokens = storage.load_tokens()
            self.assertEqual(loaded_tokens, self.test_tokens)
    
    def test_load_nonexistent_tokens(self):
        """Test loading tokens when no token file exists."""
        storage = SecureTokenStorage("nonexistent_user", self.password)
        self.assertIsNone(storage.load_tokens())
    
    def test_clear_tokens(self):
        """Test clearing stored tokens."""
        storage = SecureTokenStorage(self.username, self.password)
        
        with mock.patch('scripts.auth.secure_storage.get_token_path') as mock_path:
            test_path = Path(self.test_dir) / f"{self.username}_token.json"
            mock_path.return_value = test_path
            
            # Save then clear tokens
            storage.save_tokens(self.test_tokens)
            self.assertTrue(test_path.exists())
            
            self.assertTrue(storage.clear_tokens())
            self.assertFalse(test_path.exists())
    
    def test_clear_nonexistent_tokens(self):
        """Test clearing tokens when no token file exists."""
        storage = SecureTokenStorage("nonexistent_user", self.password)
        self.assertTrue(storage.clear_tokens())
    
    def test_generate_key_from_password(self):
        """Test key generation from password."""
        from scripts.auth.secure_storage import generate_key_from_password
        
        password = "testpassword"
        key1, salt1 = generate_key_from_password(password)
        key2, salt2 = generate_key_from_password(password, salt1)
        
        # Same password and salt should produce same key
        self.assertEqual(key1, key2)
        
        # Different salt should produce different key
        _, salt3 = generate_key_from_password(password)
        key3, _ = generate_key_from_password(password, salt3)
        self.assertNotEqual(key1, key3)
