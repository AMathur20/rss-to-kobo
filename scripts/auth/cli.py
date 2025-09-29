"""
Command-line interface for OAuth authentication.
"""
import logging
import sys
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from typing import Optional, Any
from urllib.parse import urlparse, parse_qs

from . import config, exceptions
from .oauth_handler import OAuthHandler
from dropbox import Dropbox  # Add this import

logger = logging.getLogger(__name__)

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Simple HTTP server to handle OAuth callbacks."""
    
    def __init__(self, request, client_address, server):
        self.auth_code = None
        self.error = None
        super().__init__(request, client_address, server)
    
    def do_GET(self):
        """Handle GET requests to the callback URL."""
        # Parse the query parameters
        query = urlparse(self.path).query
        params = parse_qs(query)
        
        if 'code' in params:
            self.auth_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(
                b"<html><body><h1>Authentication successful!</h1>"
                b"<p>You can close this window and return to the application.</p></body></html>"
            )
        elif 'error' in params:
            self.error = params['error'][0]
            self.send_response(400)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Error: {self.error}".encode())
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"Invalid request")
        
        # Shutdown the server after handling the request
        def shutdown():
            self.server.shutdown()
        Thread(target=shutdown).start()


def run_oauth_flow(username: str) -> bool:
    """Run the OAuth 2.0 authorization code flow.
    
    Args:
        username: The username to authenticate
        
    Returns:
        bool: True if authentication was successful, False otherwise
    """
    try:
        oauth = OAuthHandler(username)
        
        # Step 1: Get authorization URL and open in browser
        auth_url = oauth.get_authorization_url()
        print(f"Opening authorization URL in your browser: {auth_url}")
        print("If the browser doesn't open, please copy and paste the URL into your browser.")
        
        # Try to open the URL in the default browser
        try:
            webbrowser.open(auth_url)
        except Exception as e:
            logger.warning(f"Could not open browser: {e}")
        
        # Step 2: Start a local server to handle the redirect
        oauth_config = config.get_oauth_config()
        port = oauth_config.get('redirect_port', 5000)
        
        with HTTPServer(('localhost', port), OAuthCallbackHandler) as httpd:
            print(f"Waiting for authorization response on port {port}...")
            # Run the server in a separate thread
            server_thread = Thread(target=httpd.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            
            # Wait for the server to handle the request
            server_thread.join(timeout=300)  # 5 minute timeout
            
            # Check if we got an auth code
            if hasattr(httpd, 'RequestHandlerClass'):
                handler = httpd.RequestHandlerClass
                if hasattr(handler, 'auth_code') and handler.auth_code:
                    # Complete the OAuth flow
                    redirect_url = f"http://localhost:{port}/?code={handler.auth_code}"
                    oauth.finish_authorization(redirect_url)
                    print("Successfully authenticated with Dropbox!")
                    return True
                elif hasattr(handler, 'error') and handler.error:
                    print(f"Authorization error: {handler.error}")
                else:
                    print("Authorization timed out or was cancelled.")
            
            return False
            
    except exceptions.AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        return False
    except Exception as e:
        logger.exception("Unexpected error during OAuth flow")
        return False


def check_auth(username: str) -> bool:
    """Check if the user is authenticated.
    
    Args:
        username: The username to check
        
    Returns:
        bool: True if authenticated, False otherwise
    """
    try:
        oauth = OAuthHandler(username)
        if oauth.is_authenticated():
            print(f"User '{username}' is authenticated with Dropbox.")
            return True
        else:
            print(f"User '{username}' is not authenticated.")
            return False
    except Exception as e:
        logger.error(f"Error checking authentication status: {e}")
        return False


def logout_user(username: str) -> bool:
    """Log out the specified user by removing their tokens.
    
    Args:
        username: The username to log out
        
    Returns:
        bool: True if logout was successful, False otherwise
    """
    try:
        oauth = OAuthHandler(username)
        if oauth.logout():
            print(f"Successfully logged out user '{username}'.")
            return True
        else:
            print(f"Failed to log out user '{username}'.")
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        return False


def get_authenticated_client(username: str) -> Optional[Any]:
    """Get an authenticated client for the specified user.
    
    Args:
        username: The username to get a client for
        
    Returns:
        An authenticated client if available, None otherwise
    """
    try:
        from dropbox import Dropbox
        from .oauth_handler import OAuthHandler
        
        handler = OAuthHandler(username)
        return handler.get_authenticated_client()
    except Exception as e:
        logger.error(f"Failed to get authenticated client: {e}")
        return None

def main():
    """Command-line interface for OAuth authentication."""
    import argparse
    
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='RSS to Kobo - Authentication Management',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''Examples:
  rss-auth login username     # Start OAuth login flow
  rss-auth logout username    # Remove saved tokens
  rss-auth status username    # Check authentication status
'''
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Login command
    login_parser = subparsers.add_parser('login', help='Authenticate with Dropbox')
    login_parser.add_argument('username', help='Your username')
    login_parser.add_argument('--no-browser', action='store_true', help='Print URL instead of opening browser')
    
    # Logout command
    logout_parser = subparsers.add_parser('logout', help='Remove authentication tokens')
    logout_parser.add_argument('username', help='Username to log out')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Check authentication status')
    status_parser.add_argument('username', help='Username to check')
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('auth.log')
        ]
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == 'login':
            print(f"Starting OAuth flow for user: {args.username}")
            if args.no_browser:
                auth_url = OAuthHandler(args.username).get_authorization_url()
                print(f"Please visit this URL to authorize the application:\n\n{auth_url}\n")
                auth_code = input("Enter the authorization code from the URL: ").strip()
                handler = OAuthHandler(args.username)
                tokens = handler.finish_authorization(auth_code)
                print("\nAuthentication successful!")
                print(f"Access token expires at: {tokens.get('expires_at')}")
            else:
                success = run_oauth_flow(args.username)
                if success:
                    print("\n✅ Authentication successful!")
                else:
                    print("\n❌ Authentication failed")
                    return 1
            
        elif args.command == 'logout':
            success = logout_user(args.username)
            if success:
                print(f"✅ Successfully logged out {args.username}")
            else:
                print(f"❌ Failed to log out {args.username}")
                return 1
                
        elif args.command == 'status':
            client = get_authenticated_client(args.username)
            if client:
                try:
                    account = client.users_get_current_account()
                    print(f"✅ Authenticated as: {account.name.display_name} ({account.email})")
                    return 0
                except Exception as e:
                    print(f"❌ Token is invalid or expired: {e}")
                    return 1
            else:
                print("❌ Not authenticated")
                return 1
                
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"\n❌ An error occurred: {e}")
        return 1


if __name__ == "__main__":
    main()
