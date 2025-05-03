from scrape_user import user_scraper
from pprint import pprint
import os
import json
from prefect import flow, task
from prefect.logging import get_run_logger

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

@flow(log_prints=True, name="TikTok-Content-Scraper")
def scrape_list(input : list, output_folder : str = "scraped_data"):
    logger = get_run_logger()
    _init_output_location(output_folder)

    for i, x in enumerate(input):
        x = str(x)
        if x.isdigit():
            # start content scraping
            continue
        else:
            # start user scraping
            user_metadata = user_scraper(x)
            write_metadata_package(filepath=f"{output_folder}/user_{x}.json", metadata_package=user_metadata)


if __name__ == "__main__":
    input_lst = ["cdu", "7496425065773288726"]
    scrape_list(input_lst)
