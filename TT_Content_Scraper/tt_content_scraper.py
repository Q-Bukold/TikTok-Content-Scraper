import os
from pathlib import Path
import logging


from .data_management.base_scraper import BaseScraper
from .scraper_functions.scrape_metadata import scrape_metadata
from .scraper_functions.scrape_user import scrape_user
from .data_management.logger import logger


class TT_Content_Scraper(BaseScraper):
    def __init__(self,
                wait_time = 0.35,
                output_files_fp = "data/",
                progress_file_fn = "progress_tracking/scraping_progress.db"):
        super().__init__(wait_time,output_files_fp,progress_file_fn)

        logger.info("Scraper Initialized")
    
    def _exception_handler(func):
        def inner_function(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except TypeError:
                print(f"{func.__name__} raised an TypeError")
        return inner_function
    
    def scrape_pending(self, only_content=False, only_users=False):
    
        if only_content:
            seed_type = "content"
        elif only_users:
            seed_type = "user"
        else:
            seed_type = "all"
        
        continue_scraping = True
        while continue_scraping:
            seedlist = self.get_pending_objects(type=seed_type, limit=100)
            if len(seedlist) == 0:
                continue_scraping=False

            for seed in seedlist.items():
                id = seed[0]
                type = seed[1]["type"]
                title = seed[1]["title"]

                if type == "user":
                    self._user_action_protocol(id)

    #@_exception_handler
    def _user_action_protocol(self, id):
        filepath = os.path.join("users/", f"{id}.json")
        Path("users/").mkdir(parents=True, exist_ok=True)
        user_data = scrape_user(id)
        self._write_metadata_package(user_data, filepath)
        self.mark_completed(id, filepath)
