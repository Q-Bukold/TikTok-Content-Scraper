import pandas
import json
import requests
from bs4 import BeautifulSoup
import browser_cookie3
from dataclasses import dataclass
import typing


def scrape_user(username : str, browser_name = None) -> json:
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

    if browser_name is None:
        browser_name = browser_name  # Use the stored browser_name if not provided

    if browser_name is not None:
            cookies = getattr(browser_cookie3, browser_name)(domain_name='.tiktok.com')  # Inspired by pyktok
    
    headers = {'Accept-Encoding': 'gzip, deflate, sdch',
                'Accept-Language': 'en-US,en;q=0.8',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Cache-Control': 'max-age=0',
                'Connection': 'keep-alive',
                'referer' : 'https://www.tiktok.com/'}

    #context_dict = {'viewport': {'width': 0, 'height': 0},
    #                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:58.0) Gecko/20100101 Firefox/58.0'}

    cookies = dict()

    response = requests.get(f"https://www.tiktok.com/@{username}",
            allow_redirects=False, # may have to set to True
            headers=headers,
            cookies=cookies,
            timeout=20,
            stream=False)
    
    # retain any new cookies that got set in this request
    cookies = response.cookies

    soup = BeautifulSoup(response.text, "html.parser")
    rehydration_data = soup.find('script', attrs={'id':"__UNIVERSAL_DATA_FOR_REHYDRATION__"})

    rehydration_data_json = json.loads(rehydration_data.string)

    # filtering html data
    user_data = rehydration_data_json["__DEFAULT_SCOPE__"]["webapp.user-detail"]["userInfo"]
    
    return user_data
