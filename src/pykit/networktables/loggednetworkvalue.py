from typing import Generic, TypeVar, Union

from ntcore import (
    BooleanEntry,
    DoubleEntry,
    IntegerEntry,
    StringEntry,
)
from pykit.logger import Logger
from pykit.logtable import LogTable
from pykit.networktables.loggednetworkinput import LoggedNetworkInput

NTEntry = Union[
    DoubleEntry,
    BooleanEntry,
    StringEntry,
    IntegerEntry,
]
PyNTValue = Union[float, bool, str, int]

T = TypeVar("T", bound=PyNTValue)
V = TypeVar("V", bound=NTEntry)


class LoggedNetworkValue(LoggedNetworkInput, Generic[T, V]):
    """
    A generic base class for loggable NetworkTables values.

    This class provides a common framework for handling different types of
    NetworkTables entries that need to be logged and replayed.
    """

    _value: T
    _defaultValue: T
    _entry: V

    def __init__(self, key: str, defaultValue: T) -> None:
        """
        Initializes a LoggedNetworkValue.

        :param key: The NetworkTables key.
        :param defaultValue: The default value.
        """
        self._key = key
        self._value = defaultValue
        self._defaultValue = defaultValue
        Logger.registerDashboardInput(self)

        self._entry.set(defaultValue)
        self.setDefault(defaultValue)

    def __call__(self) -> T:
        """
        Allows the object to be called to retrieve its value.

        :return: The current value.
        """
        return self.value

    @property
    def value(self) -> T:
        """The current value of the network entry."""
        return self._value

    @value.setter
    def value(self, value: T) -> None:
        """
        Sets the value of the network entry.

        :param value: The new value.
        """
        self._value = value

    def setDefault(self, defaultValue: T) -> None:
        """
        Sets the default value for the network entry.

        :param defaultValue: The new default value.
        """
        self._defaultValue = defaultValue

    def toLog(self, table: LogTable, prefix: str):
        """
        Logs the current value to the log table.

        :param table: The log table.
        :param prefix: The prefix for the log entry.
        """
        table.put(f"{prefix}/{LoggedNetworkInput.removeSlash(self._key)}", self._value)

    def fromLog(self, table: LogTable, prefix: str):
        """
        Loads the value from the log table.

        :param table: The log table.
        :param prefix: The prefix for the log entry.
        """
        self._value = table.get(
            f"{prefix}/{LoggedNetworkInput.removeSlash(self._key)}",
            self._defaultValue,
        )

    def periodic(self):
        """
        Updates the value periodically. In normal mode, it reads from NetworkTables.
        In replay mode, it relies on `fromLog` to update the value.
        """
        if not Logger.isReplay():
            self._value = self._entry.get(self._defaultValue)
        Logger.processInputs(self.prefix, self)
