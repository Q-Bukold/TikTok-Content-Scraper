# What is it?

**This scraper allows you to download both TikTok videos and slides without an official API key. Additionally, it can scrape approximately 100 metadata fields related to the video, author, music, video file, and hashtags. The scraper is built as a Python class and can be inherited by a custom parent class, allowing for easy integration with databases or other systems.**

## Features

- Download TikTok videos (mp4) and slides (jpeg's + mp3).
- Scrape extensive metadata.
- Customizable and extendable via inheritance.
- Supports batch processing and progress tracking.
- **Progress Tracking**: SQLite database tracks scraping progress, errors, and completion status
- **CLI Interface**: Easy-to-use command-line interface with multiple commands
- **Statistics**: Detailed progress statistics and reporting
- **Rate Limiting**: Configurable wait times to respect API limits

## Installation

Clone this repository and install dependencies:

```bash
git clone <repository-url>
cd TT_Content_Scraper
pip install -r requirements.txt
```

# Using the scraper via the command line

## Quick Start

### 1. Prepare your ID lists

Create text files with TikTok IDs (one per line):

**content_ids.txt:**
```
7123456789012345678
7234567890123456789
7345678901234567890
```

**user_ids.txt:**
```
user123
user456
user789
```

### 2. Add IDs to the tracker

```bash
# Add content IDs
python -m TT_Content_Scraper add content_ids.txt --type content

# Add user IDs
python -m TT_Content_Scraper add user_ids.txt --type user
```

### 3. Start scraping

```bash
# Scrape all pending objects
python -m TT_Content_Scraper scrape

# Or scrape specific types
python -m TT_Content_Scraper scrape --type content --scrape-files
```

### 4. Monitor progress

```bash
# View statistics
python -m TT_Content_Scraper stats

# View detailed stats for content objects
python -m TT_Content_Scraper stats --type content --detailed
```

## CLI Commands

### `add` - Add IDs from file

Add TikTok IDs to the tracking database from a text file.

```bash
python -m TT_Content_Scraper add <file> --type <content|user> [options]
```

**Arguments:**
- `file`: Text file containing IDs (one per line)
- `--type`: Object type (`content` or `user`)
- `--title`: Optional title for all added objects

**Examples:**
```bash
python -m TT_Content_Scraper add my_ids.txt --type content
python -m TT_Content_Scraper add users.txt --type user --title "Batch 1"
```

### `scrape` - Start scraping

Begin scraping pending objects from the database.

```bash
python -m TT_Content_Scraper scrape [options]
```

**Options:**
- `--type <content|user|all>`: Type of objects to scrape (default: all)
- `--scrape-files`: Download binary files (videos, images, audio)
- `--clear-console`: Clear console between iterations

**Examples:**
```bash
# Scrape everything
python -m TT_Content_Scraper scrape

# Scrape only content with file downloads
python -m TT_Content_Scraper scrape --type content --scrape-files

# Scrape users only
python -m TT_Content_Scraper scrape --type user
```

### `stats` - View statistics

Display scraping progress and statistics.

```bash
python -m TT_Content_Scraper stats [options]
```

**Options:**
- `--type <content|user|all>`: Object type to show stats for (default: all)
- `--detailed`: Show detailed statistics including error information

**Examples:**
```bash
python -m TT_Content_Scraper stats
python -m TT_Content_Scraper stats --type content --detailed
```

### `status` - Check object status

Check the status of specific objects by their IDs.

```bash
python -m TT_Content_Scraper status <id1> <id2> [...]
```

**Example:**
```bash
python -m TT_Content_Scraper status 7123456789012345678 user123
```

### `reset-errors` - Reset failed objects

Reset all objects with error status back to pending for retry.

```bash
python -m TT_Content_Scraper reset-errors
```

### `clear` - Clear all data

Clear all tracking data from the database (use with caution).

```bash
python -m TT_Content_Scraper clear --confirm
```

## Global Options

These options can be used with any command:

- `--output-dir <path>`: Output directory for scraped data (default: `data/`)
- `--progress-db <path>`: Progress database file path (default: `progress_tracking/scraping_progress.db`)
- `--wait-time <seconds>`: Wait time between requests (default: 0.35)
- `--verbose, -v`: Enable verbose output

**Example:**
```bash
python -m TT_Content_Scraper --output-dir "my_data/" --wait-time 0.5 scrape --type content
```

## Output Structure

The scraper organizes output files as follows:

```
data/
├── content_metadata/
│   ├── 7123456789012345678.json
│   ├── 7234567890123456789.json
│   └── ...
├── user_metadata/
│   ├── max.json
│   ├── john.json
│   └── ...
└── content_files/
    ├── tiktok_7123456789012345678_video.mp4
    ├── tiktok_7234567890123456789_slide0.jpeg
    ├── tiktok_7234567890123456789_slide1.jpeg
    ├── tiktok_7234567890123456789_audio.mp3
    └── ...
```

## Progress Tracking

The scraper uses an SQLite database to track progress:

### Object Status Types
- **Pending**: Objects waiting to be scraped
- **Completed**: Successfully scraped objects
- **Error**: Objects that failed during scraping
- **Retry**: Error objects reset for retry

### Database Schema
The tracker maintains detailed information about each object:
- Unique ID and type (content/user)
- Current status and timestamps
- Error messages and attempt counts
- File paths for completed objects

## Programming Interface

You can also use the scraper programmatically:

```python
from TT_Content_Scraper import TT_Content_Scraper, ObjectTracker

# Create scraper instance
scraper = TT_Content_Scraper(
    wait_time=0.35,
    output_files_fp="data/",
    progress_file_fn="progress.db"
)

# Add objects to track
tracker = ObjectTracker("progress.db")
tracker.add_objects(["123", "456"], type="content")

# Start scraping
scraper.scrape_pending(only_content=True, scrape_files=True)

# Get statistics
stats = tracker.get_stats("content")
print(f"Completed: {stats['completed']}")
```

## Configuration

### Default Settings
- **Wait Time**: 0.35 seconds between requests
- **Output Directory**: `data/`
- **Progress Database**: `progress_tracking/scraping_progress.db`
- **Console Clearing**: Disabled by default

### Customizing Settings
All settings can be customized via command-line options or when creating scraper instances programmatically.

## Logging

The scraper uses Python's logging module with different levels:
- **INFO**: General progress information
- **DEBUG**: Detailed operation information
- **WARNING**: Non-fatal issues
- **ERROR**: Error conditions

## Best Practices

1. **Respect Rate Limits**: Use appropriate wait times to avoid being blocked
2. **Backup Progress**: Regularly backup your progress database
3. **Check Disk Space**: Monitor available disk space when downloading files

## Disclaimer

This tool is for educational and research purposes in the EU only. Please respect the applicable regulations. Be responsible with scraping and avoid overloading TikTok's servers.
```
