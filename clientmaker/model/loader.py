# Copyright 2012-2015 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
# http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
"""Module for loading various model files.

This module provides the classes that are used to load models.  
This can include:

    * Service models (e.g. the model for EC2, S3, DynamoDB, etc.)
    * Service model extras which customize the service models
    * Other models associated with a service (pagination, waiters)
    * Non service-specific config (Endpoint data, retry config)


Directory Layout
================

The Loader expects a particular directory layout.  In order for any
directory specified in AWS_DATA_PATH to be considered, it must have
this structure for service models::

    <root>
      |
      |-- servicename1
      |   |-- 2012-10-25
      |       |-- service-2.json
      |-- ec2
      |   |-- 2014-01-01
      |   |   |-- paginators-1.json
      |   |   |-- service-2.json
      |   |   |-- waiters-2.json
      |   |-- 2015-03-01
      |       |-- paginators-1.json
      |       |-- service-2.json
      |       |-- waiters-2.json
      |       |-- service-2.sdk-extras.json


That is:

    * The root directory contains sub directories that are the name
      of the services.
    * Within each service directory, there's a sub directory for each
      available API version.
    * Within each API version, there are model specific files, including
      (but not limited to): service-2.json, waiters-2.json, paginators-1.json

The ``-1`` and ``-2`` suffix at the end of the model files denote which version
schema is used within the model.  Even though this information is available in
the ``version`` key within the model, this version is also part of the filename
so that code does not need to load the JSON model in order to determine which
version to use.

The ``sdk-extras`` and similar files represent extra data that needs to be
applied to the model after it is loaded. Data in these files might represent
information that doesn't quite fit in the original models, but is still needed
for the sdk. For instance, additional operation parameters might be added here
which don't represent the actual service api.
"""
import os

import json
from collections import OrderedDict
from clientmaker.exceptions import DataNotFoundError, UnknownServiceError
from loguru import logger


def deep_merge(base, extra):
    """Deeply two dictionaries, overriding existing keys in the base.

    :param base: The base dictionary which will be merged into.
    :param extra: The dictionary to merge into the base. Keys from this
        dictionary will take precedence.
    """
    for key in extra:
        # If the key represents a dict on both given dicts, merge the sub-dicts
        if key in base and isinstance(base[key], dict)\
                and isinstance(extra[key], dict):
            deep_merge(base[key], extra[key])
            continue

        # Otherwise, set the key on the base to be the value of the extra.
        base[key] = extra[key]



class SchemaLoader(object):
    _loaders = {}

    def __init__(self, data_path):
        self.data_path = data_path
        self.services = self.load_services()

    @classmethod
    def get_loader(cls, data_path):
        if data_path not in cls._loaders:
            cls._loaders[data_path] = cls(data_path)
        return cls._loaders[data_path]

    @property
    def extras_types(self):
        return self._extras_types

    def load_services(self):
        services = dict()
        possible_services = [
            d for d in os.listdir(self.data_path)
            if os.path.isdir(os.path.join(self.data_path, d))]
        for service_name in possible_services:
            full_dirname = os.path.join(self.data_path, service_name)
            api_versions = os.listdir(full_dirname)
            max_api_version = max(api_versions)
            type_names = dict()
            service_version_dirname = os.path.join(full_dirname, max_api_version)
            for d in os.listdir(service_version_dirname):
                fpath = os.path.join(service_version_dirname, d)
                if not fpath.endswith('.json'):
                    continue
                name = d.split('-')[0]
                if d.find('.sdk-extras.') > 0:
                    name = '{}.sdk-extras'.format(name)
                if name in type_names:
                    logger.error('{} already in typenames {}'.format(d, type_names))
                type_names[name] = fpath
            services[service_name] = dict(api_version = max_api_version, type_names=type_names)
        return OrderedDict(sorted(services.items(), key=lambda t: t[0]))


    def load_service_model(self, service_name, type_name):
        """Load a  service model

        This is the main method for loading aws models (e.g. a service
        model, pagination configs, waiter configs, etc.).

        :type service_name: str
        :param service_name: The name of the service (e.g ``ec2``, ``s3``).

        :type type_name: str
        :param type_name: The model type.  Valid types include, but are not
            limited to: ``service``, ``paginators``, ``waiters``.


        :raises: UnknownServiceError if there is no known service with
            the provided service_name.

        :raises: DataNotFoundError if no data could be found for the
            service_name/type_name/api_version.

        :return: The loaded data, as a python type (e.g. dict, list, etc).
        """
        data_fullpath = self.services.get(service_name, {}).get('type_names', {}).get(type_name)
        if not data_fullpath:
            raise UnknownServiceError(
                service_name=service_name,
                known_service_names=', '.join(sorted(self.services)))
        model = self.load_data(data_fullpath)

        # Load in all the extras
        if service_name == 'service':
            extras_name = 'service.sdk-extras'
            extras_fullpath = self.services.get(service_name, {}).get('type_names', {}).get(extras_name)
            extras_model = self.load_data(extras_fullpath)
            if 'merge' in extras_model:
                deep_merge(model, extras_model['merge'])

        return model

    def load_data(self, full_path):
        with open(full_path, 'rb') as fp:
            payload = fp.read().decode('utf-8')
            logger.debug("Loading JSON file: {}".format(full_path))
            return json.loads(payload, object_pairs_hook=OrderedDict)
