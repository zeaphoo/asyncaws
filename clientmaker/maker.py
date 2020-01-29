
import sys
from loguru import logger
from clientmaker.loader import SchemaLoader
from clientmaker.model import ServiceModel

class ClientMaker(object):
    def __init__(self):
        self.init_logging()
    
    def init_logging(self):
        logger.add(sys.stdout, format="[{time}] [{level}] [{message}]", filter="my_module", level="INFO")
    
    def make(self):
        logger.info('start to make client.')
        loader = SchemaLoader()
        model_data = loader.load_service_model('s3', 'service')
        model = ServiceModel(model_data)
        logger.info(model.operation_names)
        logger.info('make process completed.')
