import json
import requests
from bs4 import BeautifulSoup
import browser_cookie3
from ._filter_tiktok_data import _filter_tiktok_data


def scrape_metadata(video_id, browser_name=None) -> dict:
    cookies = {}

    if browser_name is None:
        browser_name = browser_name

    if browser_name is not None:
            cookies = getattr(browser_cookie3, browser_name)(domain_name='.tiktok.com')

    headers = {
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'en-US,en;q=0.8',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'referer' : 'https://www.tiktok.com/'
    }

    response = requests.get(
            f"https://www.tiktok.com/@tiktok/video/{video_id}",
            headers=headers,
            cookies=cookies,
            timeout=20
    )

    soup = BeautifulSoup(response.text, "html.parser")
    script_tag = soup.find('script', id="__UNIVERSAL_DATA_FOR_REHYDRATION__")
    data = json.loads(script_tag.string)
    metadata = data["__DEFAULT_SCOPE__"]["webapp.video-detail"]["itemInfo"]["itemStruct"]
    sorted = _filter_tiktok_data(data_slot=metadata)
    return sorted