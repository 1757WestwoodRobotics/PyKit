from ntcore import NetworkTableInstance, StringEntry
from pykit.networktables.loggednetworkvalue import LoggedNetworkValue


class LoggedNetworkString(LoggedNetworkValue[str, StringEntry]):
    """
    A loggable network value for strings.

    This class provides a convenient way to interact with string values
    on NetworkTables while ensuring they are properly logged and replayed.
    """

    def __init__(self, key, defaultValue: str = "") -> None:
        """
        Initializes a LoggedNetworkString.

        :param key: The NetworkTables key.
        :param defaultValue: The default value to use if the key is not present.
        """
        self._entry = (
            NetworkTableInstance.getDefault().getStringTopic(key).getEntry(defaultValue)
        )
        super().__init__(key, defaultValue)
