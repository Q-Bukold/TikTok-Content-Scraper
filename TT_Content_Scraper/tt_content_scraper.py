import os
from pathlib import Path
import time
from datetime import timedelta
import statistics
from pprint import pprint
import json
import requests

from .src.logger import logger
from .src.object_tracker_db import ObjectTracker
from .src.scraper_functions.base_scraper import BaseScraper

# initialize html scraper
base_scraper = BaseScraper()


class TT_Content_Scraper(ObjectTracker):
    def __init__(self,
                wait_time = 0.35,
                output_files_fp = "data/",
                progress_file_fn = "progress_tracking/scraping_progress.db",
                clear_console = False,
                browser_name = None):
        
        # initialize object tracker (database of pending and finished objects (ids))
        super().__init__(progress_file_fn)

        # create output folder if doesnt exist
        Path(output_files_fp).mkdir(parents=True, exist_ok=True)
        self.output_files_fp = output_files_fp

        self.WAIT_TIME = wait_time
        self.iter_times = []
        self.ITER_TIME = 0
        self.iterations = 0
        self.repeated_error = 0
        self.clear_console = clear_console

        logger.info("Scraper Initialized\n***")
        
    def scrape_pending(self, only_content=False, only_users=False, scrape_files = False):
    
        if only_content:
            seed_type = "content"
        elif only_users:
            seed_type = "user"
        else:
            seed_type = "all"
        
        while True:
            #self._logging_queue_progress(type = seed_type)
            seedlist = self.get_pending_objects(type=seed_type, limit=100)
            assert len(seedlist) > 0, f"No more pending objects of type {seed_type} to scrape"
            for self.iterations, seed in enumerate(seedlist.items()):
                start = time.time()

                id = seed[0]
                type = seed[1]["type"]
                #title = seed[2]["title"]

                if self.clear_console:
                    self._clear_console()

                logger.info(f"Scraping ID: {id}")
                self._logging_queue_progress(type = seed_type)


                if type == "user":
                    self._user_action_protocol(id)
                elif type == "content":
                    self._content_action_protocol(id, scrape_files)

                # measure time and set wait time
                stop = time.time()
                self.ITER_TIME = stop - start
                wait_time_left = max(0, self.WAIT_TIME - self.ITER_TIME)
                self.ITER_TIME = self.ITER_TIME + wait_time_left
                
                # succesfull run
                logger.info("Continuing with next ID...\n\n--------")

                time.sleep(wait_time_left)
                self.repeated_error = 0


    def _user_action_protocol(self, id):
        filepath = os.path.join(self.output_files_fp, "user_metadata/", f"{id}.json")
        Path(self.output_files_fp, "user_metadata/").mkdir(parents=True, exist_ok=True)
        user_data = base_scraper.scrape_user(id)
        self._write_metadata_package(user_data, filepath)
        self.mark_completed(id, filepath)
        self.n_scraped_total += 1

    def _content_action_protocol(self, id, scrape_files):
        filepath = os.path.join(self.output_files_fp, "content_metadata/", f"{id}.json")
        Path(self.output_files_fp, "content_metadata/").mkdir(parents=True, exist_ok=True)

        try:
            sorted_metadata, link_to_binaries = base_scraper.scrape_metadata(id)
        except KeyError as e:
            logger.warning(f"ID {id} did not lead to any metadata - KeyError {e}")
            self.mark_error(id, str(e))
            self.n_errors_total += 1
            self.n_pending -= 1
            return None
    
        if scrape_files:
            """To later find all files relating to an ID search for "self.output_files_fp/content_files/tiktok_{id}*"""
            Path(self.output_files_fp, "content_files/").mkdir(parents=True, exist_ok=True)

            try:
                binaries : dict = base_scraper.scrape_binaries(link_to_binaries)
            except ConnectionError as e:
                logger.warning(f"ID {id} did not lead to any downloadable files - KeyError {e}")
                self.mark_error(id=id)
                self.n_errors_total += 1
                self.n_pending -= 1
                return None

            
            # if video available
            if binaries["mp4"]:
                sorted_metadata["file_metadata"]["is_slide"] = False
                self._write_video(video_content=binaries["mp4"],
                                  filename=Path(self.output_files_fp, "content_files/", f"tiktok_video_{id}.mp4"))
            # if slide (with music) available
            elif binaries["jpegs"]:
                sorted_metadata["file_metadata"]["is_slide"] = True
                for i, jpeg in enumerate(binaries["jpegs"]):
                    self._write_pictures(picture_content=jpeg,
                                         filename=Path(self.output_files_fp, "content_files/", f"tiktok_picture_{id}_{str(i)}.jpeg"))
                if binaries["mp3"]:
                    self._write_audio(audio_content=binaries["mp3"],
                                            filename=Path(self.output_files_fp, "content_files/", f"tiktok_audio_{id}.mp3"))

        self._write_metadata_package(sorted_metadata, filepath)
        self.mark_completed(id, filepath)
        self.n_scraped_total += 1
        self.n_pending -= 1

    def _logging_queue_progress(self, type):
        if self.iterations == 0:
            stats = self.get_stats(type)
            self.n_scraped_total = stats["completed"]
            self.n_errors_total = stats["errors"]
            self.n_pending = stats["pending"]
            self.n_retry= stats["retry"]     
            self.n_total = self.n_scraped_total + self.n_errors_total + self.n_pending + self.n_retry  
    

        # calculate ETA
        self.iter_times.insert(0, self.ITER_TIME)
        if len(self.iter_times) > 100: self.iter_times.pop(0)

        if self.iterations % 15 == 0 and self.iterations < 2_000:
            self.mean_iter_time = statistics.mean(self.iter_times)
            self.queue_eta = str(timedelta(seconds=int(self.n_pending * self.mean_iter_time)))
        elif self.iterations % 501 == 0:
            self.queue_eta = str(timedelta(seconds=int(self.n_pending * self.mean_iter_time)))
        
        if self.n_total > 0 or self.n_scraped_total > 0:
            logger.info(f"Scraped objects ► {(self.n_scraped_total + self.n_errors_total) :,} / {self.n_total :,}")
            logger.info(f"...minus errors ► {self.n_scraped_total :,}") #/ {(self.n_total-self.n_errors_total) :,}

        if self.repeated_error > 0:
            logger.info(f"Errors in a row ► {self.repeated_error}")

        logger.info("Iteration time ► " + str(round(self.ITER_TIME, 2)) + " sec.")
        logger.info("......averaged ► " +str(round(self.mean_iter_time, 2)) + " sec.")
        logger.info(f"ETA ► {self.queue_eta}\n↓↓↓")

        #logger.info("Disk Information:")
        #_check_disk_usage((self.already_scraped_count + self.iterations), self.mean_iter_time, self.VIDEOS_OUT_FP, stop_at_tb = 0.01)
        
        return None

    # utils
    def _clear_console(self):
        os.system('clear')
            
    # output
    def _write_metadata_package(self, metadata_package, filename):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(metadata_package, f, ensure_ascii=False, indent=4)
        logger.debug(f"▼ JSON saved to {filename}")

    def _write_video(self, video_content, filename,):
        with open(filename, 'wb') as fn:
            fn.write(video_content)
        logger.debug(f"▼ MP4  saved to {filename}")

    def _write_pictures(self, picture_content, filename):
        with open(filename, 'wb') as f:
            f.write(picture_content)
        logger.debug(f"▼ JPEG saved to {filename}")

    def _write_audio(self, audio_content, filename):
        with open(filename, "wb") as f:
            f.write(audio_content)
        logger.debug(f"▼ MP3  saved to {filename}")