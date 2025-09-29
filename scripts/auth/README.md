# Authentication Module

This module handles OAuth 2.0 authentication with Dropbox, token management, and secure credential storage for the RSS to Kobo application.

## Components

### config.py
Handles configuration and environment variables for the authentication system.

### secure_storage.py
Provides secure, encrypted storage for OAuth tokens using Fernet encryption.

### exceptions.py
Custom exceptions for the authentication system.

## Usage

### Configuration
1. Copy `.env.template` to `.env` in the project root
2. Fill in your Dropbox app credentials
3. Configure any additional settings as needed

### Initializing Secure Storage
```python
from scripts.auth.secure_storage import SecureTokenStorage

# Create a secure storage instance for a user
storage = SecureTokenStorage("username", "optional_password")

# Save tokens
tokens = {
    "access_token": "your_access_token",
    "refresh_token": "your_refresh_token",
    "expires_at": 1234567890
}
storage.save_tokens(tokens)

# Load tokens
loaded_tokens = storage.load_tokens()
```

### Handling Configuration
```python
from scripts.auth import config

# Get OAuth configuration
oauth_config = config.get_oauth_config()

# Get token path for a user
token_path = config.get_token_path("username")
```

## Security Notes
- Tokens are encrypted before being written to disk
- File permissions are set to restrict access
- A strong encryption key is derived from the provided password
- The `.env` file is excluded from version control

## Testing
Run the test suite with:
```bash
pytest scripts/tests/
```
