# What is it?

This is a modified version of the TikTok-Content-Scraper featuring support for an SQL database integration. Use the .sql script to create your own database. Then add all the relevant video or slide IDs to the scrape_logs table. You can then use the scrape_to_db.py script to select input IDs from the scrape_logs table and insert the scraped metadata into the other tables. In the event of a non-tragic error, an error code will be stored in the scrape_logs table. I know this branch is not very well documented, yet. Please message me in case of any questions.

---
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
   ```

2. **Install All Dependencies in the Requirements File**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Example Script**:
   ```bash
   python3 scrape_to_db.py
   ```

# Citation
Bukold, Q. (2025). TikTok Content Scraper (Version 1.0) [Computer software]. Weizenbaum Institute. https://doi.org/10.34669/WI.RD/4


## Overwriting the _download_data function 
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
