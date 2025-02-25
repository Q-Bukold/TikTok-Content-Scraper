# What is it?

**This scraper allows you to download both TikTok videos and slides without an official API key. Additionally, it can scrape approximately 100 metadata fields related to the video, author, music, video file, and hashtags. The scraper is built as a Python class and can be inherited by a custom parent class, allowing for easy integration with databases or other systems.**

## Features

- Download TikTok videos (mp4) and slides (jpeg's + mp3).
- Scrape extensive metadata.
- Customizable and extendable via inheritance.
- Supports batch processing and progress tracking.

## Usage

### Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Q-Bukold/TikTok-Content-Scraper.git
   cd TikTok-Content-Scraper
   ```

2. **Install All Dependencies in the Requirements File**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Example Script**:
   ```bash
   python example_script.py
   ```

## Scrape a single video or slide
To scrape the metadata and content of a video, the TikTok ID is required. It can be found in the URL of a video. Let's use the ID `7460303767968156958` to scrape the associated video. In the folder `examples/` you can see what a potential output could look like.

```python
from TT_Scraper import TT_Scraper

# Configure the scraper, this step is always needed
tt = TT_Scraper(wait_time=0.3, output_files_fp="data/")

# Download all metadata as a .json and all content as .mp4/.jpeg
tt.scrape(id = 7460303767968156958, scrape_content = True, download_metadata = True, download_content = True)

```

## Scrape multiple videos and slides
You can also scrape a list of IDs with the following code. The scraper detects on it's own, if the content is a Slide or Video.

```python
import pandas as pd
from TT_Scraper import TT_Scraper

# Configure the scraper, this step is always needed
tt = TT_Scraper(wait_time=0.3, output_files_fp="data/")

# Define list of TikTok ids (ids can be string or integer) 
data = pd.read_csv("data/seedlist.csv")
my_list = data["ids"].tolist()

# Insert list into scraper
tt.scrape_list(ids = my_list, scrape_content = True, batch_size = None, clear_console = True)
```

The `scrape_list` function provides a useful overview of your progress. Enable `clear_console` to clear the terminal output after every scrape. Note that `clear_console` does not work on Windows machines.

```
Queue Information:
Current Queue: 691 / 163,336
Errors in a row: 0
1.10 iteration time
2.89 sec. per video (averaged)
ETA (current queue): 5 days, 10:23:19

---
-> id 7359982080861703457
-> is slide with 17 pictures

```

# Citation
Bukold, Q. (2025). TikTok Content Scraper (Version 1.0) [Computer software]. Weizenbaum Institute. https://doi.org/10.34669/WI.RD/4

# Advanced Usage
## Alternatives to saving the data on drive
The scraper can download metadata and content (video file, images) as well as return them as variables. Metadata is returned as a dictionary or saved as a `.json` file, and content is saved as `.mp4` / `.jpeg` + `.mp3` or returned as an array of binaries. Remember the rule: what is not downloaded is returned.

```python
from TT_Scraper import TT_Scraper

# Configure the scraper, this step is always needed
tt = TT_Scraper(wait_time=0.3, output_files_fp="data/")

# Downloading Everything
tt.scrape(
	id = 7460303767968156958,
	scrape_content = True,
	download_metadata = True,
	download_content = True)
  
# Returning Everything
metadata, content = tt.scrape(
	id = 7460303767968156958,
	scrape_content = True,
	download_metadata = False,
	download_content = False)
  
# Returning one of the two and downloading the other
metadata = tt.scrape(
	id = 7460303767968156958,
	scrape_content = True,
	download_metadata = False,
	download_content = True)
```

## Alternatives to saving the data on the drive II: Overwriting the _download_data function 
Changing the output of `scrape_list()` is a bit more difficult, but can be achieved by overwriting a function called `\_download_data()` that is part of the `TT_Scraper` class. To overwrite the function, one must inherit the class. The variable `metadata_batch` is a list of dictionaries, each containing all the metadata of a video/slide as well as the binary content of a video/slide. 

Let's save the content, but insert the metadata into a database:
```python
from TT_Scraper import TT_Scraper

# create a new class, that inherits the TT_Scraper
class TT_Scraper_DB(TT_Scraper):
	def __init__(self, wait_time = 0.35, output_files_fp = "data/"):
		super().__init__(wait_time, output_files_fp)

	# overwriting download_data function to upsert metadata into database
	def _download_data(self, metadata_batch, download_metadata = True, download_content = True):

		for metadata_package in metadata_batch:
			# insert metadata into database
			self.insert_metadata_to_db(metadata_package)
	
		# downloading content
		super()._download_data(metadata_batch, download_metadata=False, download_content=True)

	def insert_metadata_to_db(metadata_package)
		...
		return None

tt = TT_Scraper_DB(wait_time = 0.35, output_files_fp = "data/")
tt.scrape_list(my_list)
```
