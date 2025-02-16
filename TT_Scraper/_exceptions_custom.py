## ERROR Classes
class NoDataFromURL(Exception):
    '''URL could not provide data'''
    pass

class ItemInfoError(Exception):
    '''Some form of content exists, but does not fit standard'''
    pass

class VideoNotFoundError(Exception):
    '''No video found under video url'''
    pass

class RetryLaterError(Exception):
    '''Could not get data, retry later!'''
    pass

class OtherError(Exception):
    # use with caution
    pass

# not a real error:
class VideoIsPicture(Exception):
    '''helper error to activate scrape_picture function'''
    pass

