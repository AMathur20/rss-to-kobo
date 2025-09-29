#!/usr/bin/env python3
"""
Test script for RSS to Kobo application.

This script tests the main functionality of the RSS to Kobo application
without requiring command-line arguments.
"""

import logging
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import yaml

# Add the project root to the Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Mock the required modules
sys.modules['feedparser'] = MagicMock()
sys.modules['ebooklib'] = MagicMock()
sys.modules['ebooklib.epub'] = MagicMock()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def test_feed_fetcher():
    """Test the FeedFetcher class with mock data."""
    from scripts.fetch_and_build import FeedFetcher
    from unittest.mock import patch, MagicMock
    import feedparser
    
    logger.info("Testing FeedFetcher with mock data...")
    
    # Create a mock for feedparser.parse
    mock_feed = MagicMock()
    mock_feed.entries = [
        {
            'title': 'Test Article 1',
            'link': 'https://example.com/test1',
            'published': '2023-01-01T12:00:00Z',
            'author': 'Test Author',
            'content': [{'value': '<p>Test content 1</p>'}],
            'summary': 'Test summary 1',
            'description': 'Test description 1'
        },
        {
            'title': 'Test Article 2',
            'link': 'https://example.com/test2',
            'published': '2023-01-02T12:00:00Z',
            'author': 'Test Author 2',
            'content': [{'value': '<p>Test content 2</p>'}],
            'summary': 'Test summary 2',
            'description': 'Test description 2'
        }
    ]
    mock_feed.get.return_value = []
    mock_feed.bozo = 0
    
    # Create a mock for load_feeds_config
    mock_config = {
        'feeds': [
            {
                'name': 'Test Feed',
                'url': 'https://example.com/feed',
                'max_items': 5,
                'enabled': True
            }
        ],
        'output': {
            'title': 'Test Feed',
            'author': 'Test Author',
            'language': 'en'
        }
    }
    
    with patch('feedparser.parse', return_value=mock_feed), \
         patch('scripts.fetch_and_build.load_feeds_config', return_value=mock_config):
        
        # Initialize FeedFetcher with mock config
        fetcher = FeedFetcher("test_user")
        
        # Test _load_feeds
        feeds = fetcher._load_feeds()
        if not feeds:
            logger.error("No feeds loaded from mock configuration")
            return False
            
        logger.info(f"Loaded {len(feeds)} feeds from mock configuration")
        
        # Test fetch_all
        results = fetcher.fetch_all()
        if not results:
            logger.error("No articles were fetched from mock feed")
            return False
            
        total_articles = sum(len(articles) for articles in results.values())
        logger.info(f"Fetched {total_articles} articles from {len(results)} mock feeds")
        
        # Verify article data
        for feed_name, articles in results.items():
            logger.info(f"Feed: {feed_name} has {len(articles)} articles")
            for article in articles:
                required_fields = ['title', 'link', 'content']
                for field in required_fields:
                    if field not in article:
                        logger.error(f"Article is missing required field: {field}")
                        return False
        
        return True

def test_epub_creation():
    """Test EPUB creation with sample data."""
    from scripts.epub_builder import EPUBCreator
    from pathlib import Path
    import tempfile
    
    logger.info("Testing EPUB creation...")
    
    # Create a temporary directory for test output
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Create a sample EPUBCreator instance
            creator = EPUBCreator(
                user="test_user",
                title="Test EPUB",
                author="Test Creator",
                language="en"
            )
            
            # Add sample content
            sample_articles = [
                {
                    "title": "Test Article 1",
                    "link": "https://example.com/test1",
                    "published": "2023-01-01T12:00:00Z",
                    "author": "Test Author",
                    "content": "<p>This is a test article content.</p>"
                },
                {
                    "title": "Test Article 2",
                    "link": "https://example.com/test2",
                    "published": "2023-01-02T12:00:00Z",
                    "content": "<p>This is another test article content.</p>"
                }
            ]
            
            # Add a feed
            creator.add_feed("Test Feed", sample_articles)
            
            # Create the EPUB file
            output_path = Path(temp_dir) / "test_output.epub"
            creator.save(output_path)
            
            # Verify the file was created
            if not output_path.exists():
                logger.error("EPUB file was not created")
                return False
                
            if output_path.stat().st_size == 0:
                logger.error("EPUB file is empty")
                return False
                
            logger.info(f"Successfully created test EPUB: {output_path} (size: {output_path.stat().st_size} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"Error in test_epub_creation: {e}", exc_info=True)
            return False

def test_config_loading():
    """Test configuration loading with mock file."""
    from scripts.utils.general import load_feeds_config
    from unittest.mock import mock_open, patch
    import yaml
    
    logger.info("Testing configuration loading with mock file...")
    
    # Sample YAML configuration
    sample_config = """
    feeds:
      - name: "Test Feed"
        url: "https://example.com/feed"
        max_items: 5
        enabled: true
    
    output:
      title: "Test Configuration"
      author: "Test Author"
      language: "en"
      directory: "test_output"
      filename_pattern: "test-%Y%m%d.epub"
    
    dropbox:
      target_folder: "/Test/Feeds"
      filename: "test.epub"
    """
    
    # Mock the open function to return our sample config
    with patch('builtins.open', mock_open(read_data=sample_config)) as mock_file:
        try:
            # Patch the path checking to always return True
            with patch('pathlib.Path.exists', return_value=True):
                config = load_feeds_config("test_user")
                
                if not config:
                    logger.error("Failed to load mock configuration")
                    return False
                    
                # Verify required sections exist
                required_sections = ['feeds', 'output']
                for section in required_sections:
                    if section not in config:
                        logger.error(f"Missing required section in config: {section}")
                        return False
                
                logger.info("Successfully loaded mock configuration:")
                logger.info(f"- Title: {config.get('output', {}).get('title', 'N/A')}")
                logger.info(f"- Feeds configured: {len(config.get('feeds', []))}")
                
                # Verify feed configuration
                feeds = config.get('feeds', [])
                if not feeds:
                    logger.error("No feeds found in configuration")
                    return False
                    
                # Check required feed fields
                for feed in feeds:
                    required_fields = ['name', 'url']
                    for field in required_fields:
                        if field not in feed:
                            logger.error(f"Feed is missing required field: {field}")
                            return False
                
                return True
                
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error in test: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in test_config_loading: {e}", exc_info=True)
            return False

def main():
    """Run all tests."""
    tests = [
        ("Configuration Loading", test_config_loading),
        ("Feed Fetcher", test_feed_fetcher),
        ("EPUB Creation", test_epub_creation),
    ]
    
    success = True
    for name, test_func in tests:
        logger.info(f"\n=== Running test: {name} ===")
        try:
            if test_func():
                logger.info(f"✓ {name} passed")
            else:
                logger.error(f"✗ {name} failed")
                success = False
        except Exception as e:
            logger.error(f"✗ {name} failed with exception: {e}", exc_info=True)
            success = False
    
    if success:
        logger.info("\nAll tests passed successfully!")
        return 0
    else:
        logger.error("\nSome tests failed. Please check the logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
