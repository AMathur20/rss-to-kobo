# 🔐 Authentication & Security Guide

## Table of Contents
- [Environment Variables](#-environment-variables)
- [Authentication Flow](#-authentication-flow)
- [Token Management](#-token-management)
- [Token Refresh & Renewal](#-token-refresh--renewal)
- [Systemd Service Setup](#-systemd-service-setup)
- [Troubleshooting](#-troubleshooting)
- [Migration Guide](#-migration-guide)

## 🌐 Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Required for Dropbox OAuth
DROPBOX_APP_KEY=your_app_key
DROPBOX_APP_SECRET=your_app_secret

# Optional configuration
OAUTH_REDIRECT_PORT=5000  # Default port for OAuth callback
LOG_LEVEL=INFO            # DEBUG, INFO, WARNING, ERROR
```

## 🔄 Authentication Flow

### First-time Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Initialize authentication
python -m scripts.auth.cli login your_username
```

### Manual Authentication (for headless servers)
```bash
# Get authorization URL
python -c "from scripts.auth.oauth_handler import OAuthHandler; print(OAuthHandler('your_username').get_authorization_url())"

# After authorizing, complete authentication
python -c "from scripts.auth.oauth_handler import OAuthHandler; print(OAuthHandler('your_username').finish_authorization('AUTH_CODE'))"
```

### Verify Authentication
```bash
python -m scripts.auth.cli status your_username
```

## 🔑 Token Management

- **Storage Location**:
  - Linux/macOS: `~/.local/share/rss-to-kobo/tokens/`
  - Windows: `%APPDATA%\rss-to-kobo\tokens\`

- **Security**:
  - Tokens are encrypted using system-specific keys
  - File permissions are set to `600` (owner read/write only)
  - Refresh tokens are used to obtain new access tokens automatically

## 🔄 Token Refresh & Renewal

The system automatically handles token refresh when:
- An access token is about to expire (within 5 minutes of expiration)
- A refresh token is available
- The application has network connectivity

## 🚀 Systemd Service Setup

1. Create a systemd service file at `/etc/systemd/system/rss-to-kobo@.service`:
   ```ini
   [Unit]
   Description=RSS to Kobo Service for %i
   After=network.target

   [Service]
   Type=simple
   User=%i
   WorkingDirectory=/path/to/project
   EnvironmentFile=/path/to/project/.env
   ExecStart=/usr/bin/python3 -m rss_to_kobo --user %i
   Restart=on-failure
   RestartSec=30s

   [Install]
   WantedBy=multi-user.target
   ```

2. Create a timer at `/etc/systemd/system/rss-to-kobo@.timer`:
   ```ini
   [Unit]
   Description=Run RSS to Kobo every 4 hours for %i

   [Timer]
   OnBootSec=5min
   OnUnitActiveSec=4h
   RandomizedDelaySec=30m

   [Install]
   WantedBy=timers.target
   ```

3. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now rss-to-kobo@your_username.timer
   ```

## 🛠 Troubleshooting

### Common Issues

#### Authentication Fails
1. Verify your Dropbox app has the correct permissions
2. Check that the redirect URI is properly configured
3. Ensure system time is synchronized (NTP)

#### Token Refresh Fails
1. Check logs: `journalctl -u rss-to-kobo@your_username -f`
2. Verify the refresh token exists:
   ```bash
   ls -l ~/.local/share/rss-to-kobo/tokens/
   ```
3. Check file permissions:
   ```bash
   chmod 600 ~/.local/share/rss-to-kobo/tokens/your_username
   ```

#### Permission Denied Errors
1. Ensure the service user has write access:
   ```bash
   chown -R username:username ~/.local/share/rss-to-kobo
   ```

### Logs
- **Linux/Unix**: `~/.local/state/rss-to-kobo/rss-to-kobo.log`
- **Windows**: `%LOCALAPPDATA%\rss-to-kobo\logs\rss-to-kobo.log`

### Debug Mode
```bash
export LOG_LEVEL=DEBUG
python -m rss_to_kobo --user your_username
```

## 🔄 Migration Guide

### From v0.1.x to v0.2.0+

1. **Backup Existing Tokens**
   ```bash
   cp -r ~/.rss-to-kobo ~/rss-to-kobo-backup
   ```

2. **Update Configuration**
   - Remove deprecated configuration files
   - Update environment variables

3. **Re-authenticate Users**
   ```bash
   python -m scripts.auth.cli logout username
   python -m scripts.auth.cli login username
   ```

4. **Verify Functionality**
   ```bash
   python -m scripts.auth.cli status username
   python -m rss_to_kobo --user username --test
   ```

## 🔒 Security Best Practices

1. **Token Security**
   - Never commit tokens to version control
   - Use environment variables for sensitive data
   - Rotate tokens periodically

2. **File Permissions**
   - Set strict permissions on configuration files
   - Use dedicated system users for the service

3. **Network Security**
   - Use HTTPS for all API calls
   - Validate all input data
   - Implement rate limiting
