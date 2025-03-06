import pandas as pd
from datetime import datetime
from pprint import pprint # not required

import sqlalchemy
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert

from TT_Scraper import TT_Scraper

class TT_Scraper_DB(TT_Scraper):
    '''
    This Class overwrites functions of the TT_Scraper in order to scrape based on a seedlist in a database and output scraped data back to the database.
    '''
    def __init__(self, wait_time = 0.35, output_files_fp = "tmp/", DB_URL = None):
        super().__init__(wait_time, output_files_fp)    
         # Connect to Database in Network
        self.engine = create_engine(DB_URL, echo=False, pool_pre_ping=True, pool_recycle=1600, connect_args={'connect_timeout': 1600})
        self.Session = sessionmaker(bind=self.engine)
        ## get schema of database
        db_ghost = MetaData()
        db_ghost.reflect(bind=self.engine)
        self.GHOST_DB = db_ghost
    
    def scrape_query(self, sql_query : str = "SELECT id FROM scrape_logs WHERE (scraped_last IS NULL AND encountered_error IS NULL);"):
        queue = pd.read_sql(sql_query, self.engine)
        print(queue)

        ## statistics
        self.total_videos = pd.read_sql("SELECT COUNT(seed_id) FROM scrape_logs;", self.engine)["count"].iloc[0]
        self.already_scraped_count = pd.read_sql("SELECT COUNT(seed_id) FROM scrape_logs WHERE scraped_last is not NULL;", self.engine)["count"].iloc[0]
        self.total_errors = pd.read_sql("SELECT COUNT(seed_id) FROM scrape_logs WHERE encountered_error IN ('M', 'D', 'I', 'V', 'O');", self.engine)["count"].iloc[0]

        self.scrape_list(ids=queue.seed_id, scrape_content=True, batch_size=20,clear_console=True)

    # overwriting download_data function to upsert metadata into database
    def _download_data(self, metadata_batch, download_metadata = True, download_content = True):

        # upserting metadata
        self.upsert_metadata_to_db(metadata_batch)

        # downloading content
        super()._download_data(metadata_batch, download_metadata=True, download_content=True)

    def delete_unused_keys(self, table, input_dict):
        '''Deletes all metadata, that is not inserted into the database. This function is needed to prevent sqlalchemy errors.'''
        columns_needed = table._columns.keys()
        return { key : value for (key, value) in input_dict.items() if key in columns_needed }

    def upsert_metadata_to_db(self, metadata_batch : list[dict] = None):
        '''
        Upserts Metadata to database.
        '''
        timezone = self.IST
        time_now = datetime.now(timezone).strftime('%Y-%m-%d %H:%M:%S')
        self.log.info("-> upserting data")
        
        with self.Session() as sess:
            # get database structure from database
            Scrape_logs = sqlalchemy.Table("scrape_logs", self.GHOST_DB, autoload=True)
            Videos = sqlalchemy.Table("videos", self.GHOST_DB, autoload=True)
            Video_files = sqlalchemy.Table("video_files", self.GHOST_DB, autoload=True)
            Music = sqlalchemy.Table("music", self.GHOST_DB, autoload=True)
            Authors = sqlalchemy.Table("authors", self.GHOST_DB, autoload=True)
            Hashtags = sqlalchemy.Table("hashtags", self.GHOST_DB, autoload=True)

            for metadata_package in metadata_batch:
                video_id = metadata_package["video_metadata"]["id"]
                error_code = metadata_package.get("error_code", None)

                #with open(f"test.json", "w", encoding="utf-8") as f:
                #    json.dump(metadata_package, f, ensure_ascii=False, indent=4)

                if error_code is not None:
                    # error data
                    sess.execute(text(f"UPDATE scrape_logs SET encountered_error = '{error_code}', scraped_last = '{time_now}' WHERE seed_id = {video_id};"))
                    if error_code != "P": #"P" is an Error that still produces valid metadata (just not the video)
                        continue
            
                # video data
                metadata_package["video_metadata"] = self.delete_unused_keys(Videos, metadata_package["video_metadata"])
                insert_stmnt = insert(Videos).values(metadata_package["video_metadata"])
                stmnt = insert_stmnt.on_conflict_do_update(index_elements=['id'], set_=metadata_package["video_metadata"])
                sess.execute(stmnt)

                # music data
                if metadata_package["music_metadata"]["id"]:
                    metadata_package["music_metadata"] = self.delete_unused_keys(Music, metadata_package["music_metadata"])
                    insert_stmnt = insert(Music).values(metadata_package["music_metadata"])
                    stmnt = insert_stmnt.on_conflict_do_update(index_elements=['id'], set_=metadata_package["music_metadata"])
                    sess.execute(stmnt)

                # author data
                if metadata_package["author_metadata"]["id"]:
                    metadata_package["author_metadata"] = self.delete_unused_keys(Authors, metadata_package["author_metadata"])
                    insert_stmnt = insert(Authors).values(metadata_package["author_metadata"])
                    stmnt = insert_stmnt.on_conflict_do_update(index_elements=['id'], set_=metadata_package["author_metadata"])
                    sess.execute(stmnt)

                # hashtag data
                if metadata_package["hashtags_metadata"]:
                    for hashtag_metadata in metadata_package["hashtags_metadata"]:
                        hashtag_metadata = self.delete_unused_keys(Hashtags, hashtag_metadata)
                        insert_stmnt = insert(Hashtags).values(hashtag_metadata)
                        stmnt = insert_stmnt.on_conflict_do_nothing(index_elements=['name'])#.on_conflict_do_update(index_elements=['name'], set_=hashtag_metadata)
                        sess.execute(stmnt)

                # save information about file
                ## video and file metadata was scraped
                if metadata_package["content_binary"] and metadata_package["file_metadata"]["filepath"]:
                    metadata_package["file_metadata"] = self.delete_unused_keys(Video_files, metadata_package["file_metadata"])
                    insert_stmnt = insert(Video_files).values(metadata_package["file_metadata"])
                    stmnt = insert_stmnt.on_conflict_do_update(index_elements=['id'], set_=metadata_package["file_metadata"])
                    sess.execute(stmnt)
                    downloaded_video = True
                ## video was not scraped, because it already existed (but we need the metadata)
                elif metadata_package["content_binary"] is None and metadata_package["file_metadata"] is not None:
                    del metadata_package["file_metadata"]["filepath"]
                    metadata_package["file_metadata"] = self.delete_unused_keys(Video_files, metadata_package["file_metadata"])
                    sess.query(Video_files).filter(Video_files.c.id == video_id).update(metadata_package["file_metadata"])
                    downloaded_video = None
                ## video was not scraped, because we already have everything
                else:
                    downloaded_video = None
                
                # logging
                ## never sets downloaded_video to false, this requires an actual deletion on the drive 
                if downloaded_video == True:
                    sess.execute(text(f"UPDATE scrape_logs SET scraped_last = '{time_now}', downloaded_video = {downloaded_video} WHERE seed_id = {video_id};"))
                else:
                    sess.execute(text(f"UPDATE scrape_logs SET scraped_last = '{time_now}' WHERE seed_id = {video_id};"))

            sess.commit()

def main():

    # specify the database connection in a separate file and import the configs
    from database_url import URL
    ## ... or specify the database connection in this file
    #URL = sqlalchemy.engine.URL.create(
    #    drivername="",
    #    username="",
    #    host="",
    #    database="",
    #    password=""
    #    )

    tt = TT_Scraper_DB(wait_time=0.8, output_files_fp="/hdd1/tt_videos", DB_URL=URL)
    tt.scrape_query("SELECT seed_id FROM scrape_logs WHERE encountered_error = 'P' AND downloaded_video is Null;")

if __name__ == "__main__":
    main()
