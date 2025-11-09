from typing import Any, Set

from wpiutil import wpistruct
from pykit.logvalue import LogValue


class LogTable:
    """A table of loggable values for a single timestamp."""

    prefix: str
    depth: int
    _timestamp: int
    data: dict[str, LogValue]

    def __init__(self, timestamp: int, prefix="/") -> None:
        """
        Constructor for the LogTable.

        :param timestamp: The timestamp for the log entries in this table.
        :param prefix: The prefix for the log entries.
        """
        self._timestamp = timestamp
        self.prefix = prefix
        self.depth = 0
        self.data: dict[str, LogValue] = {}

    @staticmethod
    def clone(source: "LogTable"):
        data: dict[str, LogValue] = {}
        for item, value in source.data.items():
            data[item] = value

        newTable = LogTable(source._timestamp, source.prefix)
        newTable.data = data
        return newTable

    def getTimestamp(self) -> int:
        """Returns the timestamp of the log table."""
        return self._timestamp

    def setTimestamp(self, timestamp: int) -> None:
        """Sets the timestamp of the log table."""
        self._timestamp = timestamp

    def writeAllowed(
        self,
        key: str,
        logType: LogValue.LoggableType,
        customType: str,
    ) -> bool:
        """
        Checks if a write operation is allowed for a given key and type.
        Prevents changing the type of a log entry.
        """
        if (currentVal := self.data.get(self.prefix + key)) is None:
            return True
        if currentVal.log_type != logType:
            print(
                f"Failed to write {key}:\nAttempted {logType} but type is {currentVal.log_type}"
            )
            return False
        if customType != currentVal.custom_type:
            print(
                f"Failed to write {key}:\nAttempted {customType} but type is {currentVal.custom_type}"
            )
            return False
        return True

    def addStructSchemaNest(self, structname: str, schema: str):
        typeString = structname
        key = "/.schema/" + typeString
        if key in self.data.keys():
            return

        self.data[key] = LogValue(schema.encode(), "structschema")

    def addStructSchema(self, struct: Any, seen: Set[str]):
        typeString = "struct:" + wpistruct.getTypeName(struct.__class__)
        key = "/.schema/" + typeString
        if key in self.data.keys():
            return
        seen.add(typeString)
        schema = wpistruct.getSchema(struct.__class__)
        self.data[key] = LogValue(schema.encode(), "structschema")

        wpistruct.forEachNested(struct.__class__, self.addStructSchemaNest)
        seen.remove(typeString)

    def put(self, key: str, value: Any, typeStr: str = ""):
        """
        Puts a value into the log table.
        The value is wrapped in a LogValue object.
        """
        if hasattr(value, "WPIStruct"):
            # its a struct!
            self.addStructSchema(value, set())
            log_value = LogValue(
                wpistruct.pack(value),
                "struct:" + wpistruct.getTypeName(value.__class__),
            )
        elif (
            hasattr(value, "__iter__")
            and len(value) > 0
            and hasattr(value[0], "WPIStruct")
        ):
            # structured array
            self.addStructSchema(value[0], set())
            log_value = LogValue(
                wpistruct.packArray(value),
                "struct:" + wpistruct.getTypeName(value[0].__class__) + "[]",
            )
        else:
            log_value = LogValue(value, typeStr)
        self.putValue(key, log_value)

    def putValue(self, key: str, log_value: LogValue):
        if isinstance(log_value.value, list) and len(log_value.value) == 0:
            # empty array is a weird case in dynamic type python, just force the type to match
            currentVal = self.data.get(self.prefix + key)
            if currentVal is not None:
                log_value.log_type = currentVal.log_type
                log_value.custom_type = currentVal.custom_type
                if currentVal.custom_type.startswith("struct"):
                    # struct logging is raw, empty array means we need a empty bytes buffer
                    log_value.value = b""
            else:
                # in the interest of not type mismatch, don't log
                return
        if self.writeAllowed(key, log_value.log_type, log_value.custom_type):
            self.data[self.prefix + key] = log_value
        else:
            print(f"Failed to insert {log_value.value}")

    def get(self, key: str, defaultValue: Any) -> Any:
        """Gets a value from the log table."""
        if (log_value := self.data.get(self.prefix + key)) is not None:
            return log_value.value
        return defaultValue

    def getRaw(self, key: str, defaultValue: bytes) -> bytes:
        """Gets a raw value from the log table."""
        if (
            log_value := self.data.get(self.prefix + key)
        ) is not None and log_value.log_type == LogValue.LoggableType.Raw:
            return log_value.value
        return defaultValue

    def getBoolean(self, key: str, defaultValue: bool) -> bool:
        """Gets a boolean value from the log table."""
        if (
            log_value := self.data.get(self.prefix + key)
        ) is not None and log_value.log_type == LogValue.LoggableType.Boolean:
            return log_value.value
        return defaultValue

    def getInteger(self, key: str, defaultValue: int) -> int:
        """Gets an integer value from the log table."""
        if (
            log_value := self.data.get(self.prefix + key)
        ) is not None and log_value.log_type == LogValue.LoggableType.Integer:
            return log_value.value
        return defaultValue

    def getFloat(self, key: str, defaultValue: float) -> float:
        """Gets a float value from the log table."""
        if (
            log_value := self.data.get(self.prefix + key)
        ) is not None and log_value.log_type == LogValue.LoggableType.Float:
            return log_value.value
        return defaultValue

    def getDouble(self, key: str, defaultValue: float) -> float:
        """Gets a double value from the log table."""
        if (
            log_value := self.data.get(self.prefix + key)
        ) is not None and log_value.log_type == LogValue.LoggableType.Double:
            return log_value.value
        return defaultValue

    def getString(self, key: str, defaultValue: str) -> str:
        """Gets a string value from the log table."""
        if (
            log_value := self.data.get(self.prefix + key)
        ) is not None and log_value.log_type == LogValue.LoggableType.String:
            return log_value.value
        return defaultValue

    def getBooleanArray(self, key: str, defaultValue: list[bool]) -> list[bool]:
        """Gets a boolean array value from the log table."""
        if (
            log_value := self.data.get(self.prefix + key)
        ) is not None and log_value.log_type == LogValue.LoggableType.BooleanArray:
            return log_value.value
        return defaultValue

    def getIntegerArray(self, key: str, defaultValue: list[int]) -> list[int]:
        """Gets an integer array value from the log table."""
        if (
            log_value := self.data.get(self.prefix + key)
        ) is not None and log_value.log_type == LogValue.LoggableType.IntegerArray:
            return log_value.value
        return defaultValue

    def getFloatArray(self, key: str, defaultValue: list[float]) -> list[float]:
        """Gets a float array value from the log table."""
        if (
            log_value := self.data.get(self.prefix + key)
        ) is not None and log_value.log_type == LogValue.LoggableType.FloatArray:
            return log_value.value
        return defaultValue

    def getDoubleArray(self, key: str, defaultValue: list[float]) -> list[float]:
        """Gets a double array value from the log table."""
        if (
            log_value := self.data.get(self.prefix + key)
        ) is not None and log_value.log_type == LogValue.LoggableType.DoubleArray:
            return log_value.value
        return defaultValue

    def getStringArray(self, key: str, defaultValue: list[str]) -> list[str]:
        """Gets a string array value from the log table."""
        if (
            log_value := self.data.get(self.prefix + key)
        ) is not None and log_value.log_type == LogValue.LoggableType.StringArray:
            return log_value.value
        return defaultValue

    def getAll(self, subtableOnly: bool = False) -> dict[str, LogValue]:
        """Returns all log values in the table."""
        if not subtableOnly:
            return self.data
        return {
            key: value
            for key, value in self.data.items()
            if key.startswith(self.prefix)
        }

    def getSubTable(self, subtablePrefix: str) -> "LogTable":
        """
        Returns a subtable containing only entries with the given prefix.

        :param subtablePrefix: The prefix to filter entries by.
        :return: A new LogTable containing only the filtered entries.
        """
        subtable = LogTable(self.getTimestamp(), self.prefix + subtablePrefix + "/")
        subtable.data = self.data
        subtable.depth = self.depth + 1
        return subtable
