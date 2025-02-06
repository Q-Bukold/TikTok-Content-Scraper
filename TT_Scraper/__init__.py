import time
import sys
import traceback
import json
from bs4 import BeautifulSoup
import json
import time

from ._exceptions_custom import *
from .HTML_Scraper import HTML_Scraper

class TT_Scraper(HTML_Scraper):
    def __init__(self, wait_time = 0.35, output_files_fp = "data/"):
        super().__init__(wait_time, output_files_fp)
    
    from ._scrape_video import _scrape_video
    from ._scrape_picture import _scrape_picture
    from ._filter_tiktok_data import _force_to_int, _prep_hashtags_and_mentions, _filter_tiktok_data
    from ._download_data import _download_data, write_video, write_pictures, write_metadata_package
    from ._exceptions_handling import _exception_handler
    
    def scrape_list(self, scrape_list : list = None, scrape_content : bool = True, batch_size : int = None, pretty_output = True, total_videos=0, already_scraped_count=0, total_errors=0):

        # initialisation        
        self.queue_length = len(scrape_list)
        self.log.info(f"Length of Queue = {str(self.queue_length)}")

        if not batch_size:
            batch_size = self.queue_length

        ## statistics
        self.total_videos = total_videos
        self.already_scraped_count = already_scraped_count
        self.total_errors = total_errors
        
        # scrape batches of data
        batch_of_metadata = []
        for self.iterations, id in enumerate(scrape_list, start=1):
                # logging
                start = time.time()
                self._logging_queue_progress()

                # scraping
                self.log.info(f"-> id {id}")
                metadata_package, video_content_binary = self.scrape(id=id, scrape_content=scrape_content, download_metadata=False, download_content=False)
                metadata_package["content_binary"] = video_content_binary
                self.repeated_error = 0  

                # save data in memory until stored
                batch_of_metadata.append(metadata_package)
                
                #with open(f"test_batch.json", "w", encoding="utf-8") as f:
                #    json.dump(batch_of_metadata, f, ensure_ascii=False, indent=4)
                
                # stored batch of data
                if len(batch_of_metadata) >= batch_size:
                    # upsert metadata and write mp4s to output dir
                    self.log.info("\nstoring data batch...\n")
                    self._download_data(metadata_batch = batch_of_metadata)
                    
                    # clean up
                    batch_of_metadata = []

                # measure time and set wait time
                stop = time.time()
                self.ITER_TIME = stop - start
                wait_time_left = max(0, self.WAIT_TIME - self.ITER_TIME)
                time.sleep(wait_time_left)
                self.ITER_TIME = self.ITER_TIME + wait_time_left

                # interrupt if too many errors in a row
                if self.repeated_error > self.ALLOW_REPEATED_ERRORS:
                    self.log.ERROR("Too many Errors in a row!")
                    self.log.ERROR(traceback.format_exc())
                    self.log.ERROR("Stopping program...")
                    sys.exit(0)
                
                # end of loop
                if pretty_output:
                    self._clear()

        self._logging_queue_progress()
        if batch_of_metadata:
            self.log.info("Final output...")
            self._download_data(metadata_batch = batch_of_metadata)
        self.log.info("Queue ended.\n")

    def scrape(self, id, scrape_content : bool = False, download_metadata = True, download_content = True):
        id = str(id)
        try:
            # scraping html data
            requested_data = self.request_and_retain_cookies(f"https://www.tiktok.com/@tiktok/video/{id}")
            soup = BeautifulSoup(requested_data.text, "html.parser")
            tt_script = soup.find('script', attrs={'id':"__UNIVERSAL_DATA_FOR_REHYDRATION__"})
            try:
                requested_data_str = json.loads(tt_script.string)
            except AttributeError:
                raise RetryLaterError

            # filtering html data
            if requested_data_str:
                try:
                    interesting_elements = requested_data_str["__DEFAULT_SCOPE__"]['webapp.video-detail']['itemInfo']['itemStruct']
                except KeyError:
                    raise ItemInfoError
            else:
                self.log.info(f"https://www.tiktok.com/@tiktok/video/{id}")
                raise NoDataFromURL
            metadata_package = self._filter_tiktok_data(interesting_elements)

            # scraping content, if requested by user
            if scrape_content == True:
                try:
                    content_binary = self._scrape_video(metadata = requested_data_str)
                    video_fn = f"tiktok_video_{id}.mp4"
                    filepath = f"{self.VIDEOS_OUT_FP}{video_fn}"
                    metadata_package["file_metadata"]["filepath"] = filepath
                    metadata_package["file_metadata"]["is_slide"] = False
                except VideoIsPicture:
                    content_binary, picture_formats = self._scrape_picture(metadata = requested_data_str)
                    video_fn = f"tiktok_picture_{id}_X.jpeg"
                    filepath = f"{self.VIDEOS_OUT_FP}{video_fn}"
                    metadata_package["file_metadata"]["filepath"] = filepath
                    metadata_package["file_metadata"]["is_slide"] = True
                    metadata_package["file_metadata"]["picture_formats"] = picture_formats
            else:
                content_binary = None
                metadata_package["file_metadata"]["filepath"] = None

        # handling exceptions        
        except NoDataFromURL:
            error_code = "D"
            self.log.warning("No data from URL provided")
            metadata_package = self._exception_handler(id, error_code, "NoDataFromURL")
            content_binary = None
        except ItemInfoError:
            error_code="I"
            self.log.warning("The scraped HTML code could not provide the searched metadata elements")
            metadata_package = self._exception_handler(id, error_code, "ItemInfoError")
            content_binary = None
        except VideoNotFoundError:
            error_code="V"
            metadata_package = self._exception_handler(id, error_code, "VideoNotFoundError")
            content_binary = None
        except OtherError:
            error_code="O"
            metadata_package = self._exception_handler(id, error_code, "OtherError")
            content_binary = None
        except RetryLaterError:
            #retry 
            self.repeated_error += 1
            self.log.warning("-> retrying video due to error in package download...")
            time.sleep(self.repeated_error * 3)
            self._innit_request_headers()
            metadata_package, content_binary = self.scrape(id=id, scrape_content=scrape_content, download_metadata=False, download_content=False)
            if self.repeated_error > self.ALLOW_REPEATED_ERRORS:
                self.log.ERROR("too many errors in a row")
                sys.quit(1)
        
        # download or return data
        if download_metadata and download_content:
            metadata_package["content_binary"] = content_binary
            self._download_data(metadata_batch = [metadata_package])
        elif not download_metadata and download_content:
            metadata_package["content_binary"] = content_binary
            self._download_data(metadata_batch = [metadata_package], download_metadata=False)
            return metadata_package
        elif download_metadata and not download_content:
            metadata_package["content_binary"] = content_binary
            self._download_data(metadata_batch = [metadata_package], download_content=False)
            return content_binary
        else:
            return metadata_package, content_binary

