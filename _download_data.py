import json

def _download_data(self, metadata_batch, download_metadata = True, download_content = True):
    for metadata_package in metadata_batch:
        content_binary = metadata_package.pop("content_binary")

        # in case a video or slides where scraped:
        if content_binary and download_content:
            
            # pictures / slides
            if type(content_binary) is list:
                self.write_pictures(content_binary, metadata_package["file_metadata"]["filepath"])
            
            # mp4 video
            else:
                self.write_video(content_binary, metadata_package["file_metadata"]["filepath"])

        # save metadata
        if download_metadata:
            self.write_metadata_package(self.VIDEOS_OUT_FP, metadata_package)
        else:
            return metadata_package
    
    return None

def write_metadata_package(self, filepath_name, metadata_package):
    filepath_name = "{filepath_name}tiktok_metadata_{metadata}.json".format(filepath_name=filepath_name, metadata=metadata_package["video_metadata"]["id"])
    with open(filepath_name, "w", encoding="utf-8") as f:
        json.dump(metadata_package, f, ensure_ascii=False, indent=4)
    self.log.info(f"--> JSON saved to {filepath_name}")

def write_video(self, video_content, filepath_name):
    with open(filepath_name, 'wb') as fn:
        fn.write(video_content)

    self.log.info(f"--> MP4  saved to {filepath_name}")
    return None

def write_pictures(self, picture_content_binary_lst, filepath_name):
    for i, picture_content_binary in enumerate(picture_content_binary_lst):
        filepath_name_numerated = filepath_name.replace("X", str(i))        
        with open(filepath_name_numerated, 'wb') as f:
            f.write(picture_content_binary)
        self.log.info(f"--> JPEG saved to {filepath_name_numerated}")
