from ntcore import BooleanEntry, NetworkTableInstance
from pykit.networktables.loggednetworkvalue import LoggedNetworkValue


class LoggedNetworkBoolean(LoggedNetworkValue[bool, BooleanEntry]):
    def __init__(self, key, defaultValue: bool = False) -> None:
        self._entry = (
            NetworkTableInstance.getDefault()
            .getBooleanTopic(key)
            .getEntry(defaultValue)
        )
        super().__init__(key, defaultValue)
