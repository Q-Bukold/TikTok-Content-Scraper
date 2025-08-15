#!/usr/bin/env python3
"""
TikTok Content Scraper CLI

Command-line interface for the TT_Content_Scraper package.
"""
import argparse
import sys
import os
from pathlib import Path
from typing import Optional, List

from .tt_content_scraper import TT_Content_Scraper
from .src.object_tracker_db import ObjectTracker, ObjectStatus


def setup_parser() -> argparse.ArgumentParser:
    """Set up the argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        description="TikTok Content Scraper - CLI interface for scraping TikTok content and user data",
        prog="tt-scraper"
    )
    
    # Global arguments
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="data/",
        help="Output directory for scraped data (default: data/)"
    )
    parser.add_argument(
        "--progress-db",
        default="progress_tracking/scraping_progress.db",
        help="Progress database file path (default: progress_tracking/scraping_progress.db)"
    )
    parser.add_argument(
        "--wait-time", "-w",
        type=float,
        default=0.35,
        help="Wait time between requests in seconds (default: 0.35)"
    )
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands",
        required=True
    )
    
    # Add IDs from file command
    add_parser = subparsers.add_parser(
        "add",
        help="Add IDs to the object tracker from a text file"
    )
    add_parser.add_argument(
        "file",
        help="Text file containing IDs (one per line)"
    )
    add_parser.add_argument(
        "--type",
        choices=["content", "user"],
        required=True,
        help="Type of objects to add (content or user)"
    )
    add_parser.add_argument(
        "--title",
        help="Optional title for all added objects"
    )
    
    # Scrape command
    scrape_parser = subparsers.add_parser(
        "scrape",
        help="Start scraping pending objects"
    )
    scrape_parser.add_argument(
        "--type",
        choices=["content", "user", "all"],
        default="all",
        help="Type of objects to scrape (default: all)"
    )
    scrape_parser.add_argument(
        "--scrape-files",
        action="store_true",
        help="Download binary files (videos, images, audio) for content"
    )
    scrape_parser.add_argument(
        "--clear-console",
        action="store_true",
        help="Clear console between iterations"
    )
    
    # Statistics command
    stats_parser = subparsers.add_parser(
        "stats",
        help="Display scraping statistics"
    )
    stats_parser.add_argument(
        "--type",
        choices=["content", "user", "all"],
        default="all",
        help="Type of objects to show stats for (default: all)"
    )
    stats_parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed statistics including error objects"
    )
    
    # Status command
    status_parser = subparsers.add_parser(
        "status",
        help="Check status of specific object(s)"
    )
    status_parser.add_argument(
        "ids",
        nargs="+",
        help="Object IDs to check status for"
    )
    
    # Reset errors command
    reset_parser = subparsers.add_parser(
        "reset-errors",
        help="Reset all error objects back to pending for retry"
    )

    # Reset all objects command
    reset_all_parser = subparsers.add_parser(
        "reset-all",
        help="Reset all error objects back to pending for retry"
    )
    
    # Clear data command
    clear_parser = subparsers.add_parser(
        "clear",
        help="Clear all tracking data (use with caution!)"
    )
    clear_parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm you want to clear all data"
    )
    
    return parser


def load_ids_from_file(filepath: str) -> List[str]:
    """Load IDs from a text file, one per line."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            ids = [line.strip() for line in f if line.strip()]
        return ids
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file '{filepath}': {e}", file=sys.stderr)
        sys.exit(1)


def print_stats(tracker: ObjectTracker, obj_type: str = "all", detailed: bool = False):
    """Print statistics for the object tracker."""
    stats = tracker.get_stats(type=obj_type)
    
    print(f"\n=== Statistics ({obj_type}) ===")
    print(f"Completed: {stats['completed']:,}")
    print(f"Pending:   {stats['pending']:,}")
    print(f"Errors:    {stats['errors']:,}")
    print(f"Retry:     {stats['retry']:,}")
    
    total = sum(stats.values())
    print(f"Total:     {total:,}")
    
    if total > 0:
        print(f"\nProgress: {stats['completed']/total*100:.1f}% complete")
        if stats['errors'] > 0:
            print(f"Error rate: {stats['errors']/total*100:.1f}%")
    
    if detailed and stats['errors'] > 0:
        print(f"\n=== Error Details ===")
        error_objects = tracker.get_error_objects()
        for obj_id, obj_data in list(error_objects.items())[:10]:  # Show first 10 errors
            print(f"ID {obj_id}: {obj_data['last_error']} (attempts: {obj_data['attempts']})")
        if len(error_objects) > 10:
            print(f"... and {len(error_objects) - 10} more errors")


