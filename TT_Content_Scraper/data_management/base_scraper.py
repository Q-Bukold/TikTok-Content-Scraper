import logging
import json
import os
from datetime import datetime
from enum import Enum
from pathlib import Path
import logging
import os
import json

from .object_tracker_db import ObjectTracker
import TT_Content_Scraper.data_management.logger

logger = logging.getLogger('TTCS.Base')

class BaseScraper(ObjectTracker):
    def __init__(self,
                wait_time = 0.35,
                output_files_fp = "data/",
                progress_file_fn = "progress_tracking/scraping_progress.db"):
        
        super().__init__(db_file=progress_file_fn)
        
        self.WAIT_TIME = wait_time

        # create output folder if doesnt exist
        Path(output_files_fp).mkdir(parents=True, exist_ok=True)
        self.output_files_fp = output_files_fp

    # utils
    def _clear_console(self):
        os.system('clear')
            
    # output
    def _write_metadata_package(self, metadata_package, filename):
        with open(f"{self.output_files_fp}{filename}", "w", encoding="utf-8") as f:
            json.dump(metadata_package, f, ensure_ascii=False, indent=4)
        logger.debug(f"--> JSON saved to {filename}")

    def _write_video(self, video_content, filename,):
        with open(f"{self.output_files_fp}{filename}", 'wb') as fn:
            fn.write(video_content)
        logger.debug(f"--> MP4  saved to {filename}")

    def _write_pictures(self, picture_content, filename):
        with open(f"{self.output_files_fp}{filename}", 'wb') as f:
            f.write(picture_content)
        logger.debug(f"--> JPEG saved to {filename}")

    def _write_slide_audio(self, audio_content, filename):
        with open(f"{self.output_files_fp}{filename}", "wb") as f:
            f.write(audio_content)
        logger.debug(f"--> MP3 saved to {filename}")