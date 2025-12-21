from ntcore import DoubleEntry, NetworkTableInstance
from pykit.networktables.loggednetworkvalue import LoggedNetworkValue


class LoggedNetworkNumber(LoggedNetworkValue[float, DoubleEntry]):
    def __init__(self, key, defaultValue: float = 0.0) -> None:
        self._entry = (
            NetworkTableInstance.getDefault().getDoubleTopic(key).getEntry(defaultValue)
        )
        super().__init__(key, defaultValue)
