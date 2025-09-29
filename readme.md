# 📚 RSS to Kobo (Headless Server Edition)

A headless server application that automatically fetches articles from RSS feeds, bundles them into EPUBs, and syncs them to Kobo e-readers via Dropbox. Designed to run on servers without a graphical interface.

## 📋 Table of Contents

- [🔧 Key Features](#-key-features)
- [🚀 Quick Start](#-quick-start)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [🔐 Authentication](#-authentication)
- [⚙️ Configuration](#️-configuration)
  - [Feed Configuration](#feed-configuration)
- [🚀 Running the Application](#-running-the-application)
- [🖥️ Server Deployment](#️-server-deployment)
- [🐛 Troubleshooting](#-troubleshooting)
- [📚 Documentation](#-documentation)
- [🚀 Roadmap](#-roadmap)
- [📂 Project Structure](#-project-structure)
- [📝 License](#-license)

## 🔧 Key Features

- **Headless Operation**: No GUI or display server required
- **Automated Sync**: Scheduled fetching and syncing of RSS feeds
- **Secure Storage**: Encrypted token storage with password protection
- **Systemd Integration**: Easy daemon setup with auto-restart
- **Container Ready**: Lightweight and container-friendly
- **Resource Efficient**: Low memory and CPU footprint
- **Comprehensive Logging**: Built-in log rotation and management

## 🚀 Quick Start

### Prerequisites
- **Server Environment** (Ubuntu/Debian recommended)
- Python 3.10 or later
- Dropbox account with developer access
- Kobo e-reader with Dropbox support
- Required system packages:
  ```bash
  sudo apt-get update
  sudo apt-get install -y python3-venv python3-pip
  ```

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/AMathur20/rss-to-kobo.git
   cd rss-to-kobo
   ```

2. Set up a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

## 🔐 Authentication

### Manual Authentication

1. **Get the authorization URL**:
   ```bash
   python -c "from scripts.auth.oauth_handler import OAuthHandler; print(OAuthHandler('your_username').get_authorization_url())"
   ```

2. **Authorize the App**
   - Open the URL in a browser on any device
   - Log in to Dropbox and authorize the app
   - You'll be redirected to a localhost URL (this will fail, which is expected)
   - Copy the full redirect URL from the browser's address bar

3. **Complete Authentication**:
   ```bash
   python -c "from scripts.auth.oauth_handler import OAuthHandler; print(OAuthHandler('your_username').finish_authorization('PASTE_REDIRECT_URL_HERE'))"
   ```

4. **Verify Authentication Status**:
   ```bash
   python scripts/auth_dropbox.py status your_username
   ```
   This will show the current authentication status and token expiration information.

## ⚙️ Configuration

### Feed Configuration
Create a YAML configuration file in `config/feeds/<username>.yaml`:

```yaml
feeds:
  - name: "Tech News"
    url: "https://example.com/tech/rss"
    max_articles: 5
    enabled: true

  - name: "Science Daily"
    url: "https://example.com/science/feed"
    max_articles: 3
    enabled: true

# Output settings
output:
  title: "My Daily Digest"
  author: "RSS to Kobo"
  language: "en"
  directory: "output"
  filename_pattern: "%Y%m%d-news.epub"
  description: "A curated collection of articles from your favorite sources"

# Dropbox settings (must be within Dropbox/Apps/Kobo/ for Kobo sync)
dropbox:
  target_folder: "/RSS Feeds"
  filename: "Daily-Digest.epub"
```

## 🚀 Running the Application

### Basic Usage
```bash
# Run with a specific user's configuration
python rss_to_kobo.py --user your_username

# Debug mode with verbose output
python rss_to_kobo.py --user your_username --debug
```

### Scheduled Execution
For automated execution, set up a cron job or systemd timer:

```bash
# Example crontab entry to run daily at 6 AM
0 6 * * * cd /path/to/rss-to-kobo && ./venv/bin/python rss_to_kobo.py --user your_username
```

## 🖥️ Server Deployment

### System Requirements
- **OS**: Linux (Ubuntu/Debian recommended)
- **Python**: 3.10+
- **Storage**: 100MB free space minimum
- **Memory**: 512MB RAM (1GB recommended)
- **Network**: Outbound HTTPS to Dropbox API

### Systemd Service
Example service file at `systemd/rss-to-kobo@.service`:

```ini
[Unit]
Description=RSS to Kobo Service for %i
After=network.target

[Service]
Type=oneshot
User=%i
Environment=PYTHONUNBUFFERED=1
WorkingDirectory=/path/to/rss-to-kobo
ExecStart=/path/to/venv/bin/python rss_to_kobo.py --user %i
```

### Docker
```bash
docker build -t rss-to-kobo .
docker run -d \
  -v /path/to/config:/app/config \
  -v /path/to/output:/app/output \
  -e DROPBOX_APP_KEY=your_key \
  -e DROPBOX_APP_SECRET=your_secret \
  rss-to-kobo
```

## 🐛 Troubleshooting

### Common Issues

#### Authentication Failures
- Verify Dropbox app has `files.content.write` permission
- Check token expiration (tokens last 4 hours by default)
- Ensure system clock is synchronized (NTP)
- View authentication logs: `tail -f dropbox_auth.log`

#### Feed Parsing Errors
```bash
# Test feed URL accessibility
curl -I https://example.com/your-feed-url

# Check feed content
curl https://example.com/your-feed-url | xmllint --format -
```

#### Missing Dependencies
```bash
# Install system requirements
sudo apt-get install -y python3-venv python3-pip

# Reinstall Python dependencies
pip install -r requirements.txt --force-reinstall
```

### Logging
Logs are available in these locations:
- **Systemd service**: `journalctl -u rss-to-kobo@username.service`
- **Manual execution**: `rss-to-kobo.log` in current directory
- **Docker**: `docker logs rss-to-kobo`

Set log level via environment variable:
```bash
export RSS_TO_KOBO_LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

## 📚 Documentation

For more detailed information, please refer to the following guides:

- [Authentication Guide](docs/authentication.md) - Complete guide to setting up and managing authentication
- [Troubleshooting Guide](docs/troubleshooting.md) - Solutions to common issues and problems

## 🚀 Roadmap

### Planned Features

1. **Web Interface**
   - User-friendly dashboard for feed management
   - Token management UI
   - Real-time status and logs

2. **Enhanced Error Handling**
   - Better error recovery and retry mechanisms
   - Detailed error reporting
   - Automatic notification of failures

3. **Deployment Improvements**
   - Docker containerization
   - Systemd service templates
   - Automated backups

## 📂 Project Structure

```
.
├── config/                    # Configuration files
│   └── feeds/                # User feed configurations
│       ├── sample_user.yaml  # Example configuration
│       └── <username>.yaml   # User configurations
├── scripts/                  # Core application code
│   ├── auth/                # Authentication handlers
│   ├── epub_builder.py      # EPUB generation
│   └── feed_fetcher.py      # RSS feed processing
├── tests/                   # Test suite
├── .env.template           # Environment template
├── requirements.txt        # Dependencies
├── rss_to_kobo.py         # Main entry point
└── README.md              # This file
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with Python and community contributions
- Special thanks to all contributors for their valuable input
- Dropbox API team for their excellent documentation

## 🔗 Additional Resources

- [Authentication Guide](docs/AUTHENTICATION.md)
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
- [API Documentation](docs/API.md)
