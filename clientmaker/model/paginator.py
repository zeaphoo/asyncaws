
class PaginatorModel(object):
    def __init__(self, paginator_config):
        self._paginator_config = paginator_config['pagination']
        self.pagination_names = list(sorted(paginator_config['pagination'].keys()))

    def get_paginator(self, operation_name):
        try:
            single_paginator_config = self._paginator_config[operation_name]
        except KeyError:
            raise ValueError("Paginator for operation does not exist: %s"
                             % operation_name)
        return single_paginator_config