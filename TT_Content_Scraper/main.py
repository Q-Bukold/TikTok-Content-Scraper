import sys

from .scraper_functions.base_scraper import Scraper
from .scraper_functions import scrape_content_metadata, scrape_user


if __name__ == "__main__":

    if sys.argv[1]:
        MODE = sys.argv[1]
