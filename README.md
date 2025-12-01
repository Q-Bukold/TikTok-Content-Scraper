# What is it?

This scraper allows you to download TikTok **user profiles**, **videos** and **slides** without an official API key. Additionally, it can scrape approximately 100 metadata fields related to the video, author, music, video file, and hashtags. It can also download the mp4 of videos and pictures as well as music of all slides. 

You do not need your own progress tracking, the scraper takes care of everything - even common errors. It was built to scrape 1M+ IDs, but can also be used for smaller datasets. The scraped metadata is downloaded, but modifying the scraper can also allow you to connect it to a database.

#### Features
- Scrape extensive metadata on users and content (90+ elements)
- Download TikTok videos (mp4) and slides (jpegs + mp3)
- Easy data management: SQLite database tracks scraping progress, errors, and completion status of all ID's
- Use via command line: Easy-to-use command-line interface with multiple commands

#### Disclaimer
This tool was built for research purposes in the EU. Please respect the applicable regulations. If this work is used for your academic work, it must be cited according to the information given in this repository or the [Weizenbaum Institute](https://www.weizenbaum-library.de/handle/id/814) library. Not citing open-source software can be considered plagiarism.

> Bukold, Q. (2025). TikTok-Content-Scraper (Version X.X) [Computer software]. https://www.weizenbaum-library.de/handle/id/814

# Installation

Clone this repository and install dependencies with bash:
1. Download the repository -> ```git clone https://github.com/Q-Bukold/TikTok-Content-Scraper.git```
2. Switch to the downloaded folder -> ```cd TikTok_Content_Scraper```
3. Install all packages in requirements.txt -> ```pip install -r requirements.txt```
4. Run the example script -> ```python3 example_script.py```

# Using the scraper via Python script
**Run the [example script](https://github.com/Q-Bukold/TikTok-Content-Scraper/blob/main/example_script.py) to check out all basic functions**. The scraper works in two steps; a) fill a progress database with your IDs and b) start the scraping progress and let the database manage your progress. 

## Configuring the scraper (this step is always needed)
1. Import the scraper in your Python file
2. Initialize the scraper with the paths and settings you want. The folders are created automatically.
3. Every time you use the "scraper" object, it is now using these settings
```python
from TT_Content_Scraper import TT_Content_Scraper

scraper = TT_Content_Scraper(
    wait_time=0.35,
    output_files_fp="data/",
    progress_file_fn="progress_tracking/scraping_progress.db",
    clear_console=False # only works with mac and linux systems
)
```
We have now created the necessary output folders and initialized a database that tracks which IDs still need to be scraped or caused errors. The database is stored in the progress_file. If you delete this file, the database is also deleted. The wait time defines the seconds that the scraper waits between requests. Increase this time in case you get blocked by TikTok. The clear_console command gives you a nicer terminal output, but does not work on windows!

## Adding ids of videos or slides you want to scrape
Now, we will fill our progress database with the videos and user IDs that we want to scrape. We only have to do this once! To reset the database delete the progress_file or execute the command ```scraper.clear_all_data()```. More commands to reset all IDs to pending, get the database statistics or reset the IDs marked as errors can be found in the [object tracker](https://github.com/Q-Bukold/TikTok-Content-Scraper/blob/main/TT_Content_Scraper/src/object_tracker_db.py) file.

To scrape the metadata and content of a video, the TikTok ID is required. It can be found in the URL of a video. To scrape the metadata of a user, the TikTok username is required (with or without an @). It can be found in the URL of a user profile.

```python
# caution! do not forget to set the "type" arg to "content"
# the "title" is optional
scraper.add_objects(ids=["7398323154424171806", "7447600730267061526"], title="from seedlist aug 20", type="content")
```

Add usernames:
```python
# caution! do not forget to set the "type" arg to "user"
scraper.add_objects(ids=["tagesschau", "bundeskanzler"], title="from seedlist aug 20", type="user")
```

## Start scraping all objects you added that have not been scraped (pending objects)
All IDs you have previously added are now permanently stored in the progress database as pending, even if you restart your server. To start the scraping process, execute the code below. The database will track the IDs that a) caused an **error**, b) are **completed** and c) are still **pending**. 

The ```scrape_pending``` function has multiple arguments. Use ```only_content=True``` to only scrape IDs marked as content and ```only_users=True``` to only scrape IDs marked as belonging to a user. If both arguments are false, both types are scraped. By default, the scraper only scrapes the metadata, turn on ```scrape_files = True``` to also scrape the mp3/mp4/jpegs or the slides and videos.

```python
from TT_Content_Scraper import TT_Content_Scraper

scraper = TT_Content_Scraper(
    wait_time=0.35,
    output_files_fp="data/",
    progress_file_fn="progress_tracking/scraping_progress.db",
    clear_console=False # only works with mac and linux systems
)

scraper.scrape_pending(scrape_files=True) # scrape_files indicates, if you want to scrape the mp3/mp4/jpeg of all content
```

## Output of the scraper
**The scrape_pending function provides a useful overview of your progress:**
> Enable clear_console to clear the terminal output after every scrape. Note that clear_console does not work on Windows machines.
``` text
09-15/13:51;INFO :TTCS.DB   : Scraping ID: 7431135705826364704
09-15/13:51;INFO :TTCS      : Scraped objects ► 309,376 / 2,979,827
09-15/13:51;INFO :TTCS      : ...minus errors ► 259,564
09-15/13:51;INFO :TTCS      : Iteration time ► 2.72 sec.
09-15/13:51;INFO :TTCS      : ......averaged ► 2.52 sec.
09-15/13:51;INFO :TTCS      : ETA ► 70 days 7:45:11
---
09-15/13:51;INFO :TTCS      : is slide with 17 pictures
09-15/13:51;INFO :TTCS.DB   : ▼ JPEG saved to data/content_files/tiktok_picture_7431135705826364704_1.jpeg
...
```

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

### Database Schema
The tracker maintains detailed information about each object:
- Unique ID and type (content/user)
- Current status and timestamps
- Error messages and attempt counts
- File paths for completed objects

## Best Practices

1. **Respect Rate Limits**: Use appropriate wait times to avoid being blocked and avoid overloading TikTok's servers.
2. **Backup Progress**: Regularly back up your progress database
3. **Check Disk Space**: Monitor available disk space when downloading files

---
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
