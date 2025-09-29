# 🔧 Troubleshooting Guide

## Table of Contents
- [Authentication Issues](#-authentication-issues)
- [Token Refresh Problems](#-token-refresh-problems)
- [File Permission Errors](#-file-permission-errors)
- [Network Connectivity](#-network-connectivity)
- [Log Files](#-log-files)
- [Debug Mode](#-debug-mode)

## 🔐 Authentication Issues

### Symptoms
- "Failed to authenticate with Dropbox"
- "Invalid OAuth token"
- "Refresh token not found"

### Solutions
1. **Check Dropbox App Settings**
   - Ensure your app has the correct permissions:
     - `files.content.write`
     - `files.content.read`
     - `account_info.read`
   - Verify the redirect URI is correctly configured

2. **Re-authenticate**
   ```bash
   # Log out first
   python -m scripts.auth.cli logout your_username
   
   # Then log in again
   python -m scripts.auth.cli login your_username
   ```

3. **Check System Time**
   - Ensure your system time is synchronized:
     ```bash
     # On Linux
     sudo timedatectl set-ntp true
     
     # On Windows
     w32tm /resync
     ```

## 🔄 Token Refresh Problems

### Symptoms
- "Failed to refresh access token"
- "Token has expired"
- "Refresh token not found"

### Solutions
1. **Check Token File**
   - Verify the token file exists and is readable:
     ```bash
     ls -l ~/.local/share/rss-to-kobo/tokens/your_username
     ```
   - Check if it contains a refresh token:
     ```bash
     grep -A 2 refresh_token ~/.local/share/rss-to-kobo/tokens/your_username
     ```

2. **File Permissions**
   - Ensure the service user has write access:
     ```bash
     chmod 600 ~/.local/share/rss-to-kobo/tokens/your_username
     chown $USER:$USER ~/.local/share/rss-to-kobo/tokens/your_username
     ```

3. **Check Dropbox App Settings**
   - Ensure "Refresh token" is enabled in your Dropbox app settings
   - Verify the app has the correct permissions

## 📁 File Permission Errors

### Symptoms
- "Permission denied" when accessing files
- "Could not write to token file"

### Solutions
1. **Check Directory Permissions**
   ```bash
   # Create directories if they don't exist
   mkdir -p ~/.local/share/rss-to-kobo/tokens
   
   # Set correct ownership and permissions
   chmod 700 ~/.local/share/rss-to-kobo
   chmod 700 ~/.local/share/rss-to-kobo/tokens
   chown -R $USER:$USER ~/.local/share/rss-to-kobo
   ```

2. **SELinux/AppArmor**
   - Check if SELinux or AppArmor is blocking access:
     ```bash
     # For SELinux
     sudo ausearch -m avc -ts recent
     
     # For AppArmor
     sudo aa-status
     ```

## 🌐 Network Connectivity

### Symptoms
- "Connection timed out"
- "Failed to connect to Dropbox API"

### Solutions
1. **Check Internet Connection**
   ```bash
   ping dropbox.com
   curl -v https://api.dropboxapi.com/2/users/get_current_account
   ```

2. **Proxy Settings**
   - If behind a proxy, set the `HTTP_PROXY` and `HTTPS_PROXY` environment variables:
     ```bash
     export HTTP_PROXY=http://proxy.example.com:8080
     export HTTPS_PROXY=http://proxy.example.com:8080
     ```

3. **Firewall Rules**
   - Ensure outbound HTTPS (port 443) is allowed to:
     - `*.dropboxapi.com`
     - `*.dropbox.com`

## 📝 Log Files

### Location
- **Linux/Unix**: `~/.local/state/rss-to-kobo/rss-to-kobo.log`
- **Windows**: `%LOCALAPPDATA%\rss-to-kobo\logs\rss-to-kobo.log`

### Viewing Logs
```bash
# Follow logs in real-time
tail -f ~/.local/state/rss-to-kobo/rss-to-kobo.log

# Search for errors
grep -i error ~/.local/state/rss-to-kobo/rss-to-kobo.log

# View last 100 lines
tail -n 100 ~/.local/state/rss-to-kobo/rss-to-kobo.log
```

## 🐞 Debug Mode

Enable debug logging to get more detailed information:

```bash
# Set debug log level
export LOG_LEVEL=DEBUG

# Run with debug output
python -m rss_to_kobo --user your_username --debug
```

### Common Debug Scenarios

1. **Authentication Debugging**
   ```bash
   # Check token status
   python -m scripts.auth.cli status your_username --verbose
   
   # Test token refresh
   python -c "from scripts.auth.oauth_handler import OAuthHandler; print(OAuthHandler('your_username').get_valid_tokens())"
   ```

2. **Network Debugging**
   ```bash
   # Test connection to Dropbox API
   curl -v -X POST https://api.dropboxapi.com/2/users/get_current_account \
     --header "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     --header "Content-Type: application/json" \
     --data "null"
   ```

3. **File Operations**
   ```bash
   # Check file permissions
   ls -la ~/.local/share/rss-to-kobo/tokens/
   
   # Test file operations
   python -c "import os; print('Write test:', os.access(os.path.expanduser('~/.local/share/rss-to-kobo/tokens'), os.W_OK))"
   ```

## Still Having Issues?

If you're still experiencing problems:
1. Check the [GitHub Issues](https://github.com/yourusername/rss-to-kobo/issues) for similar problems
2. Enable debug logging and check the output
3. Create a new issue with:
   - Steps to reproduce
   - Error messages
   - Log output (with sensitive information redacted)
   - Environment details (OS, Python version, package versions)
