
import sys
from loguru import logger
from clientmaker.loader import SchemaLoader
from clientmaker.model import ServiceModel
from clientmaker.waiter import WaiterModel
from clientmaker.paginator import PaginatorModel

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
        model_data = loader.load_service_model('s3', 'waiters')
        model = WaiterModel(model_data)
        logger.info(model.waiter_names)
        model_data = loader.load_service_model('s3', 'paginators')
        model = PaginatorModel(model_data)
        logger.info(model.pagination_names)
        logger.info('make process completed.')
