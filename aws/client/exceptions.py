
class AsyncAWSClientError(Exception):
    """
    The base exception class for BotoCore exceptions.

    :ivar msg: The descriptive message associated with the error.
    """
    fmt = 'An unspecified error occurred'

    def __init__(self, **kwargs):
        msg = self.fmt.format(**kwargs)
        Exception.__init__(self, msg)
        self.kwargs = kwargs


class NoCredentialsError(AsyncAWSClientError):
    """
    No credentials could be found
    """
    fmt = 'Unable to locate credentials'
