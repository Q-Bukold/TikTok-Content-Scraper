###
"""
TT_Content_Scraper Package

A comprehensive TikTok content scraping package that allows you to:
- Track scraping progress with SQLite database
- Scrape TikTok user metadata and content metadata
- Download binary files (videos, images, audio)
- Handle errors and retry failed scrapes
- Monitor progress with detailed statistics

Main Components:
- TT_Content_Scraper: Main scraper class
- ObjectTracker: Database for tracking scraping progress
- BaseScraper: Core scraping functionality
"""

# Package metadata
__version__ = "2.0.0"
__author__ = "Quentin Bukold"
__description__ = "TikTok Content Scraper with progress tracking"

# Import main classes to make them available at package level
try:
    from .tt_content_scraper import TT_Content_Scraper
    from .src.object_tracker_db import ObjectTracker, ObjectStatus
    
    # Import logger configuration
    from .src import logger
    
    # Define what gets imported with "from TT_Content_Scraper import *"
    __all__ = [
        "TT_Content_Scraper",
        "ObjectTracker", 
        "ObjectStatus",
        "logger"
    ]
    
except ImportError as e:
    # Handle import errors gracefully during development
    import warnings
    warnings.warn(f"Some imports failed: {e}")
    __all__ = []

# Package-level configuration
DEFAULT_CONFIG = {
    "wait_time": 0.35,
    "output_files_fp": "data/",
    "progress_file_fn": "progress_tracking/scraping_progress.db",
    "clear_console": False,
    "scrape_files": False
}

def create_scraper(**kwargs):
    """
    Convenience function to create a TT_Content_Scraper instance with configuration.
    
    Args:
        **kwargs: Configuration options to override defaults
        
    Returns:
        TT_Content_Scraper: Configured scraper instance
        
    Example:
        >>> scraper = create_scraper(wait_time=0.5, output_files_fp="my_data/")
        >>> scraper.scrape_pending(only_content=True)
    """
    config = DEFAULT_CONFIG.copy()
    config.update(kwargs)
    
    return TT_Content_Scraper(
        wait_time=config["wait_time"],
        output_files_fp=config["output_files_fp"],
        progress_file_fn=config["progress_file_fn"],
        clear_console=config["clear_console"]
    )

def create_tracker(db_file="object_progress.db"):
    """
    Convenience function to create an ObjectTracker instance.
    
    Args:
        db_file (str): Path to SQLite database file
        
    Returns:
        ObjectTracker: Configured tracker instance
        
    Example:
        >>> tracker = create_tracker("my_progress.db")
        >>> tracker.add_objects(["123", "456"], type="content")
    """
    return ObjectTracker(db_file)

def get_version():
    """Return the package version."""
    return __version__

def get_stats_summary(tracker_or_db_file):
    """
    Get a quick statistics summary.
    
    Args:
        tracker_or_db_file: Either ObjectTracker instance or path to db file
        
    Returns:
        dict: Statistics for content and user objects
    """
    if isinstance(tracker_or_db_file, str):
        tracker = ObjectTracker(tracker_or_db_file)
        should_close = True
    else:
        tracker = tracker_or_db_file
        should_close = False
    
    try:
        return {
            "content": tracker.get_stats("content"),
            "user": tracker.get_stats("user"),
            "all": tracker.get_stats("all")
        }
    finally:
        if should_close:
            tracker.close()