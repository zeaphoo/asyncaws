
import sys
from loguru import logger
from clientmaker.loader import SchemaLoader

class ClientMaker(object):
    def __init__(self):
        self.init_logging()
    
    def init_logging(self):
        logger.add(sys.stdout, format="[{time}] [{level}] [{message}]", filter="my_module", level="INFO")
    
    def make(self):
        logger.info('start to make client.')
        loader = SchemaLoader()
        loader.load_service_model('s3', 'service')
        logger.info('make process completed.')
