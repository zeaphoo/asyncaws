
import jmespath
import logging
import time

from .exceptions import WaiterConfigError


class WaiterModel(object):
    SUPPORTED_VERSION = 2

    def __init__(self, waiter_config):
        """
        Note that the WaiterModel takes ownership of the waiter_config.
        It may or may not mutate the waiter_config.  If this is a concern,
        it is best to make a copy of the waiter config before passing it to
        the WaiterModel.
        :type waiter_config: dict
        :param waiter_config: The loaded waiter config
            from the <service>*.waiters.json file.  This can be
            obtained from a botocore Loader object as well.
        """
        self._waiter_config = waiter_config['waiters']

        # These are part of the public API.  Changing these
        # will result in having to update the consuming code,
        # so don't change unless you really need to.
        version = waiter_config.get('version', 'unknown')
        self._verify_supported_version(version)
        self.version = version
        self.waiter_names = list(sorted(waiter_config['waiters'].keys()))

    def _verify_supported_version(self, version):
        if version != self.SUPPORTED_VERSION:
            raise Exception("Unsupported waiter version, supported version "
                           "must be: %s, but version of waiter config "
                           "is: %s" % (self.SUPPORTED_VERSION,
                                       version))

    def get_waiter(self, waiter_name):
        try:
            single_waiter_config = self._waiter_config[waiter_name]
        except KeyError:
            raise ValueError("Waiter does not exist: %s" % waiter_name)
        return SingleWaiterConfig(single_waiter_config)

class SingleWaiterConfig(object):
    """Represents the waiter configuration for a single waiter.
    A single waiter is considered the configuration for a single
    value associated with a named waiter (i.e TableExists).
    """
    def __init__(self, single_waiter_config):
        self._config = single_waiter_config

        # These attributes are part of the public API.
        self.description = single_waiter_config.get('description', '')
        # Per the spec, these three fields are required.
        self.operation = single_waiter_config['operation']
        self.delay = single_waiter_config['delay']
        self.max_attempts = single_waiter_config['maxAttempts']

    @property
    def acceptors(self):
        acceptors = []
        for acceptor_config in self._config['acceptors']:
            acceptor = AcceptorConfig(acceptor_config)
            acceptors.append(acceptor)
        return acceptors


class AcceptorConfig(object):
    def __init__(self, config):
        self.state = config['state']
        self.matcher = config['matcher']
        self.expected = config['expected']
        self.argument = config.get('argument')
        self.matcher_func = self._create_matcher_func()

    def _create_matcher_func(self):
        # An acceptor function is a callable that takes a single value.  The
        # parsed AWS response.  Note that the parsed error response is also
        # provided in the case of errors, so it's entirely possible to
        # handle all the available matcher capabilities in the future.
        # There's only three supported matchers, so for now, this is all
        # contained to a single method.  If this grows, we can expand this
        # out to separate methods or even objects.

        if self.matcher == 'path':
            return self._create_path_matcher()
        elif self.matcher == 'pathAll':
            return self._create_path_all_matcher()
        elif self.matcher == 'pathAny':
            return self._create_path_any_matcher()
        elif self.matcher == 'status':
            return self._create_status_matcher()
        elif self.matcher == 'error':
            return self._create_error_matcher()
        else:
            raise WaiterConfigError(
                error_msg="Unknown acceptor: %s" % self.matcher)

    def _create_path_matcher(self):
        expression = jmespath.compile(self.argument)
        expected = self.expected

        def acceptor_matches(response):
            if 'Error' in response:
                return
            return expression.search(response) == expected
        return acceptor_matches

    def _create_path_all_matcher(self):
        expression = jmespath.compile(self.argument)
        expected = self.expected

        def acceptor_matches(response):
            if 'Error' in response:
                return
            result = expression.search(response)
            if not isinstance(result, list) or not result:
                # pathAll matcher must result in a list.
                # Also we require at least one element in the list,
                # that is, an empty list should not result in this
                # acceptor match.
                return False
            for element in result:
                if element != expected:
                    return False
            return True
        return acceptor_matches

    def _create_path_any_matcher(self):
        expression = jmespath.compile(self.argument)
        expected = self.expected

        def acceptor_matches(response):
            if 'Error' in response:
                return
            result = expression.search(response)
            if not isinstance(result, list) or not result:
                # pathAny matcher must result in a list.
                # Also we require at least one element in the list,
                # that is, an empty list should not result in this
                # acceptor match.
                return False
            for element in result:
                if element == expected:
                    return True
            return False
        return acceptor_matches

    def _create_status_matcher(self):
        expected = self.expected

        def acceptor_matches(response):
            # We don't have any requirements on the expected incoming data
            # other than it is a dict, so we don't assume there's
            # a ResponseMetadata.HTTPStatusCode.
            status_code = response.get('ResponseMetadata', {}).get(
                'HTTPStatusCode')
            return status_code == expected
        return acceptor_matches

    def _create_error_matcher(self):
        expected = self.expected

        def acceptor_matches(response):
            # When the client encounters an error, it will normally raise
            # an exception.  However, the waiter implementation will catch
            # this exception, and instead send us the parsed error
            # response.  So response is still a dictionary, and in the case
            # of an error response will contain the "Error" and
            # "ResponseMetadata" key.
            return response.get("Error", {}).get("Code", "") == expected
        return acceptor_matches