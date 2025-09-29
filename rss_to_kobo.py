"""
Main script for RSS to Kobo workflow.

This script combines fetching feeds, building EPUB, and uploading to Dropbox.
"""

import argparse
import logging
import logging.config
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple, Type, TypeVar, cast

# Add the project root to the Python path
project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import logging configuration
from config.logging_config import get_logging_config
from scripts.utils.logging_utils import log_execution_time, setup_logger

# Set up logging
logging.config.dictConfig(get_logging_config(debug=False))
logger = logging.getLogger(__name__)

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments.
    
    Returns:
        Parsed command line arguments
    """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(description="RSS to Kobo workflow")
    # Add arguments with type hints
    parser.add_argument(
        "--user",
        type=str,
        required=True,
        help="Username for feed configuration"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="",
        help="Output EPUB file path (default: auto-generated)"
    )
    parser.add_argument(
        "--no-upload",
        action="store_true",
        help="Skip Dropbox upload"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    parser.add_argument(
        "--target",
        type=str,
        default="Daily-RSS.epub",
        help="Target filename in Dropbox (default: Daily-RSS.epub)",
    )
    return parser.parse_args()

@log_execution_time(logging.getLogger(__name__))
def setup_environment(debug: bool = False) -> bool:
    """Set up the Python environment and check requirements.
    
    Returns:
        bool: True if setup was successful, False otherwise
    """
    try:
        # Add project root to Python path
        project_root = Path(__file__).parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        return True
    except Exception as e:
        logger.error(f"Failed to set up environment: {e}")
        return False

def main() -> int:
    """Run the complete RSS to Kobo workflow.
    
    Returns:
        int: Exit code (0 for success, non-zero for errors)
    """
    args = parse_arguments()
    
    if not setup_environment():
        return 1
    
    # Set up debug logging if requested
    if getattr(args, 'debug', False):
        logging.config.dictConfig(get_logging_config(debug=True))
        logger.debug("Debug logging enabled")

    # Import modules after setting up environment
    logger.debug("Importing required modules...")
    try:
        from scripts.fetch_and_build import FeedFetcher, build_epub
        from scripts.upload_to_dropbox import upload_to_dropbox
        logger.debug("Successfully imported all required modules")
    except ImportError as e:
        logger.critical("Failed to import required modules: %s", e, exc_info=True)
        logger.error("Make sure you're running from the project root directory and all dependencies are installed.")
        return 1
    
    # Step 1: Fetch feeds
    try:
        logger.info("Starting feed fetch for user: %s", args.user)
        logger.debug("Initializing FeedFetcher...")
        fetcher: FeedFetcher = FeedFetcher(args.user)
        
        logger.debug("Fetching all feeds...")
        feeds_data = fetcher.fetch_all()
        
        # Debug: Print the type and first few items of feeds_data
        logger.debug("Type of feeds_data: %s", type(feeds_data))
        if feeds_data:
            logger.debug("Feed names: %s", list(feeds_data.keys()))
            for feed_name, articles in list(feeds_data.items())[:3]:
                logger.debug("Feed '%s' has %d articles", feed_name, len(articles))
                if articles:
                    logger.debug("First article title: %s", articles[0].get('title', 'No title'))
        
        if not feeds_data or not any(articles for articles in feeds_data.values()):
            logger.warning("No feed data was returned from fetch_all()")
            return 1
            
        logger.info("Successfully fetched data from %d feed(s)", len(feeds_data))
                    
    except Exception as e:
        logger.critical("Critical error while fetching feeds: %s", e, exc_info=True)
        return 1
    
    # Step 2: Build EPUB
    try:
        logger.info("Starting EPUB generation from %d feed(s)...", len(feeds_data))
        logger.debug("Calling build_epub with user: %s", args.user)
        
        # The feeds_data is already in the correct format for build_epub
        # It's a dictionary where keys are feed names and values are lists of articles
        epub_path: Optional[str] = build_epub(args.user, feeds_data)
        
        if not epub_path:
            logger.error("build_epub returned None or empty path")
            return 1
            
        epub_path_obj = Path(epub_path)
        if not epub_path_obj.exists():
            logger.error("EPUB file does not exist at path: %s", epub_path)
            return 1
            
        file_size = epub_path_obj.stat().st_size / (1024 * 1024)  # Size in MB
        logger.info("✅ Successfully generated EPUB (%.2f MB): %s", 
                   file_size, epub_path)
        
    except Exception as e:
        logger.critical("Critical error during EPUB generation: %s", e, exc_info=True)
        return 1
    
    # Step 3: Upload to Dropbox (unless disabled)
    if not args.no_upload and epub_path is not None:
        try:
            logger.info("Initiating Dropbox upload for file: %s", epub_path)
            logger.debug("Target path in Dropbox: %s", args.target)
            
            success: bool = upload_to_dropbox(epub_path, args.user, args.target)
            
            if not success:
                logger.error("❌ Upload to Dropbox failed (returned False)")
                return 1
                
            logger.info("✅ Successfully uploaded to Dropbox as '%s'", args.target)
            
        except Exception as e:
            logger.critical("Critical error during Dropbox upload: %s", e, exc_info=True)
            return 1
            
    elif not args.no_upload:
        logger.critical("Cannot proceed with Dropbox upload: No valid EPUB file path available")
        return 1
    else:
        logger.info("ℹ️  Dropbox upload skipped as requested (--no-upload flag was set)")
        logger.debug("EPUB file remains at: %s", epub_path)
    
    logger.info("✅ RSS to Kobo workflow completed successfully")
    logger.debug("Exiting with status code 0")
    return 0

if __name__ == "__main__":
    sys.exit(main())
