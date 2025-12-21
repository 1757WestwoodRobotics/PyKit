from ntcore import BooleanEntry, NetworkTableInstance
from pykit.networktables.loggednetworkvalue import LoggedNetworkValue


class LoggedNetworkBoolean(LoggedNetworkValue[bool, BooleanEntry]):
    """
    A loggable network value for booleans.

    This class provides a convenient way to interact with boolean values
    on NetworkTables while ensuring they are properly logged and replayed.
    """

    def __init__(self, key, defaultValue: bool = False) -> None:
        """
        Initializes a LoggedNetworkBoolean.

        :param key: The NetworkTables key.
        :param defaultValue: The default value to use if the key is not present.
        """
        self._entry = (
            NetworkTableInstance.getDefault()
            .getBooleanTopic(key)
            .getEntry(defaultValue)
        )
        super().__init__(key, defaultValue)
