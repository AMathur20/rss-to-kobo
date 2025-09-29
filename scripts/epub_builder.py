"""
EPUB generation module for RSS to Kobo.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup
from ebooklib import epub

from .utils import format_date, get_output_path
from .utils.logging_utils import setup_logger

logger = setup_logger(__name__)


class EPUBCreator:
    """Class to handle EPUB creation from RSS feed items."""

    def __init__(self, user: str, title: str = "Daily RSS Digest", 
                 author: str = "RSS to Kobo", language: str = "en") -> None:
        """Initialize the EPUB creator.

        Args:
            user: Username for the EPUB
            title: Base title for the EPUB
            author: Author name for the EPUB
            language: Language code for the EPUB
        """
        self.user = user
        self.title = f"{title} - {format_date()}"
        self.author = author
        self.language = language
        self.book: Optional[epub.EpubBook] = None
        self.chapters: List[epub.EpubHtml] = []

    def _init_book(self) -> None:
        """Initialize the EPUB book with metadata."""
        if self.book is not None:
            return
            
        self.book = epub.EpubBook()
        
        # Set basic metadata
        self.book.set_identifier(f"rss-digest-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        self.book.set_title(self.title)
        self.book.set_language(self.language)
        self.book.add_author(self.author)
        
        # Add creation date
        self.book.add_metadata('DC', 'date', datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))
        
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
            logger.error("Error writing EPUB file: %s", e, exc_info=True)
            raise


def build_epub(
    user: str, 
    feeds_data: Dict[str, List[Dict[str, Any]]],
    output_path: Optional[Path] = None,
    config: Optional[Dict[str, Any]] = None
) -> Path:
    """
    Build an EPUB from feed data.

    Args:
        user: Username for the EPUB
        feeds_data: Dictionary mapping feed names to lists of articles
        output_path: Optional path to save the EPUB file
        config: Optional configuration dictionary

    Returns:
        Path to the generated EPUB file
        
    Raises:
        ValueError: If there's an error building the EPUB
    """
    try:
        # Process configuration
        config = config or {}
        output_config = config.get('output', {})
        
        # Determine output path
        if not output_path:
            output_dir = Path(output_config.get('directory', 'output'))
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Use configured filename pattern or default
            filename_pattern = output_config.get('filename_pattern', 
                                              f"{user}_rss_%Y%m%d.epub")
            filename = datetime.now().strftime(filename_pattern)
            output_path = output_dir / filename
        
        # Get metadata from config or use defaults
        title = output_config.get('title', 'Daily RSS Digest')
        author = output_config.get('author', 'RSS to Kobo')
        language = output_config.get('language', 'en')
        
        # Create EPUB
        creator = EPUBCreator(
            user=user,
            title=title,
            author=author,
            language=language
        )
        
        # Add description if available
        if 'description' in output_config:
            creator.book.add_metadata('DC', 'description', output_config['description'])
        
        # Add all feeds and their articles
        for feed_name, articles in feeds_data.items():
            if not articles:
                logger.warning("No articles found for feed: %s", feed_name)
                continue
                
            try:
                creator.add_feed(feed_name, articles)
                logger.debug("Added feed to EPUB: %s (%d articles)", 
                           feed_name, len(articles))
            except Exception as e:
                logger.error("Error adding feed %s to EPUB: %s", feed_name, e)
                continue
        
        # Save the EPUB
        return creator.generate()
        
    except Exception as e:
        error_msg = f"Error building EPUB: {e}"
        logger.error(error_msg, exc_info=True)
        raise ValueError(error_msg) from e
