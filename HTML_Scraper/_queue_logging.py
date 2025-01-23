from datetime import datetime, timedelta
import time
import sys
import statistics
import traceback
import shutil

def _logging_queue_progress(self):

    # calculate ETA
    self.iter_times.insert(0, self.ITER_TIME)
    if len(self.iter_times) > 500:
        self.iter_times.pop()
    if self.iterations % 15 == 0 and self.iterations < 2_000:
        self.mean_iter_time = statistics.mean(self.iter_times)
        self.queue_eta = str(timedelta(seconds=int((self.queue_length - self.iterations) * self.mean_iter_time)))
    elif (self.iterations) % 501 == 0:
        self.queue_eta = str(timedelta(seconds=int((self.queue_length - self.iterations) * self.mean_iter_time)))
    
    if self.total_videos > 0 or self.already_scraped_count > 0:
        self.log.info("Database Information:")
        self.log.info(f"Total Scrapes in DB: {self.already_scraped_count + self.iterations :,} / {self.total_videos :,}")
        self.log.info(f"--> minus errors: {(self.already_scraped_count + self.iterations) - (self.total_errors) :,} / {self.total_videos :,}")
        self.log.info("\n****\n")

    self.log.info(f"Current Queue: {self.iterations:,} / {self.queue_length:,}")
    self.log.info(f"Errors in a row: {self.repeated_error}\n")

    self.log.info(str(round(self.ITER_TIME, 2)) + " sec. iteration time")
    self.log.info(str(round(self.mean_iter_time, 2)) + " sec. per video (averaged)")
    self.log.info(f"ETA (current queue): {self.queue_eta}\n***\n")

    #self.log.info("Disk Information:")
    #check_disk_usage((self.already_scraped_count + self.iterations), self.mean_iter_time, self.VIDEOS_OUT_FP, stop_at_tb = 0.01)
    
    return None

def check_disk_usage(self, scraped_count, iter_time, dir, stop_at_tb = 0, only_videos_in_dir = False):
        stop_at = stop_at_tb #TB left

        total, used, free = shutil.disk_usage(dir)
        free = free * pow(10, -12) # in TB
        free -= stop_at
        used = used * pow(10, -12) # in TB
        
        self.log.info(u"%.2f" % free, "free space (in TB)")
        self.log.info(u"%.2f" % used, "used space (in TB)")

        if only_videos_in_dir:
            # how long until full
            avg_video_size = used / scraped_count
            vids_until_full = int(free / avg_video_size)
            time_until_full = (vids_until_full * iter_time) #seconds
            self.log.info(f"{int(vids_until_full):,} videos until full")
            self.log.info(str(timedelta(seconds=int(time_until_full))), "hours until full")

        self.log.info("\n")

        if float(free) < stop_at:
            self.log.info("System full")
            sys.exit(0)
