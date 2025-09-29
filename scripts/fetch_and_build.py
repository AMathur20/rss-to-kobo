"""
Fetch RSS feeds and build EPUB for Kobo.
"""

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

import feedparser
from bs4 import BeautifulSoup

from .epub_builder import build_epub
from .utils import clean_html, load_feeds_config
from .utils.logging_utils import setup_logger

logger = setup_logger(__name__)


class FeedFetcher:
    """Handle fetching and processing of RSS feeds."""
    
    def __init__(self, user: str) -> None:
        """Initialize the fetcher for a specific user."""
        self.user = user
        self.feeds = self._load_feeds()
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load the user's configuration."""
        try:
            return load_feeds_config(self.user)
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return {}

    def _load_feeds(self) -> Dict[str, Dict[str, Any]]:
        """Load feed configuration for the user.

        Returns:
            Dictionary mapping feed names to their configuration
            
        Raises:
            ValueError: If configuration is invalid or missing required fields
        """
        try:
            config = load_feeds_config(self.user)
            
            if not config or not isinstance(config, dict):
                raise ValueError("Invalid configuration format: expected a dictionary")
                
            feeds = config.get('feeds', [])
            if not feeds or not isinstance(feeds, list):
                logger.warning("No feeds configured in the configuration file")
                feeds = []
                
            # Validate each feed configuration
            valid_feeds = {}
            for feed in feeds:
                if not isinstance(feed, dict):
                    logger.warning(f"Skipping invalid feed configuration: {feed}")
                    continue
                    
                name = feed.get('name')
                url = feed.get('url')
                
                if not name or not url:
                    logger.warning(f"Skipping feed with missing name or URL: {feed}")
                    continue
                    
                # Set default values
                feed.setdefault('max_items', 10)
                feed.setdefault('enabled', True)
                
                valid_feeds[name] = feed
                
            if not valid_feeds:
                logger.warning("No valid feeds found in the configuration")
                
            return valid_feeds
            
        except FileNotFoundError as e:
            error_msg = f"Configuration file not found: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e
            
        except yaml.YAMLError as e:
            error_msg = f"Error parsing configuration file: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e
            
        except Exception as e:
            error_msg = f"Unexpected error loading feed configuration: {e}"
            logger.error(error_msg, exc_info=True)
            raise ValueError(error_msg) from e

    @staticmethod
    def _get_domain_name(url: str) -> str:
        """Extract domain name from URL for default feed name."""
        try:
            netloc = urlparse(url).netloc
            return netloc.replace("www.", "").split(".")[0].title()
        except Exception:
            return "Unknown Feed"

    def _fetch_feed(self, url: str, max_articles: int = 5) -> List[Dict[str, Any]]:
        """Fetch and parse a single RSS feed."""
        try:
            logger.info("Fetching feed: %s", url)
            feed = feedparser.parse(url)

            if feed.get("bozo"):
                logger.warning("Feed parse error (%s): %s", url, feed.bozo_exception)
                return []

            articles = []
            for entry in feed.entries[:max_articles]:
                try:
                    # Extract content - try different possible fields
                    content = ""
                    for field in ["content", "summary", "description"]:
                        if field in entry:
                            content = (
                                entry[field][0]["value"]
                                if isinstance(entry[field], list)
                                else entry[field]
                            )
                            break

                    # Clean the HTML content
                    content = clean_html(content)

                    # Create article dict
                    article = {
                        "title": entry.get("title", "Untitled"),
                        "link": entry.get("link", ""),
                        "published": entry.get("published", ""),
                        "author": entry.get("author", ""),
                        "content": content,
                    }
                    articles.append(article)

                except Exception as e:
                    logger.warning("Error processing entry in %s: %s", url, e)

            return articles

        except Exception as e:
            logger.error("Error fetching feed %s: %s", url, e)
            return []

    def fetch_all(self) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch all configured feeds.
        
        Returns:
            Dictionary mapping feed names to lists of articles
            
        Raises:
            ValueError: If there are issues with the configuration
        """
        if not self.feeds:
            logger.error("No feeds configured or error loading configuration")
            return {}

        results = {}
        for feed_name, feed_config in self.feeds.items():
            if not feed_config.get('enabled', True):
                logger.info("Skipping disabled feed: %s", feed_name)
                continue
                
            url = feed_config.get('url')
            if not url:
                logger.warning("Skipping feed with no URL: %s", feed_name)
                continue
                
            max_articles = feed_config.get('max_items', 10)
            logger.info("Fetching feed: %s (max items: %d)", feed_name, max_articles)
            
            try:
                articles = self._fetch_feed(url, max_articles)
                if articles:
                    results[feed_name] = articles
                    logger.info("Fetched %d articles from %s", len(articles), feed_name)
                else:
                    logger.warning("No articles fetched from %s", feed_name)
                    
                # Be nice to servers
                time.sleep(1)
                    
            except Exception as e:
                logger.error("Error fetching feed %s: %s", feed_name, e, exc_info=True)
                continue
                
        if not results:
            logger.warning("No articles were fetched from any feeds")
            
        return results


def main() -> int:
    """Handle command-line interface for fetching feeds and building EPUB.

    Returns:
        int: Exit code (0 for success, non-zero for errors)
    """
    parser = argparse.ArgumentParser(description="Fetch RSS feeds and generate EPUB for Kobo")
    parser.add_argument("--user", required=True, help="Username for feed configuration")
    parser.add_argument("--output", help="Output EPUB file path (default: auto-generated)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Set up logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    try:
        logger.info("Starting feed fetch for user: %s", args.user)
        
        # Initialize fetcher and load configuration
        fetcher = FeedFetcher(args.user)
        
        # Fetch articles from all feeds
        feeds_data = fetcher.fetch_all()

        if not feeds_data:
            logger.error("No feed data available to generate EPUB")
            return 1
            
        # Get output path from config or use default
        output_path = None
        if args.output:
            output_path = Path(args.output)
        elif hasattr(fetcher, 'config') and fetcher.config.get('output'):
            output_config = fetcher.config['output']
            output_dir = Path(output_config.get('directory', 'output'))
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{args.user}_rss.epub"

        # Generate EPUB
        try:
            logger.info("Generating EPUB...")
            epub_path = build_epub(args.user, feeds_data, output_path=output_path, config=fetcher.config)
            logger.info("Successfully generated EPUB: %s", epub_path)
            return 0
            
        except Exception as e:
            logger.error("Error generating EPUB: %s", e, exc_info=True)
            return 1
            
    except Exception as e:
        logger.error("Fatal error: %s", e, exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
