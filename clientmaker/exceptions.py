class ClientMakerError(Exception):
    """
    The base exception class for ClientMaker exceptions.

    :ivar msg: The descriptive message associated with the error.
    """
    fmt = 'An unspecified error occurred'

    def __init__(self, **kwargs):
        msg = self.fmt.format(**kwargs)
        Exception.__init__(self, msg)
        self.kwargs = kwargs

class UndefinedModelAttributeError(ClientMakerError):
    pass


class MissingServiceIdError(ClientMakerError):
    fmt = (
        "The model being used for the service {service_name} is missing the "
        "serviceId metadata property, which is required."
    )

class DataNotFoundError(ClientMakerError):
    """
    The data associated with a particular path could not be loaded.

    :ivar path: The data path that the user attempted to load.
    """
    fmt = 'Unable to load data for: {data_path}'


class UnknownServiceError(ClientMakerError):
    """Raised when trying to load data for an unknown service.

    :ivar service_name: The name of the unknown service.

    """
    fmt = (
        "Unknown service: '{service_name}'. Valid service names are: "
        "{known_service_names}")