from ntcore import DoubleEntry, NetworkTableInstance
from pykit.networktables.loggednetworkvalue import LoggedNetworkValue


class LoggedNetworkNumber(LoggedNetworkValue[float, DoubleEntry]):
    """
    A loggable network value for numbers (doubles).

    This class provides a convenient way to interact with numeric values
    on NetworkTables while ensuring they are properly logged and replayed.
    """

    def __init__(self, key, defaultValue: float = 0.0) -> None:
        """
        Initializes a LoggedNetworkNumber.

        :param key: The NetworkTables key.
        :param defaultValue: The default value to use if the key is not present.
        """
        self._entry = (
            NetworkTableInstance.getDefault().getDoubleTopic(key).getEntry(defaultValue)
        )
        super().__init__(key, defaultValue)
