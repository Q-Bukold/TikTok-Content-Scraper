import json

def _download_data(self, metadata_batch, download_metadata = True, download_content = True):
    for metadata_package in metadata_batch:
        content_binary = metadata_package.pop("content_binary")

        # in case a video or slides where scraped:
        if content_binary and download_content:
            
            # pictures / slides
            if content_binary["type"] == "slide":
                self.write_pictures(content_binary["slide_pictures"], metadata_package["file_metadata"]["filepath"])
                self.write_slide_audio(content_binary["slide_audio"], metadata_package["file_metadata"]["filepath"])
            
            # videos
            elif content_binary["type"] == "video":
                self.write_video(content_binary["mp4_binary"], metadata_package["file_metadata"]["filepath"])

        # save metadata
        if download_metadata:
            self.write_metadata_package(metadata_package["file_metadata"]["filepath"], metadata_package)
        else:
            return metadata_package
    
    return None

def write_metadata_package(self, filepath, metadata_package):
    filename = filepath.replace("*", "metadata.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(metadata_package, f, ensure_ascii=False, indent=4)
    self.log.info(f"--> JSON saved to {filename}")

def write_video(self, video_content, filepath):
    filename = filepath.replace("*", "video.mp4")
    with open(filename, 'wb') as fn:
        fn.write(video_content)
    self.log.info(f"--> MP4  saved to {filename}")
    return None

def write_pictures(self, slide_pictures, filepath):
    for i, picture in enumerate(slide_pictures):
        filename = filepath.replace("*", f"slide{str(i)}.jpeg")
        with open(filename, 'wb') as f:
            f.write(picture)
        self.log.info(f"--> JPEG saved to {filename}")

def write_slide_audio(self, slide_audio, filepath):
    filename = filepath.replace("*", "slide_audio.mp3")
    if slide_audio:
        with open(filename, "wb") as f:
            f.write(slide_audio)
        self.log.info(f"--> MP3 saved to {filename}")