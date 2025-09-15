from TT_Content_Scraper import TT_Content_Scraper

# initialize the scraper
scraper = TT_Content_Scraper(
    wait_time=0.35,
    output_files_fp="data/",
    progress_file_fn="progress_tracking/scraping_progress.db",
    clear_console=False # only works with mac and linux systems
)

# add content ids you want to scrape
scraper.add_objects(ids=["7398323154424171806", "7447600730267061526"], title="from seedlist aug 20", type="content")

# add usernames you want to scrape
scraper.add_objects(ids=["tagesschau", "bundeskanzler"], title="from seedlist aug 20", type="user")

# start scraping all objects you added that have not been scraped
scraper.scrape_pending(scrape_files=True) # scrape_files indicated if you want to scrape the mp3/mp4/jpeg of all content.
