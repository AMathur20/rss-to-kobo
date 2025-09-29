"""
Dropbox upload module for RSS to Kobo.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional, Union

import dropbox
from dropbox import Dropbox
from dropbox.exceptions import ApiError, AuthError, BadInputError, HttpError
from dropbox.files import WriteMode, UploadSessionCursor, CommitInfo

from .auth.oauth_handler import OAuthHandler
from .utils import get_output_path
from .utils.logging_utils import setup_logger

logger = setup_logger(__name__)
CHUNK_SIZE = 4 * 1024 * 1024  # 4MB chunks for large file uploads


def get_dropbox_client(username: str) -> Optional[Dropbox]:
    """Get an authenticated Dropbox client for the specified user.

    Args:
        username: The username to get a client for

    Returns:
        An authenticated Dropbox client or None if authentication fails
    """
    try:
        handler = OAuthHandler(username)
        return handler.get_authenticated_client()
    except Exception as e:
        logger.error(f"Failed to authenticate user '{username}': {e}")
        return None


def upload_to_dropbox(
    local_path: Union[str, Path], username: str, target_filename: str = "Daily-RSS.epub"
) -> bool:
    """Upload a file to Dropbox in the 'Apps/Rakuten Kobo' folder.

    Args:
        local_path: Path to local file to upload
        username: Username for authentication
        target_filename: Filename to use in Dropbox (default: "Daily-RSS.epub")

    Returns:
        bool: True if upload was successful, False otherwise
    """
    # Always use the Kobo-specific folder
    target_path = f"/Apps/Rakuten Kobo/{target_filename}"
    local_path = Path(local_path)
    if not local_path.exists():
        logger.error("Local file not found: %s", local_path)
        return False

    dbx = None
    try:
        # Get authenticated client
        dbx = get_dropbox_client(username)
        if not dbx:
            logger.error("Failed to authenticate with Dropbox for user: %s", username)
            return False

        # Get file size for progress tracking
        file_size = local_path.stat().st_size
        logger.info("Uploading %s (%.1f MB) to Dropbox as '%s'...", 
                   local_path.name, file_size / (1024 * 1024), target_filename)

        # Use chunked upload for large files
        if file_size <= CHUNK_SIZE:
            with open(local_path, "rb") as f:
                dbx.files_upload(
                    f.read(), 
                    target_path,
                    mode=WriteMode('overwrite')
                )
        else:
            with open(local_path, "rb") as f:
                # Start the upload session
                upload_session_start_result = dbx.files_upload_session_start(
                    f.read(CHUNK_SIZE))
                cursor = UploadSessionCursor(
                    session_id=upload_session_start_result.session_id,
                    offset=f.tell()
                )
                commit = CommitInfo(
                    path=target_path,
                    mode=WriteMode('overwrite')
                )

                # Upload in chunks
                while f.tell() < file_size:
                    remaining = file_size - f.tell()
                    chunk_size = min(CHUNK_SIZE, remaining)
                    chunk = f.read(chunk_size)
                    
                    if remaining <= CHUNK_SIZE:
                        dbx.files_upload_session_finish(chunk, cursor, commit)
                    else:
                        dbx.files_upload_session_append_v2(chunk, cursor)
                        cursor.offset = f.tell()
                        
                    # Log progress
                    progress = (f.tell() / file_size) * 100
                    logger.debug("Uploaded %d/%d bytes (%.1f%%)",
                               f.tell(), file_size, progress)

        logger.info("✅ Successfully uploaded '%s' to Dropbox", target_filename)
        return True

    except AuthError as e:
        logger.error("❌ Authentication failed for user '%s'", username)
        logger.debug("AuthError details: %s", str(e))
    except ApiError as e:
        logger.error("❌ Dropbox API error: %s", e.error)
    except (BadInputError, HttpError) as e:
        logger.error("❌ Dropbox request failed: %s", str(e))
    except Exception as e:
        logger.error("❌ Unexpected error during upload: %s", str(e), exc_info=True)
    finally:
        if dbx:
            try:
                dbx.close()
            except Exception:
                pass  # Ignore errors during client cleanup

    return False


def main() -> int:
    """Handle command-line interface for Dropbox upload.

    Returns:
        int: Exit code (0 for success, non-zero for errors)
    """
    parser = argparse.ArgumentParser(
        description="Upload files to Dropbox for RSS to Kobo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python -m scripts.upload_to_dropbox file.epub -u username
  python -m scripts.upload_to_dropbox file.epub -u username -o CustomName.epub
"""
    )
    
    parser.add_argument(
        "file", 
        help="Path to the file to upload"
    )
    parser.add_argument(
        "-u", "--user", 
        required=True, 
        help="Username for authentication"
    )
    parser.add_argument(
        "-o", "--output", 
        default="Daily-RSS.epub", 
        help="Output filename in Dropbox (default: Daily-RSS.epub)"
    )
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true", 
        help="Enable verbose logging for debugging"
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('upload.log')
        ],
    )

    logger.info("Starting Dropbox upload for user: %s", args.user)
    logger.debug("Source: %s, destination: %s", args.file, args.output)

    # Upload the file
    success = upload_to_dropbox(args.file, args.user, args.output)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
