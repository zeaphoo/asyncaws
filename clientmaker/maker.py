
import sys
from loguru import logger
from clientmaker.loader import Loader

class ClientMaker(object):
    def __init__(self):
        self.init_logging()
    
    def init_logging(self):
        logger.add(sys.stdout, format="[{time}] [{level}] [{message}]", filter="my_module", level="INFO")
    
    def make(self):
        loader = Loader()




if __name__ == '__main__':
    cm = ClientMaker()
    cm.make()