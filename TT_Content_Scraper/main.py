import sys

from .data_management.base_scraper import Scraper
from .scraper_functions import scrape_metadata, scrape_user


if __name__ == "__main__":

    if sys.argv[1]:
        MODE = sys.argv[1]
