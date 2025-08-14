import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)-1s;%(levelname)s:%(name)-15s: %(message)s',
    datefmt='%m-%d/%H:%M',
    force=True  # Important for Jupyter!
)

logger = logging.getLogger('TTCS')

#formatter = logging.Formatter('%(asctime)-1s;%(levelname)s:%(name)-8s: %(message)s', datefmt='%m-%d/%H:%M')
#stream_handler = logging.StreamHandler()
#stream_handler.setFormatter(formatter)
#logger.addHandler(stream_handler)

#filename = os.path.join(os.path.dirname(progress_file_fn), "TT_Content_Scraper.log")
#fileHandler = logging.FileHandler(filename)
#fileHandler.setFormatter(formatter)
#stream_handler.setLevel(logging.INFO)
#logger.addHandler(fileHandler)
    
