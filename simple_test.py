#!/usr/bin/env python3
"""
Simple test script for RSS to Kobo application.

This script provides a simplified way to test the core functionality
of the RSS to Kobo application.
"""

import logging
import sys
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def create_sample_config():
    """Create a sample configuration file for testing."""
    config_path = Path("config/feeds/test_user.yaml")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    sample_config = """
    # Test RSS Feed Configuration
    feeds:
      - name: "BBC News"
        url: "http://feeds.bbci.co.uk/news/rss.xml"
        max_items: 3
        enabled: true
    
    output:
      title: "Test RSS Digest"
      author: "RSS to Kobo"
      language: "en"
      directory: "test_output"
      filename_pattern: "test_%Y%m%d.epub"
      description: "A test RSS digest"
    """
    
    with open(config_path, 'w') as f:
        f.write(sample_config)
    
    logger.info(f"Created sample configuration at {config_path}")
    return config_path

def test_epub_creation():
    """Test EPUB creation with sample data."""
    from scripts.epub_builder import EPUBCreator
    
    logger.info("Testing EPUB creation with sample data...")
    
    try:
        # Create EPUB with test data
        creator = EPUBCreator(
            user="test_user",
            title="Test EPUB",
            author="Test Author",
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
        
        # Create output directory if it doesn't exist
        output_dir = Path("test_output")
        output_dir.mkdir(exist_ok=True)
        
        # Save the EPUB
        output_path = output_dir / "test_output.epub"
        creator.save(output_path)
        
        if output_path.exists():
            file_size = output_path.stat().st_size / 1024  # in KB
            logger.info(f"Successfully created test EPUB: {output_path} ({file_size:.1f} KB)")
            return True
        else:
            logger.error("Failed to create EPUB file")
            return False
            
    except Exception as e:
        logger.error(f"Error in EPUB creation test: {e}", exc_info=True)
        return False

def main():
    """Run the simple test suite."""
    logger.info("Starting simple test suite...")
    
    # Create sample config
    config_path = create_sample_config()
    
    # Test EPUB creation
    logger.info("\n=== Testing EPUB Creation ===")
    if test_epub_creation():
        logger.info("✓ EPUB creation test passed")
    else:
        logger.error("✗ EPUB creation test failed")
        return 1
    
    logger.info("\nAll tests completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
