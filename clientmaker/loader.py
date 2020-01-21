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

This module provides the classes that are used to load models used
by botocore.  This can include:

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



class JSONFileLoader(object):
    """Loader JSON files.

    This class can load the default format of models, which is a JSON file.

    """
    def exists(self, file_path):
        """Checks if the file exists.

        :type file_path: str
        :param file_path: The full path to the file to load without
            the '.json' extension.

        :return: True if file path exists, False otherwise.

        """
        return os.path.isfile(file_path + '.json')

    def load_file(self, file_path):
        """Attempt to load the file path.

        :type file_path: str
        :param file_path: The full path to the file to load without
            the '.json' extension.

        :return: The loaded data if it exists, otherwise None.

        """
        full_path = file_path + '.json'
        if not os.path.isfile(full_path):
            return

        # By default the file will be opened with locale encoding on Python 3.
        # We specify "utf8" here to ensure the correct behavior.
        with open(full_path, 'rb') as fp:
            payload = fp.read().decode('utf-8')
            logger.debug("Loading JSON file: %s", full_path)
            return json.loads(payload, object_pairs_hook=OrderedDict)


def create_loader(search_path_string=None):
    """Create a Loader class.

    This factory function creates a loader given a search string path.

    :type search_string_path: str
    :param search_string_path: The AWS_DATA_PATH value.  A string
        of data path values separated by the ``os.path.pathsep`` value,
        which is typically ``:`` on POSIX platforms and ``;`` on
        windows.

    :return: A ``Loader`` instance.

    """
    if search_path_string is None:
        return Loader()
    paths = []
    extra_paths = search_path_string.split(os.pathsep)
    for path in extra_paths:
        path = os.path.expanduser(os.path.expandvars(path))
        paths.append(path)
    return Loader(extra_search_paths=paths)


