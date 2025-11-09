from typing import Optional, Generic, TypeVar

from wpilib import SendableChooser, SmartDashboard
from pykit.logger import Logger
from pykit.logtable import LogTable
from pykit.networktables.loggednetworkinput import LoggedNetworkInput

T = TypeVar("T")


class LoggedDashboardChooserInputs:
    def __init__(self) -> None:
        pass


class LoggedDashboardChooser(LoggedNetworkInput, Generic[T]):
    key: str
    selectedValue: str = ""

    sendableChooser: SendableChooser = SendableChooser()

    options: dict[str, T] = {}

    def __init__(self, key: str) -> None:
        self.key = key
        SmartDashboard.putData(key, self.sendableChooser)
        self.periodic()

        Logger.registerDashboardInput(self)

    def addOption(self, key: str, value: T):
        self.sendableChooser.addOption(key, key)
        self.options[key] = value

    def setDefaultOption(self, key: str, value: T):
        self.sendableChooser.setDefaultOption(key, key)
        self.options[key] = value

    def getSelected(self) -> Optional[T]:
        assert self.selectedValue is not None
        return self.options.get(self.selectedValue)

    def periodic(self):
        if not Logger.isReplay():
            self.selectedValue = self.sendableChooser.getSelected()
            if self.selectedValue is None:
                self.selectedValue = ""

        Logger.processInputs(self.prefix + "/SmartDashboard", self)

    def toLog(self, table: LogTable, prefix: str):
        table.put(f"{prefix}/{self.key}", self.selectedValue)

    def fromLog(self, table: LogTable, prefix: str):
        self.selectedValue = table.get(f"{prefix}/{self.key}", self.selectedValue)
