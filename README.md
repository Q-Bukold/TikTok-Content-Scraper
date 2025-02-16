# What is it?

This scraper allows you to download both TikTok videos and slides without an official API key. In addition, about 100 metadata about the video, author, music, video file and hashtags can be scraped. The scraper was built as a Python class and can be inherited by a custom parent class. This allows the scraper to be easily connected to a database, for example.

# Usage
## Setup
1. Download the latest version of this repository
2. Open the downloaded folder
3. Pip install all python libraries listed in requirements.txt
4. Run the example_script.py or create you own script.

## Scrape a single video or slide
To scrape the metadata and content of a video, the TikTok ID is required. It can be found in the URL of a video. Let's use the ID 7460303767968156958 to scrape the associated video. In examples/ you can see what a potential output could look like.
```python
from TT_Scraper import TT_Scraper

# Configure the scraper, this step is always needed
tt = TT_Scraper(wait_time=0.3, output_files_fp="data/")

# Download all metadata as a .json and all content as .mp4/.jpeg
tt.scrape(id = 7460303767968156958, scrape_content = True)
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

The scrape_list function provides an useful overview over your progress. Enable "clear_console" to clear the output in terminal after every scrape.
> Caution the clear_console function does not work on Windows machines.

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
Bukold, Q. (2025). TikTok-Content-Scraper (Version 1.0) [Computer software]. https://www.weizenbaum-library.de/handle/id/814

# Advanced Usage
## Alternatives to saving the data on drive
The scraper can download metadata and content (video file, images) as well as return them as variables. The metadata is returned as a dictionary or saved as .json and the content is saved as .mp4 / .jpeg or returned in raw form. The raw form can be stored with a simple file.write(). In each case remember the rule: what is not downloaded is returned.
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

## Alternatives to saving the data on the drive II: .scrape_list() 
Changing the output of scrape_list() is a bit more difficult, but can be achieved by overwriting a function called \_download_data() that is part of the TT_Scraper class. To overwrite the function, one must inherit the class. The variable "metadata_batch" is a list of dictionaries, each containing all the metadata of a video/slide as well as the binary content of a video/slide. 

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
