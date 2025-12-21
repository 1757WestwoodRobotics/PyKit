from pykit.logger import Logger
from pykit.logtable import LogTable
from pykit.networktables.loggednetworkinput import LoggedNetworkInput
from ntcore import NetworkTableInstance


class LoggedNetworkNumber(LoggedNetworkInput):
    def __init__(self, key, defaultValue: float = 0.0) -> None:
        self._key = key
        self._value = defaultValue
        self.defaultValue = defaultValue
        self._entry = (
            NetworkTableInstance.getDefault().getDoubleTopic(key).getEntry(defaultValue)
        )
        Logger.registerDashboardInput(self)

        self._entry.set(defaultValue)
        self.setDefault(defaultValue)

    def __call__(self) -> float:
        return self.value

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, value: float) -> None:
        self._entry.set(value)

    def setDefault(self, defaultValue: float) -> None:
        self.defaultValue = defaultValue
        self._entry.set(self._entry.get(defaultValue))

    def toLog(self, table: LogTable, prefix: str):
        table.put(f"{prefix}/{LoggedNetworkInput.removeSlash(self._key)}", self._value)

    def fromLog(self, table: LogTable, prefix: str):
        self._value = table.get(
            f"{prefix}/{LoggedNetworkInput.removeSlash(self._key)}",
            self.defaultValue,
        )

    def periodic(self):
        if not Logger.isReplay():
            self._value = self._entry.get(self.defaultValue)
        Logger.processInputs(self.prefix, self)
