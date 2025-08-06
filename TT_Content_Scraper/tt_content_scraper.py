import os
from pathlib import Path
import logging
import time
from datetime import datetime, timedelta
import statistics


from .data_management.base_scraper import BaseScraper
from .scraper_functions.scrape_metadata import scrape_metadata
from .scraper_functions.scrape_user import scrape_user
from .data_management.logger import logger


class TT_Content_Scraper(BaseScraper):
    def __init__(self,
                wait_time = 0.35,
                output_files_fp = "data/",
                progress_file_fn = "progress_tracking/scraping_progress.db",
                clear_console = False):
        super().__init__(wait_time,output_files_fp,progress_file_fn)

        logger.info("Scraper Initialized")

        self.WAIT_TIME = wait_time
        self.iter_times = []
        self.ITER_TIME = 0
        self.iterations = 0
        self.repeated_error = 0
        self.clear_console = clear_console
    
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
        
        while True:
            self._logging_queue_progress(type = seed_type)
            seedlist = self.get_pending_objects(type=seed_type, limit=100)
            assert len(seedlist) > 0, f"No more pending objects of type {seed_type} to scrape"
            for self.iterations, seed in enumerate(seedlist.items()):
                start = time.time()
                id = seed[0]
                type = seed[1]["type"]
                title = seed[1]["title"]

                if type == "user":
                    self._user_action_protocol(id)
                elif type == "content":
                    self._content_action_protocol(id)

                # measure time and set wait time
                stop = time.time()
                self.ITER_TIME = stop - start
                wait_time_left = max(0, self.WAIT_TIME - self.ITER_TIME)
                self.ITER_TIME = self.ITER_TIME + wait_time_left

                # succesfull run
                if self.clear_console:
                    self._clear_console()
                self._logging_queue_progress(type = seed_type)
                time.sleep(wait_time_left)
                self.repeated_error = 0


    #@_exception_handler
    def _user_action_protocol(self, id):
        filepath = os.path.join("users/", f"{id}.json")
        Path("users/").mkdir(parents=True, exist_ok=True)
        user_data = scrape_user(id)
        self._write_metadata_package(user_data, filepath)
        self.mark_completed(id, filepath)

    def _content_action_protocol(self, id):
        None
    
    def _logging_queue_progress(self, type):
        stats = self.get_stats(type)
        self.already_scraped_count = stats["completed"]
        self.total_errors = stats["errors"]
        self.total_videos = self.already_scraped_count + self.total_errors + stats["pending"] + stats["retry"]

        # calculate ETA
        self.iter_times.insert(0, self.ITER_TIME)
        if len(self.iter_times) > 100: self.iter_times.pop(0)

        if self.iterations % 15 == 0 and self.iterations < 2_000:
            self.mean_iter_time = statistics.mean(self.iter_times)
            self.queue_eta = str(timedelta(seconds=int(stats["pending"] * self.mean_iter_time)))
        elif (self.iterations) % 501 == 0:
            self.queue_eta = str(timedelta(seconds=int(stats["pending"] * self.mean_iter_time)))
        
        if self.total_videos > 0 or self.already_scraped_count > 0:
            logger.info(f"Scraped objects: {self.already_scraped_count :,} / {self.total_videos :,}")
            logger.info(f"-> minus errors: {(self.already_scraped_count) - (self.total_errors) :,} / {self.total_videos :,}")

        if self.repeated_error > 0:
            logger.info(f"Errors in a row: {self.repeated_error}")

        logger.info(str(round(self.ITER_TIME, 2)) + " sec. iteration time")
        logger.info(str(round(self.mean_iter_time, 2)) + " sec. per video (averaged)")
        logger.info(f"ETA (current queue): {self.queue_eta}\n***\n")

        #logger.info("Disk Information:")
        #_check_disk_usage((self.already_scraped_count + self.iterations), self.mean_iter_time, self.VIDEOS_OUT_FP, stop_at_tb = 0.01)
        
        return None

    def _clear_console(self):
        os.system('clear')