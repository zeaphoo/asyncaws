
class AWSClientError(Exception):
    """
    The base exception class for AWSClient exceptions.

    :ivar msg: The descriptive message associated with the error.
    """
    fmt = 'An unspecified error occurred'

    def __init__(self, **kwargs):
        msg = self.fmt.format(**kwargs)
        Exception.__init__(self, msg)
        self.kwargs = kwargs


class NoCredentialsError(AWSClientError):
    """
    No credentials could be found
    """
    fmt = 'Unable to locate credentials'
