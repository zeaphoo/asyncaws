
import os
import json

class PartitionModel(object):
    def __init__(self, partition_config):
        self._partition_config = partition_config
    
    @property
    def name(self):
        return self._partition_config['partitionName']
    
    def __str__(self):
        return '<Partition:{}>'.format(self.name)
    
    def __repr__(self):
        return self.__str__()

class EndpointModel(object):
    def __init__(self, endpoint_config):
        self._endpoint_config = endpoint_config
        self.partitions = [PartitionModel(pc) for pc in endpoint_config['partitions']]
    
    @classmethod
    def load(cls, data_path):
        with open(os.path.join(data_path, 'endpoints.json'), 'rb') as f:
            data = json.loads(f.read())
            return cls(data)