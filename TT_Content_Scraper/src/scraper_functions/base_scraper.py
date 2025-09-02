import logging
import json
import logging
import json
import requests
import browser_cookie3
from bs4 import BeautifulSoup
import json
from pprint import pprint
import ssl
import time


from ._filter_tiktok_data import _filter_tiktok_data

logger = logging.getLogger('TTCS.Base')

class RetryLaterError(Exception):
     """Something could not be scraped, maybe later..."""
     pass

class BaseScraper():
    def __init__(self, browser_name = None):
        self.headers = {
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'en-US,en;q=0.8',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'referer' : 'https://www.tiktok.com/'
        }   
        self.cookies = dict()

        if browser_name:
            self.cookies = getattr(browser_cookie3, browser_name)(domain_name='.tiktok.com')  # Inspired by pyktok
            
    def request_and_retain_cookies(self, url, retain = True) -> requests.Response:
            
            response = requests.get(url,
                    allow_redirects=True, # may have to set to True
                    headers=self.headers,
                    cookies=self.cookies,
                    timeout=20,
                    stream=False)
            
            # retain any new cookies that got set in this request
            if retain:
                self.cookies = response.cookies

            return response

    def scrape_metadata(self, video_id) -> dict:

        retries = 0
        script_tag = None
        while script_tag is None and retries <= 3:
            response = self.request_and_retain_cookies(url=f"https://www.tiktok.com/@tiktok/video/{video_id}")
            soup = BeautifulSoup(response.text, "html.parser")
            script_tag = soup.find('script', id="__UNIVERSAL_DATA_FOR_REHYDRATION__")

            if script_tag is not None:
                break # success
            else:
                retries += 1
                time.sleep(0.1)
        else:
            if script_tag is None: raise KeyError("__UNIVERSAL_DATA_FOR_REHYDRATION__ not in response")

        data = json.loads(script_tag.string)
        metadata = data["__DEFAULT_SCOPE__"]["webapp.video-detail"]["itemInfo"]["itemStruct"]
        sorted_metadata = _filter_tiktok_data(data_slot=metadata)

        # find link to binary of slide (pictures), music or video file
        images_binaries_addr = metadata.get('imagePost', None)
        if images_binaries_addr: images_binaries_addr = images_binaries_addr.get("images", None)
        
        audio_binary_addr = metadata.get('music', None)
        if audio_binary_addr: audio_binary_addr = audio_binary_addr.get("playUrl", None)
        
        video_binary_addr = metadata.get('video', None)
        if video_binary_addr: video_binary_addr = video_binary_addr.get("playAddr", None)
        if video_binary_addr == '':
            video_binary_addr = metadata.get('video', None).get("downloadAddr", None)

        link_to_binaries = {
            "mp4" : video_binary_addr,
            "mp3" : audio_binary_addr,
            "jpegs" : images_binaries_addr
            }

        return sorted_metadata, link_to_binaries

    def scrape_user(self, username : str) -> dict:
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
        
        response = self.request_and_retain_cookies(url=f"https://www.tiktok.com/@{username}")
        
        soup = BeautifulSoup(response.text, "html.parser")
        rehydration_data = soup.find('script', attrs={'id':"__UNIVERSAL_DATA_FOR_REHYDRATION__"})

        rehydration_data_json = json.loads(rehydration_data.string)

        # filtering html data
        user_data = rehydration_data_json["__DEFAULT_SCOPE__"]["webapp.user-detail"]["userInfo"]
        
        return user_data

    def scrape_binaries(self, links) -> dict:
        audio_binary = None
        video_binary = None
        picture_content_binary = None
        retries = 0

        while retries <= 3:
            try:
                if links["mp3"]:
                    audio_binary = self._scrape_audio(links["mp3"])
                if links["mp4"]:
                    video_binary = self._scrape_video(links["mp4"])
                if links["jpegs"]:
                    metadata_images = links["jpegs"]
                    logger.info("-> is slide with {} pictures".format(len(metadata_images)))
                    picture_content_binary = (len(metadata_images)) * [None]
                    for i in range(len(metadata_images)):
                        tt_pic_url = metadata_images[i]["imageURL"]["urlList"][0]
                        # metadata_images[i].pop("imageURL")
                        # picture_formats = metadata_images

                        pic_binary = self._scrape_picture(tt_pic_url)
                        picture_content_binary[i] = pic_binary
                
                return {"mp3": audio_binary,
                        "mp4": video_binary,
                        "jpegs": picture_content_binary}
            except (requests.exceptions.ChunkedEncodingError, ConnectionError, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError, ssl.SSLError, requests.exceptions.SSLError) as e:
                logger.warning(f"{e} - retrying max. 3 times with 0.5s sleep in between")
                time.sleep(0.1)
                retries += 1
                continue
        
        raise ConnectionError


    def _scrape_video(self, url):
        # edited version of pyktok.save_tiktok() (https://github.com/dfreelon/pyktok)
        # download video content
        tt_video = self.request_and_retain_cookies(url, retain=False)

        # permission error
        if str(tt_video) == "<Response [403]>" or not tt_video:
                url = url.replace("=tt_chain_token", "")
                tt_video = self.request_and_retain_cookies(url, retain=False)

        if str(tt_video) == "<Response [403]>":
            raise ConnectionError
        else:         
            return tt_video.content

    def _scrape_picture(self, url):
        # request pictures
        tt_pic = self.request_and_retain_cookies(url, retain=False)
        if str(tt_pic) == "<Response [403]>":
            raise ConnectionError
        else: 
            return tt_pic.content
            
    def _scrape_audio(self, url):
        tt_audio = self.request_and_retain_cookies(url, retain=False)
        if str(tt_audio) == "<Response [403]>":
            raise ConnectionError
        else: 
            return tt_audio.content