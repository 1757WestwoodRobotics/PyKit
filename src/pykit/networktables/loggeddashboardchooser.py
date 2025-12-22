from typing import Callable, Optional, Generic, TypeVar

from wpilib import SendableChooser, SmartDashboard
from pykit.logger import Logger
from pykit.logtable import LogTable
from pykit.networktables.loggednetworkinput import LoggedNetworkInput

T = TypeVar("T")


class LoggedDashboardChooser(LoggedNetworkInput, Generic[T]):
    """
    A wrapper for `SendableChooser` that supports logging and replay.

    This class allows for creating a dashboard-configurable chooser
    whose selection can be recorded and replayed.
    """

    key: str
    selectedValue: str = ""
    previousValue: Optional[str] = None
    listener: Optional[Callable[[T], None]] = None

    sendableChooser: SendableChooser = SendableChooser()

    options: dict[str, T] = {}

    def __init__(self, key: str) -> None:
        """
        Initializes the LoggedDashboardChooser.

        :param key: The key to use for publishing the chooser to SmartDashboard.
        """
        self.key = key
        SmartDashboard.putData(key, self.sendableChooser)
        self.periodic()

        Logger.registerDashboardInput(self)

    def addOption(self, key: str, value: T):
        """
        Adds an option to the chooser.

        :param key: The name of the option shown on the dashboard.
        :param value: The value to be returned when this option is selected.
        """
        self.sendableChooser.addOption(key, key)
        self.options[key] = value

    def setDefaultOption(self, key: str, value: T):
        """
        Sets the default option for the chooser.

        :param key: The name of the default option.
        :param value: The value to be returned by default.
        """
        self.sendableChooser.setDefaultOption(key, key)
        self.options[key] = value

    def getSelected(self) -> Optional[T]:
        """
        Gets the currently selected value.

        :return: The selected value, or None if no value is selected.
        """
        assert self.selectedValue is not None
        return self.options.get(self.selectedValue)

    def periodic(self) -> None:
        """
        Updates the chooser's state. In normal mode, it reads from NetworkTables.
        In replay mode, it reads from the log.
        """
        # In normal mode, read from NetworkTables; in replay mode, read from log
        if not Logger.isReplay():
            self.selectedValue = self.sendableChooser.getSelected()

        if self.selectedValue is None:
            self.selectedValue = ""
        Logger.processInputs(self.prefix + "/SmartDashboard", self)
        if self.selectedValue != self.previousValue and self.listener is not None:
            selected = self.getSelected()
            if selected is not None:
                self.listener(selected)
        self.previousValue = self.selectedValue

    def onChange(self, callback: Callable[[T], None]) -> None:
        """
        Registers a callback to use upon value changes.

        :param callback: The function to call when the internal value has changed
        """
        self.listener = callback

    def toLog(self, table: LogTable, prefix: str) -> None:
        """
        Logs the selected value to the table.

        :param table: The log table.
        :param prefix: The prefix for the log entry.
        """
        table.put(f"{prefix}/{self.key}", self.selectedValue)

    def fromLog(self, table: LogTable, prefix: str) -> None:
        """
        Loads the selected value from the table.

        :param table: The log table.
        :param prefix: The prefix for the log entry.
        """
        self.selectedValue = table.get(f"{prefix}/{self.key}", self.selectedValue)
