""
Tests for the authentication CLI.
"""
import sys
from unittest import TestCase, mock
from http.server import HTTPServer
from threading import Thread

from scripts.auth import cli
from scripts.auth.oauth_handler import OAuthHandler


class TestAuthCLI(TestCase):
    """Test the authentication command-line interface."""
    
    @mock.patch('webbrowser.open')
    @mock.patch('scripts.auth.cli.OAuthHandler')
    @mock.patch('scripts.auth.cli.HTTPServer')
    def test_run_oauth_flow_success(self, mock_http_server, mock_oauth_handler, mock_webbrowser):
        """Test successful OAuth flow."""
        # Setup mocks
        mock_handler = mock.Mock()
        mock_handler.auth_code = 'test_code'
        mock_http_server.return_value.RequestHandlerClass = mock_handler
        
        mock_oauth = mock.Mock()
        mock_oauth.get_authorization_url.return_value = 'http://example.com/auth'
        mock_oauth.finish_authorization.return_value = {'access_token': 'test_token'}
        mock_oauth_handler.return_value = mock_oauth
        
        # Run the flow
        result = cli.run_oauth_flow('testuser')
        
        # Verify the result
        self.assertTrue(result)
        mock_webbrowser.assert_called_once_with('http://example.com/auth')
        mock_oauth.finish_authorization.assert_called_once()
    
    @mock.patch('sys.exit')
    @mock.patch('argparse.ArgumentParser.parse_args')
    @mock.patch('scripts.auth.cli.run_oauth_flow')
    def test_main_login_success(self, mock_run_oauth, mock_parse_args, mock_exit):
        """Test main function with login command."""
        # Setup mock args
        mock_args = mock.Mock()
        mock_args.command = 'login'
        mock_args.username = 'testuser'
        mock_parse_args.return_value = mock_args
        
        # Mock successful OAuth flow
        mock_run_oauth.return_value = True
        
        # Call main
        cli.main()
        
        # Verify the result
        mock_run_oauth.assert_called_once_with('testuser')
        mock_exit.assert_called_once_with(0)
    
    @mock.patch('sys.exit')
    @mock.patch('argparse.ArgumentParser.parse_args')
    @mock.patch('scripts.auth.cli.check_auth')
    def test_main_check_authenticated(self, mock_check_auth, mock_parse_args, mock_exit):
        """Test main function with check command when authenticated."""
        # Setup mock args
        mock_args = mock.Mock()
        mock_args.command = 'check'
        mock_args.username = 'testuser'
        mock_parse_args.return_value = mock_args
        
        # Mock authenticated check
        mock_check_auth.return_value = True
        
        # Call main
        cli.main()
        
        # Verify the result
        mock_check_auth.assert_called_once_with('testuser')
        mock_exit.assert_called_once_with(0)
    
    @mock.patch('sys.exit')
    @mock.patch('argparse.ArgumentParser.parse_args')
    @mock.patch('scripts.auth.cli.logout_user')
    def test_main_logout_success(self, mock_logout_user, mock_parse_args, mock_exit):
        """Test main function with logout command."""
        # Setup mock args
        mock_args = mock.Mock()
        mock_args.command = 'logout'
        mock_args.username = 'testuser'
        mock_parse_args.return_value = mock_args
        
        # Mock successful logout
        mock_logout_user.return_value = True
        
        # Call main
        cli.main()
        
        # Verify the result
        mock_logout_user.assert_called_once_with('testuser')
        mock_exit.assert_called_once_with(0)


class TestOAuthCallbackHandler(TestCase):
    """Test the OAuth callback handler."""
    
    def test_handle_callback_with_code(self):
        """Test handling a callback with an authorization code."""
        # Create a mock request
        class MockRequest:
            def makefile(self, *args, **kwargs):
                return [b"GET /?code=test_code HTTP/1.1"]
            
            def sendall(self, data):
                self.response = data
            
            def close(self):
                pass
        
        # Create a mock server
        class MockServer:
            def __init__(self):
                self.shutdown_called = False
            
            def shutdown(self):
                self.shutdown_called = True
        
        # Setup the test
        server = MockServer()
        request = MockRequest()
        
        # Create and handle the request
        handler = cli.OAuthCallbackHandler(request, ('127.0.0.1', 12345), server)
        handler.handle()
        
        # Verify the response
        self.assertEqual(handler.auth_code, 'test_code')
        self.assertTrue(server.shutdown_called)
        self.assertIn(b'Authentication successful!', request.response)
    
    def test_handle_callback_with_error(self):
        """Test handling a callback with an error."""
        # Create a mock request
        class MockRequest:
            def makefile(self, *args, **kwargs):
                return [b"GET /?error=access_denied HTTP/1.1"]
            
            def sendall(self, data):
                self.response = data
            
            def close(self):
                pass
        
        # Create a mock server
        class MockServer:
            def shutdown(self):
                pass
        
        # Setup the test
        server = MockServer()
        request = MockRequest()
        
        # Create and handle the request
        handler = cli.OAuthCallbackHandler(request, ('127.0.0.1', 12345), server)
        handler.handle()
        
        # Verify the response
        self.assertEqual(handler.error, 'access_denied')
        self.assertIn(b'Error: access_denied', request.response)
