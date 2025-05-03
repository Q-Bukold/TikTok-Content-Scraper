from pprint import pprint
import os
import json
import pandas as pd
from prefect import flow, task
from prefect.logging import get_run_logger
from prefect.task_runners import SequentialTaskRunner

from scrape_user import user_scraper
from scrape_metadata import metadata_scraper

@task(name="creating output folder")
def _init_output_location(output_folder : str):
    # if the directory is not present then create it. 
    if not os.path.isdir(output_folder): 
        os.makedirs(output_folder)

@task(name="storing json")
def write_metadata_package(filepath, metadata_package):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(metadata_package, f, ensure_ascii=False, indent=4)

@task(name="scraping user")
def user_scraper_p(x):
    return user_scraper(x)

@task(name="scraping user")
def metadata_scraper_p(x):
    return metadata_scraper(x)

@flow(log_prints=True, name="TikTok-Content-Scraper", task_runner=SequentialTaskRunner())
def scrape_list(output_folder : str = "scraped_data"):
    logger = get_run_logger()
    input = pd.read_pickle("seedlist.pkl")
    _init_output_location(output_folder)

    for i, x in enumerate(input):
        x = str(x)
        if x.isdigit():
            # start content scraping
            content_metadata = metadata_scraper_p(x)
            write_metadata_package(filepath=f"{output_folder}/content_{x}.json", metadata_package=content_metadata)
        else:
            # start user scraping
            user_metadata = user_scraper(x)
            write_metadata_package(filepath=f"{output_folder}/user_{x}.json", metadata_package=user_metadata)


if __name__ == "__main__":
    input_lst = ["cdu", "7496425065773288726"]
    pd.to_pickle(input_lst, "seedlist.pkl")
    scrape_list()
