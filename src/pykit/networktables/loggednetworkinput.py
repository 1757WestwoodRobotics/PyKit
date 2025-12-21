class LoggedNetworkInput:
    """
    A base class for handling network inputs that can be logged and replayed.
    This class provides a common interface for periodic updates and key management.
    """

    prefix: str = "NetworkInputs"

    def __init__(self) -> None:
        """Initializes the LoggedNetworkInput."""

    def periodic(self):
        """
        A method called periodically to update the input's value.
        Subclasses should override this to implement their specific logic.
        """

    @staticmethod
    def removeSlash(key: str):
        """
        Removes a leading slash from a key if it exists.

        :param key: The key string.
        :return: The key without a leading slash.
        """
        if key.startswith("/"):
            return key[1:]
        return key
