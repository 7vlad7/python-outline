"""
Exceptions for the Outline Wrapper
"""


class OutlineException(Exception):
    """
    Base class for all exceptions
    """
    match = ""

    def __str__(self):
        return self.match


class OutlineInvalidPort(OutlineException):
    """
    Raised when a port is invalid
    """

    match = "Invalid port number, must be between 1 and 65535"


class OutlinePortAlreadyInUse(OutlineException):
    """
    Raised when a port is already in use
    """
    match = "Port already in use"


class OutlineInvalidHostname(OutlineException):
    """
    Raised when a hostname or IP is invalid
    """
    match = "An invalid hostname or IP address was provided"


class OutlineInvalidName(OutlineException):
    """
    Raised when a name is invalid
    """
    match = "Invalid name"


class OutlineAccessKeyNotFound(OutlineException):
    """
    Raised when an access key is not found
    """
    match = "Access key not found"


class OutlineInvalidDataLimit(OutlineException):
    """
    Raised when a data limit is invalid
    """

    match = "Invalid data limit"


class OutlineErrorHostname(OutlineException):
    """
    Raised when an error occurs while changing the hostname
    """
    match = """An internal error occurred.
This could be thrown if there were network
errors while validating the hostname"""
