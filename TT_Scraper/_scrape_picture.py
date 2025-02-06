import requests
import ssl

from ._exceptions_custom import *

def _scrape_picture(self, metadata):
    # get picture from web data
    try:
        metadata_images = metadata["__DEFAULT_SCOPE__"]['webapp.video-detail']['itemInfo']['itemStruct']['imagePost']['images']
        self.log.info("-> is slide with {} pictures".format(len(metadata_images)))
    except KeyError:
        raise VideoNotFoundError
    
    # download pictures
    picture_content_binary = (len(metadata_images)) * [None]
    for i in range(len(metadata_images)):
        tt_pic_url = metadata_images[i]["imageURL"]["urlList"][0]
        try:
            tt_pic = self.request_and_retain_cookies(tt_pic_url)
        except (requests.exceptions.ChunkedEncodingError, ConnectionError, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError, ssl.SSLError, requests.exceptions.SSLError):
            raise RetryLaterError
        
        picture_content_binary[i] = tt_pic.content
        metadata_images[i].pop("imageURL")
    
    picture_formats = metadata_images
    return picture_content_binary, picture_formats