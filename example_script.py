from TT_Scraper import TT_Scraper

# Configure the scraper, this step is always needed
tt = TT_Scraper(wait_time=0.3, output_files_fp="example_data/")

# Download all metadata as a .json and all content as .mp4/.jpeg
tt.scrape_list(ids = [7398323154424171806, 7447600730267061526], scrape_content = True, clear_console=True)
