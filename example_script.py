from TT_Scraper import TT_Scraper

# Configure the scraper, this step is always needed
tt = TT_Scraper(wait_time=0.3, output_files_fp="data/")

# Download all metadata as a .json and all content as .mp4/.jpeg
tt.scrape(id = 7365430669880724769, scrape_content = True)
