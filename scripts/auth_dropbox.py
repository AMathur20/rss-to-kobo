#!/usr/bin/env python3
"""
Dropbox Authentication Helper for RSS to Kobo

This script helps users authenticate with Dropbox and store their credentials securely.
"""
import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List, Union, Tuple, cast

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.auth import run_oauth_flow, check_auth, logout_user
from scripts.auth.exceptions import AuthenticationError, TokenStorageError, OAuthError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_header() -> None:
    """Print a nice header for the script."""
    print("\n" + "=" * 60)
    print("RSS to Kobo - Dropbox Authentication".center(60))
    print("=" * 60 + "\n")

def check_requirements() -> bool:
    """Check if all required environment variables are set."""
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ["DROPBOX_APP_KEY", "DROPBOX_APP_SECRET"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("Error: The following required environment variables are not set:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nPlease create a .env file with these variables. See .env.template for an example.")
        return False
    return True

def main():
    """Main entry point for the authentication script."""
    parser = argparse.ArgumentParser(description="Manage Dropbox authentication for RSS to Kobo")
    subparsers = parser.add_subparsers(dest='command', required=True, help='Command to run')
    
    # Login command
    login_parser = subparsers.add_parser('login', help='Authenticate with Dropbox')
    login_parser.add_argument('username', help='Username to associate with the tokens')
    
    # Check command
    check_parser = subparsers.add_parser('check', help='Check authentication status')
    check_parser.add_argument('username', help='Username to check')
    
    # Logout command
    logout_parser = subparsers.add_parser('logout', help='Log out and remove tokens')
    logout_parser.add_argument('username', help='Username to log out')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Print header
    print_header()
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    try:
        if args.command == 'login':
            print(f"Initiating Dropbox authentication for user: {args.username}")
            print("A browser window will open for you to authorize the application.")
            print("If the browser doesn't open, you'll be provided with a URL to visit manually.\n")
            
            success = run_oauth_flow(args.username)
            if success:
                print("\n✅ Successfully authenticated with Dropbox!")
                print(f"Tokens have been securely stored for user: {args.username}")
                sys.exit(0)
            else:
                print("\n❌ Authentication failed. Please try again.")
                sys.exit(1)
                
        elif args.command == 'check':
            print(f"Checking authentication status for user: {args.username}")
            is_authenticated = check_auth(args.username)
            if is_authenticated:
                print("✅ User is authenticated with Dropbox.")
                sys.exit(0)
            else:
                print("❌ User is not authenticated or token is invalid/expired.")
                print("Run 'python auth_dropbox.py login <username>' to authenticate.")
                sys.exit(1)
                
        elif args.command == 'logout':
            print(f"Logging out user: {args.username}")
            success = logout_user(args.username)
            if success:
                print("✅ Successfully logged out. Tokens have been removed.")
                sys.exit(0)
            else:
                print("❌ Failed to log out. The user may not have been logged in.")
                sys.exit(1)
                
    except (OAuthError, AuthenticationError, TokenStorageError) as e:
        logger.error(f"Authentication error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception("An unexpected error occurred")
        sys.exit(1)

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments.
    
    Returns:
        Parsed command line arguments
    """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description='Manage Dropbox authentication for RSS to Kobo'
    )
    subparsers: argparse._SubParsersAction = parser.add_subparsers(
        dest='command',
        help='Command to run'
    )
    
    # Login command
    login_parser = subparsers.add_parser('login', help='Authenticate with Dropbox')
    login_parser.add_argument('username', help='Your username for this application')
    
    # Logout command
    logout_parser: argparse.ArgumentParser = subparsers.add_parser(
        'logout',
        help='Remove Dropbox authentication'
    )
    logout_parser.add_argument('username', help='Your username')
    
    # Status command
    status_parser: argparse.ArgumentParser = subparsers.add_parser(
        'status',
        help='Check authentication status'
    )
    status_parser.add_argument('username', help='Your username')
    
    return parser.parse_args()

def main() -> int:
    """Main entry point for the authentication script.
    
    Returns:
        int: Exit code (0 for success, non-zero for errors)
    """
    if not check_requirements():
        return 1
        
    args = parse_arguments()
    
    try:
        if args.command == 'login':
            print_header()
            print(f"Initiating Dropbox authentication for user: {args.username}")
            print("Please follow the instructions in your browser...\n")
            run_oauth_flow(args.username)
            print("\n✅ Authentication successful! You can now use the RSS to Kobo service.")
            return 0
            
        elif args.command == 'logout':
            print_header()
            if logout_user(args.username):
                print(f"✅ Successfully logged out user: {args.username}")
                return 0
            print(f"❌ Failed to log out user: {args.username}")
            return 1
            
        elif args.command == 'status':
            print_header()
            status = check_auth(args.username)
            if status['authenticated']:
                print(f"✅ User {args.username} is authenticated with Dropbox")
                print(f"   Account: {status.get('account_name', 'Unknown')}")
                print(f"   Email: {status.get('email', 'Unknown')}")
                return 0
            print(f"❌ User {args.username} is not authenticated")
            return 1
            
        # No command provided
        print("Error: No command specified. Use --help for usage information.")
        return 1
        
    except AuthenticationError as e:
        logger.error(f"Authentication error: {e}")
        return 1
    except TokenStorageError as e:
        logger.error(f"Token storage error: {e}")
        return 1
    except OAuthError as e:
        logger.error(f"OAuth error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
