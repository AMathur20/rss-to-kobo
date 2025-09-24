# 📚 RSS to Kobo (Multi-User with Dropbox)

Automatically fetches articles from RSS feeds, bundles them into EPUBs, and syncs them to Kobo e-readers via Dropbox.

## ✨ Features
- **Multi-user** support with individual configurations
- **Flexible feed management** via YAML configuration
- **Clean EPUB output** with:
  - Table of Contents
  - Chapters per feed
  - Article titles with feed source
  - Responsive design
  - Automatic cover page
  - Article metadata (author, publication date)
- **Dropbox integration** with chunked upload support for large files
- **Modular architecture** for easy maintenance and testing
- **Comprehensive logging** for debugging and monitoring
- **Type hints** throughout the codebase for better maintainability

## 📂 Project Structure

```
.
├── feeds/                     # User feed configurations (YAML)
│   ├── example_user_feeds.yaml
│   └── <username>_feeds.yaml  # User-specific feed configurations
├── dropbox_tokens/            # Dropbox OAuth tokens (one per user)
│   └── <username>_token.json  # Securely stored access tokens
├── scripts/                   # Core Python package
│   ├── __init__.py           # Package initialization
│   ├── fetch_and_build.py    # Fetch feeds and build EPUB
│   ├── epub_builder.py       # EPUB generation logic
│   ├── upload_to_dropbox.py  # Dropbox upload handler
│   └── utils.py              # Shared utilities and helpers
├── output/                   # Generated EPUB files (gitignored)
├── systemd/                  # Systemd service files (optional)
├── requirements.txt          # Python dependencies
└── readme.md                # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or later
- Dropbox account with developer access
- Kobo e-reader with Dropbox support
- Required system packages (Ubuntu/Debian):
  ```bash
  sudo apt-get install python3-venv python3-pip
  ```

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/amathur20/rss-to-kobo.git
cd rss-to-kobo

# Create and activate virtual environment (recommended)
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Unix/macOS:
source venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure Feeds

1. Copy the example configuration:
   ```bash
   # On Windows:
   copy feeds\example_user_feeds.yaml feeds\your_username_feeds.yaml
   # On Unix/macOS:
   cp feeds/example_user_feeds.yaml feeds/your_username_feeds.yaml
   ```

2. Edit the file to add your preferred RSS feeds. Example:
   ```yaml
   # feeds/your_username_feeds.yaml
   feeds:
     - name: "Tech News"
       url: "https://example.com/feed"
       max_articles: 5  # Maximum number of articles to include from this feed
       
     - name: "Science Daily"
       url: "https://www.sciencedaily.com/rss/all.xml"
       max_articles: 3
   ```

   For a complete example with all available options, see `feeds/example_user_feeds.yaml`.

### 3. Set Up Dropbox

1. Create a Dropbox App at [Dropbox Developer Console](https://www.dropbox.com/developers/apps):
   - Click "Create app"
   - Choose "Scoped access"
   - Select **"Full Dropbox"** access (required for Kobo integration)
   - Name your app (e.g., "RSS to Kobo")
   - Click "Create app"

2. Generate an access token:
   - In your app settings, go to the "Permissions" tab
   - Under "OAuth 2", ensure these permissions are checked:
     - `files.content.write`
     - `files.content.read`
   - Go to the "Settings" tab
   - Under "OAuth 2", click "Generate" under "Generated access token"
   - Copy the generated token

**Important Note:** The Kobo e-reader requires files to be in the `/Apps/Rakuten Kobo/` folder in your Dropbox. For this to work, the app needs "Full Dropbox" access rather than just "App folder" access.

3. Save your token securely:
   ```bash
   # Create tokens directory if it doesn't exist
   mkdir -p dropbox_tokens
   
   # On Windows:
   echo {"access_token": "YOUR_ACCESS_TOKEN"} > dropbox_tokens\your_username_token.json
   
   # On Unix/macOS:
   echo '{"access_token": "YOUR_ACCESS_TOKEN"}' > dropbox_tokens/your_username_token.json
   
   # Set appropriate permissions (Unix/macOS):
   chmod 600 dropbox_tokens/your_username_token.json
   ```
   
   **Security Note:** Keep your token secret and never commit it to version control.
#### 🔄 Dropbox Token Management

#### Token Expiration
Dropbox access tokens typically expire after 4 hours. For long-running services:

1. **Check Token Expiration**:
   - Go to [Dropbox App Console](https://www.dropbox.com/developers/apps)
   - Select your app
   - Check the token expiration under "Generated access token"

2. **Renewing an Expired Token**:
   ```bash
   # Generate a new token from the Dropbox App Console
   # Then update the token file
   echo "YOUR_NEW_ACCESS_TOKEN" > /path/to/rss-to-kobo/dropbox_tokens/username_token.json
   
   # Verify the token works
   python3 -c "from scripts.upload_to_dropbox import DropboxUploader; print(DropboxUploader('username').test_connection())"
   ```

### 4. Test the Pipeline

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure your feeds** in `feeds/your_username_feeds.yaml`

3. **Set up Dropbox token**:
   - Get an access token from the [Dropbox App Console](https://www.dropbox.com/developers/apps)
   - Save it as `dropbox_tokens/your_username_token.json`

4. **Run the complete pipeline**:
   ```bash
   # Fetch feeds, build EPUB, and upload to Dropbox
   python rss_to_kobo.py --user your_username
   
   # To skip Dropbox upload (just fetch and build):
   # python rss_to_kobo.py --user your_username --no-upload
   
   # To specify a custom output filename in Dropbox:
   # python rss_to_kobo.py --user your_username --target "My-Daily-Reads.epub"
   ```
   
   For advanced usage, you can still run the individual scripts directly:
   ```bash
   # Just fetch feeds and build EPUB
   python -m scripts.fetch_and_build --user your_username
   
   # Just upload to Dropbox
   python -m scripts.upload_to_dropbox --user your_username
   ```

5. **Check the logs**:
   ```bash
   # On Windows:
   type %LOCALAPPDATA%\rss-to-kobo\rss-to-kobo.log
   
   # On Unix/macOS:
   cat ~/.local/state/rss-to-kobo/rss-to-kobo.log
   ```

### 5. Automate with systemd (Linux)

#### Single User Setup

1. Copy the systemd service and timer files:
   ```bash
   # Create systemd directory if it doesn't exist
   sudo mkdir -p /etc/systemd/system/
   
   # Copy the service and timer files
   sudo cp systemd/rss-to-kobo@.service systemd/rss-to-kobo@.timer /etc/systemd/system/
   ```

2. Edit the service file to match your setup:
   ```bash
   sudo nano /etc/systemd/system/rss-to-kobo@.service
   ```
   Update these paths if needed:
   - `WorkingDirectory`: Path to your RSS to Kobo directory
   - `ExecStart` and `ExecStartPost`: Path to your Python virtual environment

   Example configuration for a single user:
   ```ini
   [Unit]
   Description=RSS to Kobo for user %i
   After=network.target
   
   [Service]
   Type=oneshot
   User=%i
   Environment=PYTHONUNBUFFERED=1
   WorkingDirectory=/home/your_username/rss-to-kobo
   ExecStart=/home/your_username/rss-to-kobo/venv/bin/python rss_to_kobo.py --user %i
   
   # Logging configuration
   StandardOutput=journal
   StandardError=journal
   SyslogIdentifier=rss-to-kobo
   
   # Security options
   ProtectSystem=full
   PrivateTmp=yes
   NoNewPrivileges=yes
   
   # Resource limits
   MemoryLimit=512M
   CPUQuota=100%
   
   [Install]
   WantedBy=multi-user.target
   ```

#### Multi-User Setup on a Single Ubuntu Account

You can run multiple user configurations under a single Ubuntu account. Each user will have their own:

1. **Configuration Files**:
   - Feed configuration: `feeds/username_feeds.yaml`
   - Dropbox token: `dropbox_tokens/username_token.json`
   - (Optional) Custom virtual environment

2. **Systemd Service Setup**:
   ```bash
   # Create a service template that runs as the main user
   sudo cp systemd/rss-to-kobo@.service /etc/systemd/system/
   
   # Edit the service file to use the main user
   sudo nano /etc/systemd/system/rss-to-kobo@.service
   ```

   Example service file for single-user mode:
   ```ini
   [Unit]
   Description=RSS to Kobo for profile %i
   After=network.target
   
   [Service]
   Type=oneshot
   User=your_ubuntu_username  # Main Ubuntu user
   Environment=PYTHONUNBUFFERED=1
   WorkingDirectory=/path/to/rss-to-kobo
   ExecStart=/path/to/venv/bin/python rss_to_kobo.py --user %i
   
   # Logging configuration
   StandardOutput=journal
   StandardError=journal
   SyslogIdentifier=rss-to-kobo-%i
   
   # Security options
   ProtectSystem=full
   PrivateTmp=yes
   NoNewPrivileges=yes
   
   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable Timers for Each User**:
   ```bash
   # Enable timer for alice's configuration
   sudo systemctl enable --now rss-to-kobo@alice.timer
   
   # Enable timer for bob's configuration
   sudo systemctl enable --now rss-to-kobo@bob.timer
   ```

