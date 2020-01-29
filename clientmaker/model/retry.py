
import os
import json

class RetryDefinition(object):
    def __init__(self, name, definition_config):
        self.name = name
        self._definition_config = definition_config
    
    def __str__(self):
        return '<RetryDefinition:{}>'.format(self.name)
    
    def __repr__(self):
        return self.__str__()

class SingleRetryModel(object):
    def __init__(self, name, retry_config):
        self.name = name
        self._retry_config = retry_config

class RetryModel(object):
    def __init__(self, retry_config):
        self._retry_config = retry_config
        self.definitions = [RetryDefinition(k,v) for k,v in retry_config['definitions'].items()]
        self.retries = [SingleRetryModel(k, v) for k,v in retry_config['retry'].items()]
    
    @classmethod
    def load(cls, data_path):
        with open(os.path.join(data_path, '_retry.json'), 'rb') as f:
            data = json.loads(f.read())
            return cls(data)