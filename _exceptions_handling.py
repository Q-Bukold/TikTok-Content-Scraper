import traceback

def _exception_handler(self, video_id, error_code, exception_name):
    self.repeated_error += 1
    self.total_errors += 1

    self.log.warning(f"Handling Error: {exception_name}")

    self.log.debug("\n"+10*"-")
    self.log.debug(f"https://www.tiktok.com/@tiktok/video/{video_id}")
    self.log.debug(10*"-")
    self.log.debug(traceback.format_exc())
    self.log.debug(10*"-")
    
    # error package
    metadata_package = dict()
    metadata_package["video_metadata"] = dict()
    metadata_package["video_metadata"]["id"] = video_id
    metadata_package["error_code"] = error_code
    metadata_package["exception"] = exception_name
    metadata_package["video_content_binary"] = None

    return metadata_package