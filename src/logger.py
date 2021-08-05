import logging

def setup():

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger('root')
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