4. **File Structure Example**:
   ```
   /home/ubuntu/rss-to-kobo/
   ├── feeds/
   │   ├── alice_feeds.yaml
   │   └── bob_feeds.yaml
   ├── dropbox_tokens/
   │   ├── alice_token.json
   │   └── bob_token.json
   ├── output/
   │   ├── alice_*.epub
   │   └── bob_*.epub
   └── rss_to_kobo.py
   ```

5. **Managing Services**:
   ```bash
   # Check status for alice's service
   systemctl status rss-to-kobo@alice.timer
   
   # View logs for bob's service
   journalctl -u rss-to-kobo@bob.service
   
   # Manually trigger a run for alice
   systemctl start rss-to-kobo@alice.service
   
   # Disable bob's timer
   sudo systemctl disable --now rss-to-kobo@bob.timer
   ```

6. **Important Notes**:
   - All services run under the same Ubuntu user but with different configurations
   - Each user's EPUBs are generated separately
   - Logs include the username for easy filtering
   - Ensure proper file permissions for the main user to access all required files

### Customizing the Schedule

Edit the timer file to change when the service runs:

```bash
sudo systemctl edit rss-to-kobo@your_username.timer
```

Example schedules:
- Run daily at 6 AM (default): `OnCalendar=*-*-* 06:00:00`
- Run every 6 hours: `OnCalendar=*-*-* 00/6:00:00`
- Run at 8 AM and 8 PM: `OnCalendar=*-*-* 08,20:00:00`
- Run on weekdays at 7 AM: `OnCalendar=Mon..Fri 07:00:00`