def main():
    """Main entry point."""
    parser = setup_parser()
    args = parser.parse_args()
    
    try:
        if args.command == "add":
            # Load IDs from file and add to tracker
            ids = load_ids_from_file(args.file)
            
            if not ids:
                print("No IDs found in file.", file=sys.stderr)
                sys.exit(1)
            
            print(f"Loading {len(ids)} IDs from {args.file}")
            
            tracker = ObjectTracker(args.progress_db)
            tracker.add_objects(ids, title=args.title, type=args.type)
            
            print(f"Added {len(ids)} {args.type} objects to tracker")
            print_stats(tracker, args.type)
            tracker.close()
            
        elif args.command == "scrape":
            # Start scraping
            print("Initializing scraper...")
            
            scraper = TT_Content_Scraper(
                wait_time=args.wait_time,
                output_files_fp=args.output_dir,
                progress_file_fn=args.progress_db,
                clear_console=args.clear_console
            )
            
            try:
                if args.type == "content":
                    scraper.scrape_pending(
                        only_content=True,
                        scrape_files=args.scrape_files
                    )
                elif args.type == "user":
                    scraper.scrape_pending(only_users=True)
                else:
                    scraper.scrape_pending(
                        scrape_files=args.scrape_files
                    )
            except KeyboardInterrupt:
                print("\nScraping interrupted by user.")
            except AssertionError as e:
                print(f"Scraping completed: {e}")
            #except Exception as e:
            #    print(f"Error during scraping: {e}", file=sys.stderr)
            #    sys.exit(1)
            
        elif args.command == "stats":
            # Show statistics
            tracker = ObjectTracker(args.progress_db)
            print_stats(tracker, args.type, args.detailed)
            tracker.close()
            
        elif args.command == "status":
            # Check status of specific objects
            tracker = ObjectTracker(args.progress_db)
            
            print(f"\n=== Object Status ===")
            for obj_id in args.ids:
                status = tracker.get_object_status(obj_id)
                if status:
                    print(f"ID {obj_id}:")
                    print(f"  Status: {status['status']}")
                    print(f"  Type: {status['type']}")
                    print(f"  Added: {status['added_at']}")
                    if status['completed_at']:
                        print(f"  Completed: {status['completed_at']}")
                    if status['last_error']:
                        print(f"  Last Error: {status['last_error']}")
                        print(f"  Attempts: {status['attempts']}")
                    if status['file_path']:
                        print(f"  File: {status['file_path']}")
                    print()
                else:
                    print(f"ID {obj_id}: Not found in tracker")
            
            tracker.close()
            
        elif args.command == "reset-errors":
            # Reset error objects to pending
            tracker = ObjectTracker(args.progress_db)
            count = tracker.reset_errors_to_pending()
            print(f"Reset {count} error objects back to pending")
            print_stats(tracker)
            tracker.close()
        
        elif args.command == "reset-all":
            # Reset error objects to pending
            tracker = ObjectTracker(args.progress_db)
            count = tracker.reset_all_to_pending()
            print(f"Reset {count} error, retry and completed objects back to pending")
            print_stats(tracker)
            tracker.close()
            
        elif args.command == "clear":
            # Clear all data
            if not args.confirm:
                print("This will delete ALL tracking data!")
                response = input("Are you sure? Type 'yes' to confirm: ")
                if response.lower() != 'yes':
                    print("Operation cancelled.")
                    sys.exit(0)
            
            tracker = ObjectTracker(args.progress_db)
            tracker.clear_all_data()
            print("All tracking data cleared.")
            tracker.close()
    
    except KeyboardInterrupt:
        print("\nOperation interrupted by user.")
        sys.exit(0)
    #except Exception as e:
    #    if args.verbose:
    #        import traceback
    #        traceback.print_exc()
    #    else:
    #        print(f"Error: {e}", file=sys.stderr)
    #    sys.exit(1)


if __name__ == "__main__":
    main()