import os
import os.path
import pytz
import requests
import browser_cookie3
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import time
import statistics
import traceback
from pprint import pprint
from pathlib import Path

class HTML_Scraper:
        def __init__(self,
                    wait_time = 0.35,
                    output_files_fp = "data/"):
            
            # output folder
            Path(output_files_fp).mkdir(parents=True, exist_ok=True)

            # constants
            self.IST = pytz.timezone('Europe/Berlin')
            self.ALLOW_REPEATED_ERRORS = 20
            self.VIDEOS_OUT_FP = output_files_fp
            self.WAIT_TIME = wait_time
            self.ITER_TIME = self.WAIT_TIME

            # Replaced if queue is used:
            self.total_errors = 0 
            self.repeated_error = 0 
            self.already_scraped_count = 0 
            self.total_videos = 0 
            self.iterations = 0
            self.iter_times = []
            self.mean_iter_time = 0
            self.queue_eta = None

            # request headers
            self._innit_request_headers()

            # logging
            self.log = self._innit_logger()
        
        from ._innit_request_headers import _innit_request_headers
        from ._logging_queue_progress import _logging_queue_progress
        from ._innit_logger import _innit_logger
        from ._clear_console import _clear_console
        
        def info(self):
                pprint(vars(self))
        
        def request_and_retain_cookies(self, url, browser_name=None):
                if browser_name is not None:
                        self.cookies = getattr(browser_cookie3,browser_name)(domain_name='www.tiktok.com')

                r = requests.get(url,
                        allow_redirects=False, # may have to set to True
                        headers=self.headers,
                        cookies=self.cookies,
                        timeout=20,
                        stream=False)
                
                # retain any new cookies that got set in this request
                self.cookies = r.cookies

                return r



        