After changing the timer, reload systemd:
```bash
sudo systemctl daemon-reload
sudo systemctl restart rss-to-kobo@your_username.timer
```

Use `man systemd.time` for more information on the time format.

## 🔍 Example Feed Configuration

See `feeds/example_user_feeds.yaml` for a comprehensive example with multiple categories and all available configuration options.

## 🔄 Kobo Integration

1. **Initial Setup**:
   - On your Kobo e-reader, go to **More** → **Dropbox**
   - Sign in to your Dropbox account
   - Find your EPUB in **Apps/Rakuten Kobo/**
   - Download to your device

2. **Automatic Updates**:
   - Keep Wi-Fi enabled on your Kobo
   - The device will check for updates when sleeping
   - New issues will appear in your library automatically

3. **Troubleshooting**:
   - If books don't sync, manually check for Dropbox updates in the Kobo menu
   - Ensure your Kobo is connected to Wi-Fi
   - Check that the EPUB files are being uploaded to the correct Dropbox folder

## 🛠️ Troubleshooting

### Common Issues

#### Missing Dependencies
```bash
# Install all required packages
pip install -r requirements.txt

# If you encounter specific module errors:
pip install feedparser ebooklib beautifulsoup4 dropbox pyyaml python-dateutil
```

#### Dropbox Upload Fails
- Verify your access token has `files.content.write` permission
- Check that the token hasn't expired (tokens can be revoked in Dropbox settings)
- Ensure the target folder exists in Dropbox (will be created automatically)
- Check network connectivity and firewall settings

#### EPUB Generation Issues
- Check logs in:
  - Windows: `%LOCALAPPDATA%\rss-to-kobo\rss-to-kobo.log`
  - Unix/macOS: `~/.local/state/rss-to-kobo/rss-to-kobo.log`
- Ensure feed URLs are accessible and return valid RSS/Atom feeds
- Verify that the output directory is writable

#### Feed Parsing Errors
- Check that the feed URL is correct and accessible
- Verify the feed returns valid XML
- Some feeds may require specific user-agents or headers

### Debugging

Run with increased verbosity:
```bash
python -m scripts.fetch_and_build --user your_username --verbose
python -m scripts.upload_to_dropbox --user your_username --verbose
```

### Log Files
Logs are stored in platform-specific locations:
- **Windows**: `%LOCALAPPDATA%\rss-to-kobo\rss-to-kobo.log`
- **macOS/Linux**: `~/.local/state/rss-to-kobo/rss-to-kobo.log`

To change the log level or location, set environment variables:
```bash
export RSS_TO_KOBO_LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
export RSS_TO_KOBO_LOG_FILE=/custom/path/to/logfile.log
```

## 🛠️ Local Development & Testing

### Setting up the development environment

1. **Create and activate a virtual environment**:
   ```bash
   # Create virtual environment
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Unix/macOS:
   source venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   # Run the complete pipeline
   python rss_to_kobo.py --user test_user
   
   # Run with debug output
   python rss_to_kobo.py --user test_user --verbose
   ```

4. **Testing** (optional):
   ```bash
   # Install test dependencies
   pip install pytest pytest-cov
   
   # Run tests
   pytest
   ```

## 🚀 Version 2.0 Roadmap

### Planned Features

1. **OAuth 2.0 with Refresh Tokens**
   - Implement OAuth 2.0 flow for Dropbox
   - Automatic token refresh before expiration
   - Secure token storage

2. **Web Interface**
   - User-friendly dashboard for feed management
   - Token management UI
   - Real-time status and logs

3. **Enhanced Error Handling**
   - Better error messages for token expiration
   - Automatic retry mechanisms
   - Email notifications for failures

4. **Multi-User Support**
   - User authentication
   - Per-user feed management
   - Role-based access control

5. **Deployment Improvements**
   - Docker containerization
   - Systemd service templates
   - Automated backups

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

1. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. Run tests:
   ```bash
   pytest tests/
   ```

3. Check code style:
   ```bash
   black .
   flake8
   mypy .
   ```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Thanks to all contributors who have helped improve this project
- Built with ❤️ using Python
