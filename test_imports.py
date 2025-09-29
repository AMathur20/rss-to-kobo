#!/usr/bin/env python3
"""
Test script to verify imports and basic functionality.
"""
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_imports():
    """Test importing all required modules."""
    print("Testing imports...")
    
    # Test importing from config
    try:
        from config.logging_config import get_logging_config
        print("✅ Successfully imported from config.logging_config")
    except ImportError as e:
        print(f"❌ Failed to import from config.logging_config: {e}")
        return False
    
    # Test importing from scripts.utils
    try:
        from scripts.utils.logging_utils import setup_logger, log_execution_time
        from scripts.utils.general import load_feeds_config, get_output_path, clean_html, format_date
        print("✅ Successfully imported from scripts.utils")
    except ImportError as e:
        print(f"❌ Failed to import from scripts.utils: {e}")
        return False
    
    # Test importing main modules
    try:
        from scripts.epub_builder import EPUBCreator, build_epub
        from scripts.fetch_and_build import FeedFetcher, main as fetch_and_build
        from scripts.upload_to_dropbox import upload_to_dropbox, main as upload_main
        print("✅ Successfully imported main modules")
    except ImportError as e:
        print(f"❌ Failed to import main modules: {e}")
        return False
    
    return True

def test_config_loading():
    """Test loading the configuration file."""
    print("\nTesting configuration loading...")
    
    try:
        from scripts.utils.general import load_feeds_config
        
        # Test loading the test user config
        config = load_feeds_config("test_user")
        print("✅ Successfully loaded test_user.yaml")
        
        # Print some config details
        print(f"Found {len(config.get('feeds', []))} feeds")
        print(f"Output directory: {config.get('output', {}).get('directory', 'Not specified')}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return False

if __name__ == "__main__":
    print("=== RSS to Kobo - Import Test ===\n")
    
    # Run import tests
    if not test_imports():
        print("\n❌ Some imports failed. Please check the error messages above.")
        sys.exit(1)
    
    # Run config loading test
    if not test_config_loading():
        print("\n❌ Configuration loading failed. Please check the error messages above.")
        sys.exit(1)
    
    print("\n✅ All tests passed!")
    print("\nYou can now try running the main script with:")
    print("python rss_to_kobo.py --user test_user")
