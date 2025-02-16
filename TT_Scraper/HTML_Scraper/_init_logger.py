import logging

def _init_logger(self):
    
    # name of logger
    log = logging.getLogger("logging")
    logging.basicConfig(level=logging.INFO)

    #if not log.hasHandlers():
    # own logs handler
    handler = logging.StreamHandler()
    #formatter = logging.Formatter('%(asctime)s: %(levelname)-8s %(message)s', datefmt='%m-%d/%H:%M')
    formatter = logging.Formatter('%(levelname)-8s: %(message)s', datefmt='%m-%d/%H:%M')
    handler.setFormatter(formatter)
    log.addHandler(handler)

    # only printout handlers, not log
    log.propagate = False    
    
    return log

#log = innit_logger()
