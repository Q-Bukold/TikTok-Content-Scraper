from scrape_user import user_scraper
from pprint import pprint

json_like = user_scraper("cdu")
pprint(json_like)