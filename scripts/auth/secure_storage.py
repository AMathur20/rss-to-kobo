"""
Secure storage for OAuth tokens using encryption.
"""
import json
import logging
import os
from base64 import b64decode, b64encode
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .config import get_token_path

logger = logging.getLogger(__name__)

# Constants
SALT_LENGTH = 16
ITERATIONS = 100000
KEY_LENGTH = 32


# Use a fixed salt for development to ensure consistent key generation
DEV_SALT = b'rss2kobo_salt_123'  # Fixed salt for development

def generate_key_from_password(password: str, salt: Optional[bytes] = None) -> tuple[bytes, bytes]:
    """Generate a cryptographic key from a password and optional salt.
    
    Args:
        password: The password to derive the key from
        salt: Optional salt. If None, uses a development salt.
    """
    if salt is None:
        salt = DEV_SALT  # Use fixed salt for development
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LENGTH,
        salt=salt,
        iterations=ITERATIONS,
        backend=default_backend()
    )
    key = kdf.derive(password.encode())
    return b64encode(key), salt


class SecureTokenStorage:
    """Secure storage for OAuth tokens with encryption.
    
    Uses a fixed encryption key in development mode for easier debugging.
    In production, set the TOKEN_ENCRYPTION_KEY environment variable.
    """
    
    def __init__(self, username: str, password: Optional[str] = None):
        """Initialize secure storage for a user.
        
        Args:
            username: The username for token storage
            password: Optional password for encryption. If not provided, will check TOKEN_ENCRYPTION_KEY
                     environment variable, then fall back to a development key.
        """
        self.token_path = get_token_path(username)
        # Get password from parameter, then environment, then use default
        self.password = password or os.getenv('TOKEN_ENCRYPTION_KEY') or "dev-key-1234567890"
        self._fernet = None
        logger.debug(f"Initialized SecureTokenStorage for {username}, using {'custom' if password else 'default'} encryption")
        
        # Ensure token directory exists and has correct permissions
        try:
            self.token_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        except Exception as e:
            logger.warning(f"Could not set directory permissions: {e}")
            # Try without setting permissions if we can't set them
            self.token_path.parent.mkdir(parents=True, exist_ok=True)
        
    def _get_fernet(self) -> Fernet:
        """Get a Fernet instance for encryption/decryption."""
        if self._fernet is None:
            # Derive key from password
            key, _ = generate_key_from_password(self.password)
            self._fernet = Fernet(key)
        return self._fernet
    
    def load_tokens(self) -> Optional[Dict[str, Any]]:
        """Load and decrypt tokens from storage."""
        if not self.token_path.exists():
            logger.debug(f"Token file not found: {self.token_path}")
            return None
            
        try:
            logger.debug(f"Loading tokens from {self.token_path}")
            with open(self.token_path, 'rb') as f:
                encrypted_data = f.read()
            
            if not encrypted_data:
                logger.error(f"Token file is empty: {self.token_path}")
                return None
                
            # Decrypt the data
            fernet = self._get_fernet()
            try:
                decrypted_data = fernet.decrypt(encrypted_data)
            except InvalidToken as e:
                logger.error(f"Failed to decrypt token file (invalid token): {e}")
                return None
            
            try:
                tokens = json.loads(decrypted_data.decode('utf-8'))
                logger.debug(f"Successfully loaded tokens for {self.token_path.name}")
                return tokens
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse token file (invalid JSON): {e}")
                return None
            
        except Exception as e:
            return None
    
    def save_tokens(self, tokens: Dict[str, Any]) -> bool:
        """Encrypt and save tokens to storage."""
        try:
            # Ensure the directory exists with secure permissions
            self.token_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            
            # Add timestamp
            tokens['_saved_at'] = datetime.utcnow().isoformat()
            
            # Serialize and encrypt the tokens
            json_data = json.dumps(tokens, indent=2).encode('utf-8')
            fernet = self._get_fernet()
            encrypted_data = fernet.encrypt(json_data)
            
            # Write to file atomically
            temp_path = f"{self.token_path}.tmp"
            with open(temp_path, 'wb') as f:
                f.write(encrypted_data)
            
            # On Windows, we need to remove the destination file first if it exists
            if os.path.exists(self.token_path):
                os.unlink(self.token_path)
            os.rename(temp_path, self.token_path)
            
            # Set secure file permissions (0o600 = owner read/write only)
            try:
                os.chmod(self.token_path, 0o600)
            except OSError as e:
                logger.warning(f"Could not set file permissions: {e}")
            
            logger.info(f"Tokens saved to {self.token_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save tokens: {e}", exc_info=True)
            # Clean up temp file if it exists
            if 'temp_path' in locals() and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
            return False
    
    def clear_tokens(self) -> bool:
        """Remove stored tokens."""
        try:
            if self.token_path.exists():
                os.unlink(self.token_path)
                self.token_path.unlink()
            return True
        except OSError as e:
            logger.error(f"Failed to clear tokens: {e}")
            return False
