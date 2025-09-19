"""
Main script for RSS to Kobo workflow.

This script combines fetching feeds, building EPUB, and uploading to Dropbox.
"""

import argparse
import logging
import sys
from importlib import import_module
from pathlib import Path

def main() -> int:
    """Run the complete RSS to Kobo workflow.
    
    Returns:
        int: Exit code (0 for success, non-zero for errors)
    """
    parser = argparse.ArgumentParser(description="RSS to Kobo workflow")
    parser.add_argument("--user", required=True, help="Username for feed configuration")
    parser.add_argument("--output", help="Output EPUB file path (default: auto-generated)")
    parser.add_argument("--no-upload", action="store_true", help="Skip Dropbox upload")
    parser.add_argument(
        "--target", 
        default="Daily-RSS.epub",
        help="Target filename in Dropbox (default: Daily-RSS.epub)",
    )
    
    args = parser.parse_args()
    
    # Import modules here to avoid circular imports
    try:
        from scripts.fetch_and_build import FeedFetcher, build_epub
        from scripts.upload_to_dropbox import upload_to_dropbox
    except ImportError as e:
        print(f"Error importing modules: {e}", file=sys.stderr)
        print("Make sure you're running from the project root directory.", file=sys.stderr)
        return 1
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)
    
    # Step 1: Fetch feeds
    logger.info("Fetching feeds for user: %s", args.user)
    fetcher = FeedFetcher(args.user)
    feeds_data = fetcher.fetch_all()
    
    if not feeds_data:
        logger.error("No feed data available to generate EPUB")
        return 1
    
    # Step 2: Build EPUB
    try:
        logger.info("Generating EPUB...")
        epub_path = build_epub(args.user, feeds_data)
        logger.info("Successfully generated EPUB: %s", epub_path)
    except Exception as e:
        logger.error("Error generating EPUB: %s", e, exc_info=True)
        return 1
    
    # Step 3: Upload to Dropbox (unless disabled)
    if not args.no_upload:
        logger.info("Uploading to Dropbox...")
        success = upload_to_dropbox(epub_path, args.user, args.target)
        if not success:
            logger.error("Failed to upload to Dropbox")
            return 1
        logger.info("Successfully uploaded to Dropbox")
    else:
        logger.info("Skipping Dropbox upload as requested")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
