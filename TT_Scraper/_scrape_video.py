import requests
import certifi
import ssl

from ._exceptions_custom import *

def _scrape_video(self, metadata):
    # edited version of pyktok.save_tiktok() (https://github.com/dfreelon/pyktok)

    # get video from web data
    try:
        tt_video_url = metadata["__DEFAULT_SCOPE__"]['webapp.video-detail']['itemInfo']['itemStruct']['video']['playAddr']
        if tt_video_url == '':
            tt_video_url = metadata["__DEFAULT_SCOPE__"]['webapp.video-detail']['itemInfo']['itemStruct']['video']['downloadAddr']
    except KeyError:
        raise VideoNotFoundError
    
    # download video content
    try:
        tt_video = self.request_and_retain_cookies(tt_video_url)
    except requests.exceptions.MissingSchema:
        # url seems to lead to a picture, not a video
        raise VideoIsPicture
    except (requests.exceptions.ChunkedEncodingError, ConnectionError, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError, ssl.SSLError, requests.exceptions.SSLError):
        raise RetryLaterError

    # permission error
    if str(tt_video) == "<Response [403]>" or not tt_video:
            print(f"\n{tt_video}")
            print(tt_video_url)
            tt_video_url = tt_video_url.replace("=tt_chain_token", "")
            tt_video = self.request_and_retain_cookies(tt_video_url)

    return tt_video.content

