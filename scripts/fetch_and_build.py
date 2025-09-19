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
from .utils import clean_html, load_feeds_config, setup_logger

logger = setup_logger(__name__)


class FeedFetcher:
    """Handle fetching and processing of RSS feeds."""

    def __init__(self, user: str) -> None:
        """Initialize the fetcher for a specific user."""
        self.user = user
        self.feeds = self._load_feeds()

    def _load_feeds(self) -> Dict[str, Dict[str, Any]]:
        """Load and validate feed configuration."""
        try:
            config = load_feeds_config(self.user)
            if not config or "feeds" not in config or not isinstance(config["feeds"], list):
                logger.error("Invalid feeds configuration: 'feeds' list not found")
                return {}

            # Convert list of feeds to dict by URL for easier access
            return {
                feed["url"]: {
                    "name": feed.get("name", self._get_domain_name(feed["url"])),
                    "max_articles": int(feed.get("max_articles", 5)),
                }
                for feed in config["feeds"]
                if "url" in feed
            }
        except Exception as e:
            logger.error("Error loading feed configuration: %s", e)
            return {}

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
        """Fetch all configured feeds."""
        if not self.feeds:
            logger.error("No feeds configured or error loading configuration")
            return {}

        results = {}
        for url, config in self.feeds.items():
            feed_name = config["name"]
            max_articles = config["max_articles"]

            articles = self._fetch_feed(url, max_articles)
            if articles:
                results[feed_name] = articles
                logger.info("Fetched %d articles from %s", len(articles), feed_name)
            else:
                logger.warning("No articles fetched from %s", feed_name)

            # Be nice to servers
            time.sleep(1)

        return results


def main() -> int:
    """Handle command-line interface for fetching feeds and building EPUB.

    Returns:
        int: Exit code (0 for success, non-zero for errors)
    """
    parser = argparse.ArgumentParser(description="Fetch RSS feeds and generate EPUB for Kobo")
    parser.add_argument("--user", required=True, help="Username for feed configuration")
    parser.add_argument("--output", help="Output EPUB file path (default: auto-generated)")

    args = parser.parse_args()

    # Fetch articles from all feeds
    fetcher = FeedFetcher(args.user)
    feeds_data = fetcher.fetch_all()

    if not feeds_data:
        logger.error("No feed data available to generate EPUB")
        return 1

    # Generate EPUB
    try:
        epub_path = build_epub(args.user, feeds_data)
        logger.info("Successfully generated EPUB: %s", epub_path)
        return 0
    except Exception as e:
        logger.error("Error generating EPUB: %s", e, exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
