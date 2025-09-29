"""
RSS to Kobo scripts package.
"""

__version__ = "2.0.0"

# Import main components for easier access
from .epub_builder import EPUBCreator, build_epub
from .fetch_and_build import FeedFetcher, main as fetch_and_build
from .upload_to_dropbox import upload_to_dropbox, main as upload_main
from .utils.logging_utils import setup_logger
from .utils.general import load_feeds_config, get_output_path, clean_html, format_date

# Import these conditionally to avoid circular imports
__all__ = [
    "FeedFetcher",
    "fetch_and_build",
    "build_epub",
    "EPUBCreator",
    "upload_to_dropbox",
    "upload_main",
    "setup_logger",
    "load_feeds_config",
    "get_output_path",
    "clean_html",
    "format_date",
]
