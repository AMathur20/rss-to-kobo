"""
RSS to Kobo scripts package.
"""

__version__ = "0.1.0"

# Import main components for easier access
from .epub_builder import EPUBCreator, build_epub
from .fetch_and_build import FeedFetcher, main as fetch_and_build
from .upload_to_dropbox import main as upload_main, upload_to_dropbox
from .utils import (
    clean_html,
    format_date,
    get_output_path,
    load_feeds_config,
    setup_logger,
)

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