class Loader(object):
    """Find and load data models.

    This class will handle searching for and loading data models.

    The main method used here is ``load_service_model``, which is a
    convenience method over ``load_data`` and ``determine_latest_version``.

    """
    FILE_LOADER_CLASS = JSONFileLoader
    # The included models in botocore/data/ that we ship with botocore.
    BUILTIN_DATA_PATH = os.path.join(os.getcwd(), 'aws/data')
    # For convenience we automatically add ~/.aws/models to the data path.
    BUILTIN_EXTRAS_TYPES = ['sdk']

    def __init__(self, data_path=None,
                 include_default_extras=True):
        self.file_loader = self.FILE_LOADER_CLASS()
        self.data_path = data_path or self.BUILTIN_DATA_PATH

        self._extras_types = []
        if include_default_extras:
            self._extras_types.extend(self.BUILTIN_EXTRAS_TYPES)

        self._extras_processor = ExtrasProcessor()

    @property
    def extras_types(self):
        return self._extras_types

    def list_available_services(self, type_name):
        """List all known services.

        This will traverse the search path and look for all known
        services.

        :type type_name: str
        :param type_name: The type of the service (service-2,
            paginators-1, waiters-2, etc).  This is needed because
            the list of available services depends on the service
            type.  For example, the latest API version available for
            a resource-1.json file may not be the latest API version
            available for a services-2.json file.

        :return: A list of all services.  The list of services will
            be sorted.

        """
        services = set()
        for possible_path in self._potential_locations():
            # Any directory in the search path is potentially a service.
            # We'll collect any initial list of potential services,
            # but we'll then need to further process these directories
            # by searching for the corresponding type_name in each
            # potential directory.
            possible_services = [
                d for d in os.listdir(possible_path)
                if os.path.isdir(os.path.join(possible_path, d))]
            for service_name in possible_services:
                full_dirname = os.path.join(possible_path, service_name)
                api_versions = os.listdir(full_dirname)
                for api_version in api_versions:
                    full_load_path = os.path.join(full_dirname,
                                                  api_version,
                                                  type_name)
                    if self.file_loader.exists(full_load_path):
                        services.add(service_name)
                        break
        return sorted(services)

    def determine_latest_version(self, service_name, type_name):
        """Find the latest API version available for a service.

        :type service_name: str
        :param service_name: The name of the service.

        :type type_name: str
        :param type_name: The type of the service (service-2,
            paginators-1, waiters-2, etc).  This is needed because
            the latest API version available can depend on the service
            type.  For example, the latest API version available for
            a resource-1.json file may not be the latest API version
            available for a services-2.json file.

        :rtype: str
        :return: The latest API version.  If the service does not exist
            or does not have any available API data, then a
            ``DataNotFoundError`` exception will be raised.

        """
        return max(self.list_api_versions(service_name, type_name))

    def list_api_versions(self, service_name, type_name):
        """List all API versions available for a particular service type

        :type service_name: str
        :param service_name: The name of the service

        :type type_name: str
        :param type_name: The type name for the service (i.e service-2,
            paginators-1, etc.)

        :rtype: list
        :return: A list of API version strings in sorted order.

        """
        known_api_versions = set()
        for possible_path in self._potential_locations(service_name,
                                                       must_exist=True,
                                                       is_dir=True):
            for dirname in os.listdir(possible_path):
                full_path = os.path.join(possible_path, dirname, type_name)
                # Only add to the known_api_versions if the directory
                # contains a service-2, paginators-1, etc. file corresponding
                # to the type_name passed in.
                if self.file_loader.exists(full_path):
                    known_api_versions.add(dirname)
        if not known_api_versions:
            raise DataNotFoundError(data_path=service_name)
        return sorted(known_api_versions)

    def load_service_model(self, service_name, type_name, api_version=None):
        """Load a botocore service model

        This is the main method for loading botocore models (e.g. a service
        model, pagination configs, waiter configs, etc.).

        :type service_name: str
        :param service_name: The name of the service (e.g ``ec2``, ``s3``).

        :type type_name: str
        :param type_name: The model type.  Valid types include, but are not
            limited to: ``service-2``, ``paginators-1``, ``waiters-2``.

        :type api_version: str
        :param api_version: The API version to load.  If this is not
            provided, then the latest API version will be used.

        :type load_extras: bool
        :param load_extras: Whether or not to load the tool extras which
            contain additional data to be added to the model.

        :raises: UnknownServiceError if there is no known service with
            the provided service_name.

        :raises: DataNotFoundError if no data could be found for the
            service_name/type_name/api_version.

        :return: The loaded data, as a python type (e.g. dict, list, etc).
        """
        # Wrapper around the load_data.  This will calculate the path
        # to call load_data with.
        known_services = self.list_available_services(type_name)
        if service_name not in known_services:
            raise UnknownServiceError(
                service_name=service_name,
                known_service_names=', '.join(sorted(known_services)))
        if api_version is None:
            api_version = self.determine_latest_version(
                service_name, type_name)
        full_path = os.path.join(service_name, api_version, type_name)
        model = self.load_data(full_path)

        # Load in all the extras
        extras_data = self._find_extras(service_name, type_name, api_version)
        self._extras_processor.process(model, extras_data)

        return model

    def _find_extras(self, service_name, type_name, api_version):
        """Creates an iterator over all the extras data."""
        for extras_type in self.extras_types:
            extras_name = '%s.%s-extras' % (type_name, extras_type)
            full_path = os.path.join(service_name, api_version, extras_name)

            try:
                yield self.load_data(full_path)
            except DataNotFoundError:
                pass

    def load_data(self, name):
        """Load data given a data path.

        This is a low level method that will search through the various
        search paths until it's able to load a value.  This is typically
        only needed to load *non* model files (such as _endpoints and
        _retry).  If you need to load model files, you should prefer
        ``load_service_model``.

        :type name: str
        :param name: The data path, i.e ``ec2/2015-03-01/service-2``.

        :return: The loaded data.  If no data could be found then
            a DataNotFoundError is raised.

        """
        for possible_path in self._potential_locations(name):
            found = self.file_loader.load_file(possible_path)
            if found is not None:
                return found
        # We didn't find anything that matched on any path.
        raise DataNotFoundError(data_path=name)

    def _potential_locations(self, name=None, must_exist=False,
                             is_dir=False):
        # Will give an iterator over the full path of potential locations
        # according to the search path.
        for path in self.search_paths:
            if os.path.isdir(path):
                full_path = path
                if name is not None:
                    full_path = os.path.join(path, name)
                if not must_exist:
                    yield full_path
                else:
                    if is_dir and os.path.isdir(full_path):
                        yield full_path
                    elif os.path.exists(full_path):
                        yield full_path


class ExtrasProcessor(object):
    """Processes data from extras files into service models."""
    def process(self, original_model, extra_models):
        """Processes data from a list of loaded extras files into a model

        :type original_model: dict
        :param original_model: The service model to load all the extras into.

        :type extra_models: iterable of dict
        :param extra_models: A list of loaded extras models.
        """
        for extras in extra_models:
            self._process(original_model, extras)

    def _process(self, model, extra_model):
        """Process a single extras model into a service model."""
        if 'merge' in extra_model:
            deep_merge(model, extra_model['merge'])