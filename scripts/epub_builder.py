"""
EPUB generation module for RSS to Kobo.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup
from ebooklib import epub

from .utils import format_date, get_output_path, setup_logger

logger = setup_logger(__name__)


class EPUBCreator:
    """Class to handle EPUB creation from RSS feed items."""

    def __init__(self, user: str, title: str = "Daily RSS Digest") -> None:
        """Initialize the EPUB creator.

        Args:
            user: Username for the EPUB
            title: Base title for the EPUB
        """
        self.user = user
        self.title = f"{title} - {format_date()}"
        self.book: Optional[epub.EpubBook] = None
        self.chapters: List[epub.EpubHtml] = []

    def _init_book(self) -> None:
        """Initialize the EPUB book with metadata."""
        self.book = epub.EpubBook()

        # Set metadata
        self.book.set_identifier(f"rss-digest-{datetime.now().strftime('%Y%m%d')}")
        self.book.set_title(self.title)
        self.book.set_language("en")
        self.book.add_author("RSS to Kobo")

        # Add default CSS
        self._add_default_styling()

    def _add_default_styling(self) -> None:
        """Add default CSS styling for the EPUB."""
        css = """
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 2em;
        }
        h1 { font-size: 1.8em; }
        h2 { font-size: 1.4em; }
        h3 { font-size: 1.2em; }
        .article-meta {
            color: #666;
            font-style: italic;
            margin-bottom: 1em;
        }
        """
        style = epub.EpubItem(
            uid="style_default",
            file_name="styles/default.css",
            media_type="text/css",
            content=css,
        )
        if self.book:
            self.book.add_item(style)

    def _create_chapter(
        self, feed_name: str, articles: List[Dict[str, Any]]
    ) -> epub.EpubHtml:
        """Create a chapter for a feed.

        Args:
            feed_name: Name of the feed
            articles: List of articles in the feed

        Returns:
            EpubHtml chapter
        """
        # Create chapter
        chapter = epub.EpubHtml(
            title=feed_name,
            file_name=f"feed_{len(self.chapters)}.xhtml",
            lang="en",
        )

        # Add chapter content
        content = [f"<h1>{feed_name}</h1>"]

        for article in articles:
            # Add article title and metadata
            content.append(f'<h2>{article["title"]}</h2>')
            meta = []
            if "published" in article:
                meta.append(f'Published: {format_date(article["published"])}')
            if "author" in article:
                meta.append(f'By: {article["author"]}')
            if meta:
                content.append(f'<div class="article-meta">{" | ".join(meta)}</div>')

            # Add article content
            content.append(article.get("content", "<p>No content available</p>"))
            content.append("<hr/>")

        chapter.content = "\n".join(content)
        return chapter

    def add_feed(self, feed_name: str, articles: List[Dict[str, Any]]) -> None:
        """Add a feed's articles to the EPUB.

        Args:
            feed_name: Name of the feed
            articles: List of articles in the feed
        """
        if not self.book:
            self._init_book()

        chapter = self._create_chapter(feed_name, articles)
        if self.book:
            self.book.add_item(chapter)
            self.chapters.append(chapter)

    def generate(self) -> Path:
        """Generate the EPUB file.

        Returns:
            Path to the generated EPUB file

        Raises:
            ValueError: If no content is available to generate EPUB
            Exception: If there's an error during EPUB generation
        """
        if not self.book or not self.chapters:
            raise ValueError("No content to generate EPUB")

        # Create table of contents
        self.book.toc = [(chapter, []) for chapter in self.chapters]

        # Add navigation
        self.book.add_item(epub.EpubNcx())
        self.book.add_item(epub.EpubNav())

        # Define spine (order of content)
        self.book.spine = ["nav"] + self.chapters

        # Generate output path
        output_path = get_output_path(self.user)

        # Write the EPUB file
        try:
            epub.write_epub(str(output_path), self.book, {})
            logger.info("Generated EPUB: %s", output_path)
            return output_path
        except Exception as e:
            logger.error("Error generating EPUB: %s", e)
            raise


def build_epub(user: str, feeds_data: Dict[str, List[Dict[str, Any]]]) -> Path:
    """
    Build an EPUB from feed data.

    Args:
        user: Username for the EPUB
        feeds_data: Dictionary mapping feed names to lists of articles

    Returns:
        Path to the generated EPUB file
    """
    logger.info("Building EPUB for user: %s", user)
    creator = EPUBCreator(user)

    for feed_name, articles in feeds_data.items():
        logger.info("Adding %d articles from feed: %s", len(articles), feed_name)
        creator.add_feed(feed_name, articles)

    return creator.generate()
