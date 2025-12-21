from ntcore import NetworkTableInstance, StringEntry
from pykit.networktables.loggednetworkvalue import LoggedNetworkValue


class LoggedNetworkString(LoggedNetworkValue[str, StringEntry]):
    def __init__(self, key, defaultValue: str = "") -> None:
        self._entry = (
            NetworkTableInstance.getDefault().getStringTopic(key).getEntry(defaultValue)
        )
        super().__init__(key, defaultValue)
