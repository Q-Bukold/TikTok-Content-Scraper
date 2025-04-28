import time
import sys
import traceback
import json
from bs4 import BeautifulSoup
import json
import time
import browser_cookie3
import pprint

from ._exceptions_custom import *
from .HTML_Scraper import HTML_Scraper

class TT_Scraper(HTML_Scraper):
    def __init__(self, wait_time = 0.35, output_files_fp = "data/", browser_name = None):
        super().__init__(wait_time, output_files_fp)
        if browser_name:
            self.cookies = getattr(browser_cookie3, browser_name)(domain_name=".tiktok.com")
    
    from ._scrape_video import _scrape_video
    from ._scrape_picture import _scrape_picture
    from ._filter_tiktok_data import _force_to_int, _prep_hashtags_and_mentions, _filter_tiktok_data
    from ._download_data import _download_data, write_video, write_pictures, write_metadata_package, write_slide_audio
    from ._exception_handler import _exception_handler


    def scrape_list(self, ids : list = None, scrape_content : bool = True, batch_size : int = 0, clear_console = False, total_videos=0, already_scraped_count=0, total_errors=0):
        '''
        This pipeline makes use of the scrape function to scrape a list of video or slide IDs.
        
        This function handles errors. If a known error is occuring, the error code will be part of the metadata package which is downloaded to the output folder as a json.
        
        Error Codes:
        error_code = "D" -> "No data from URL"
        error_code="I" -> "The scraped HTML code could not provide the searched metadata elements"
        error_code="V" -> "No data from URL" <legacy error code>
        error_code="O" -> "Some other error" <code is only used in development>

        Parameters
        ----------
        id : str 
            The id of the TikTok content is typically found in the URL when sharing a video or slide.

        scrape_content : bool
            False = The scraper only scrapes metadata.
            True = The scraper also scrapes the content binaries.

        batch_size : int
            Configures how many data is scraped before it is writen to the output folder. A higher batch size can lead to a faster scraper, but more memory usage. This parameter is also a first step towards multithreading the writig process.
        
        clear_console : bool
            !Caution this function only works on linux and mac!
            False = Nothing happens.
            True = The console output is cleared after every download. This improves readability.
        
        total_videos : int
            This parameter changes the initial value of the logger to a specific integer. This is mainly useful, if you connect the scraper to a database.

        already_scraped_count : int
            This parameter changes the initial value of the logger to a specific integer. This is mainly useful, if you connect the scraper to a database.
        
        total_errors : int
            This parameter changes the initial value of the logger to a specific integer. This is mainly useful, if you connect the scraper to a database.
        '''

        # initialisation        
        self.queue_length = len(ids)
        self.log.info(f"Length of Queue = {str(self.queue_length)}")

        ## statistics
        self.total_videos = total_videos
        self.already_scraped_count = already_scraped_count
        self.total_errors = total_errors
        
        # scrape batches of data
        batch_of_metadata = []
        for self.iterations, id in enumerate(ids, start=1):
                # logging
                start = time.time()
                self._logging_queue_progress()

                # scraping
                self.log.info(f"-> id {id}")
                metadata_package, content_binary = self.scrape(id=id, scrape_content=scrape_content, download_metadata=False, download_content=False)
                metadata_package["content_binary"] = content_binary
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
                if clear_console:
                    self._clear_console()

        self._logging_queue_progress()
        if batch_of_metadata:
            self.log.info("Final output...")
            self._download_data(metadata_batch = batch_of_metadata)
        self.log.info("Queue ended.\n")

    def scrape(self, id, scrape_content : bool = False, download_metadata = True, download_content = True):
        """
        Scrapes a single TikTok video based on its ID. A slide returns a json-like dictionary for all metadata and a dictionary containing the pictures and music. A video returns a json-like dictionary for all metadata and the binaries of the mp4.


        This function handles errors. If a known error is occuring, the error code will be part of the metadata package which is ether downloaded to the output folder as a .json or returned.
        
        Error Codes:
        error_code = "D" -> "No data from URL"
        error_code="I" -> "The scraped HTML code could not provide the searched metadata elements"
        error_code="V" -> "No data from URL" <legacy error code>
        error_code="O" -> "Some other error" <code is only used in development>

        Parameters
        ----------
        id : str 
            The id of the TikTok content is typically found in the URL when sharing a video or slide.

        scrape_content : bool
            False = The scraper only scrapes metadata.
            True = The scraper also scrapes the content binaries.

        download_metadata : bool
            True = The metadata is downloaded to the output folder specifed when initiating the TT_Scraper Class. 
            False = The metadata is returned as an output of this function.
        
        download_content : bool
            True = The content (mp4, mp3, jpeg) is downloaded into the output folder specifed when initiating the TT_Scraper Class.
            False = The content binaries are returned as an output of this function

        """
        id = str(id)
        try:
            _ = int(id)
        except ValueError:
            self.log.error("The provided input is not an ID.")
            raise ValueError
        
        # variables for the scraped data:
        binary_video = None
        binaries_slides = None
        binary_slides_audio = None
        metadata_package = dict()

        try:
            # scraping html data
            requested_data = self.request_and_retain_cookies(f"https://www.tiktok.com/@tiktok/video/{id}")
            html_parser = BeautifulSoup(requested_data.text, "html.parser")
            rehydration_data = html_parser.find('script', attrs={'id':"__UNIVERSAL_DATA_FOR_REHYDRATION__"})
            try:
                rehydration_data_json = json.loads(rehydration_data.string)
            except AttributeError:
                raise RetryLaterError

            # filtering html data
            if rehydration_data_json:
                try:
                    interesting_elements = rehydration_data_json["__DEFAULT_SCOPE__"]['webapp.video-detail']['itemInfo']['itemStruct']
                except KeyError:
                    raise ItemInfoError
            else:
                self.log.info(f"https://www.tiktok.com/@tiktok/video/{id}")
                raise NoDataFromURL
            metadata_package = self._filter_tiktok_data(interesting_elements)

            filepath = f"{self.VIDEOS_OUT_FP}tiktok_{id}_*"
            metadata_package["file_metadata"]["filepath"] = filepath

            # scraping content, if requested by user
            if scrape_content:
                try:
                    binary_video = self._scrape_video(metadata = rehydration_data_json)
                    metadata_package["file_metadata"]["is_slide"] = False
                except VideoIsPicture:
                    binaries_slides, picture_formats, binary_slides_audio = self._scrape_picture(metadata = rehydration_data_json)
                    metadata_package["file_metadata"]["is_slide"] = True
                    metadata_package["file_metadata"]["picture_formats"] = picture_formats

        # handling exceptions        
        except NoDataFromURL:
            error_code = "D"
            self.log.warning("No data from URL")
            metadata_package = self._exception_handler(id, error_code, "NoDataFromURL")
            content_binary = None
        except ItemInfoError:
            error_code="I"
            self.log.warning("The scraped HTML code could not provide the searched metadata elements")
            metadata_package = self._exception_handler(id, error_code, "ItemInfoError")
            content_binary = None
        except VideoNotFoundError:
            error_code="V"
            self.log.warning("No data from URL")
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
        
        # create package of binary contents (videos, pictures, music) 
        if binary_video:
            content_binary = {"type": "video", "mp4_binary": binary_video}
        elif binaries_slides:
            content_binary = {"type": "slide", "slide_pictures": binaries_slides, "slide_audio": binary_slides_audio}
        else:
            content_binary = None      

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

    def scrape_user(self, username, download_metadata = True):
        """
        Scrapes a single user page based on the username.

        Parameters
        ----------
        username : str 
            The username of the profile. It can be found in the URL when opening the profile via a web browser. Insert the username with or without an "@"

        download_metadata : bool
            True = The metadata is downloaded to the output folder specifed when initiating the TT_Scraper Class. 
            False = The metadata is returned as an output of this function.
        """
        if "@" in username:
            username = str.replace(username, "@", "")
        
        # scraping html data
        requested_data = self.request_and_retain_cookies(f"https://www.tiktok.com/@{username}")
        soup = BeautifulSoup(requested_data.text, "html.parser")
        rehydration_data = soup.find('script', attrs={'id':"__UNIVERSAL_DATA_FOR_REHYDRATION__"})

        rehydration_data_json = json.loads(rehydration_data.string)

        # filtering html data
        user_data = rehydration_data_json["__DEFAULT_SCOPE__"]["webapp.user-detail"]["userInfo"]

        filepath = f"{self.VIDEOS_OUT_FP}tiktok_user_{username}.json"

        if download_metadata:
            self.write_metadata_package(filepath=filepath, metadata_package=user_data)
        else:
            return user_data

        # handling exceptions <work in progress>       
