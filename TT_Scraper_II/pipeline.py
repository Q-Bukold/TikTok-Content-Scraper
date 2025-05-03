from scrape_user import user_scraper
from pprint import pprint
import os
import json

def scrape_list(input : list, output_folder : str = "scraped_data"):
    _init_output_location(output_folder)

    for i, x in enumerate(input):
        user_metadata = user_scraper(x)
        write_metadata_package(filepath=f"{output_folder}/user_{x}.json", metadata_package=user_metadata)


def _init_output_location(output_folder : str):
    # if the directory is not present then create it. 
    if not os.path.isdir(output_folder): 
        os.makedirs(output_folder)

def write_metadata_package(filepath, metadata_package):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(metadata_package, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    input_lst = ["cdu", "7496425065773288726"]

    scrape_list(input_lst)
