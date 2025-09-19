"""
Dropbox upload module for RSS to Kobo.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Optional, Union

import dropbox
from dropbox.exceptions import ApiError, AuthError

from .utils import get_output_path, setup_logger

logger = setup_logger(__name__)
CHUNK_SIZE = 4 * 1024 * 1024  # 4MB chunks for large file uploads


def load_dropbox_token(user: str) -> str:
    """Load Dropbox token for a user.

    Args:
        user: Username

    Returns:
        Dropbox access token

    Raises:
        FileNotFoundError: If token file doesn't exist
        ValueError: If token is invalid or malformed
    """
    token_path = Path(__file__).parent.parent / "dropbox_tokens" / f"{user}_token.json"

    try:
        with open(token_path, "r", encoding="utf-8") as f:
            token_data = json.load(f)

        if not isinstance(token_data, dict) or "access_token" not in token_data:
            raise ValueError("Invalid token format: missing 'access_token'")

        return str(token_data["access_token"])

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in token file {token_path}: {e}") from e
    except FileNotFoundError as e:
        logger.error("Dropbox token not found for user: %s", user)
        logger.info("Expected token file at: %s", token_path)
        raise


def upload_to_dropbox(
    local_path: Union[str, Path], user: str, target_filename: str = "Daily-RSS.epub"
) -> bool:
    """Upload a file to Dropbox.

    Args:
        local_path: Path to local file to upload
        user: Username for token lookup
        target_filename: Filename to use in Dropbox

    Returns:
        True if upload was successful, False otherwise
    """
    path = Path(local_path)
    if not path.exists():
        logger.error("Local file not found: %s", path)
        return False

    try:
        # Load Dropbox token
        token = load_dropbox_token(user)

        # Initialize Dropbox client
        dbx = dropbox.Dropbox(token)

        # Verify token is valid
        try:
            dbx.users_get_current_account()
        except AuthError as e:
            logger.error("Invalid Dropbox token for user %s: %s", user, e)
            return False

        # Define target path in Dropbox
        target_path = f"/Apps/Rakuten Kobo/{target_filename}"

        # Upload the file
        with path.open("rb") as file_obj:
            file_size = path.stat().st_size

            if file_size <= CHUNK_SIZE:
                # Small file upload (<= 4MB)
                dbx.files_upload(
                    file_obj.read(),
                    target_path,
                    mode=dropbox.files.WriteMode.overwrite,
                    mute=True,
                )
            else:
                # Large file upload with progress
                upload_session_start_result = dbx.files_upload_session_start(
                    file_obj.read(CHUNK_SIZE)
                )
                cursor = dropbox.files.UploadSessionCursor(
                    session_id=upload_session_start_result.session_id,
                    offset=file_obj.tell(),
                )
                commit = dropbox.files.CommitInfo(
                    path=target_path,
                    mode=dropbox.files.WriteMode.overwrite,
                )

                while file_obj.tell() < file_size:
                    remaining = file_size - file_obj.tell()
                    chunk_size = min(CHUNK_SIZE, remaining)
                    chunk = file_obj.read(chunk_size)

                    if remaining <= CHUNK_SIZE:
                        dbx.files_upload_session_finish(chunk, cursor, commit)
                    else:
                        dbx.files_upload_session_append_v2(chunk, cursor)
                        cursor.offset = file_obj.tell()

        logger.info("Successfully uploaded %s to Dropbox as %s", path, target_path)
        return True

    except (dropbox.exceptions.DropboxException, OSError) as e:
        logger.error("Error uploading to Dropbox: %s", e, exc_info=True)
        return False


def main() -> int:
    """Handle command-line interface for Dropbox upload.

    Returns:
        int: Exit code (0 for success, non-zero for errors)
    """
    parser = argparse.ArgumentParser(description="Upload EPUB to Dropbox for Kobo")
    parser.add_argument("--user", required=True, help="Username for token lookup")
    parser.add_argument(
        "--file", help="Path to EPUB file (default: auto-detect latest for user)"
    )
    parser.add_argument(
        "--target",
        default="Daily-RSS.epub",
        help="Target filename in Dropbox (default: Daily-RSS.epub)",
    )

    args = parser.parse_args()

    # Determine file to upload
    if args.file:
        local_path = Path(args.file)
    else:
        # Find the most recent EPUB for this user
        output_dir = Path(__file__).parent.parent / "output"
        epubs = list(output_dir.glob(f"{args.user}_Daily-RSS_*.epub"))

        if not epubs:
            logger.error("No EPUB files found for user %s", args.user)
            return 1

        # Sort by modification time, newest first
        epubs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        local_path = epubs[0]

    # Upload the file
    success = upload_to_dropbox(local_path, args.user, args.target)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
