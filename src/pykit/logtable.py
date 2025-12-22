from typing import Any, Optional, Set, cast

from wpiutil import wpistruct
from pykit.logvalue import LogValue


class LogTable:
    """
    Represents a table of loggable values for a single timestamp.
    It stores data as key-value pairs where keys are strings and values are `LogValue` objects.
    """

    prefix: str
    depth: int
    _timestamp: int
    data: dict[str, LogValue]

    def __init__(self, timestamp: int, prefix="/") -> None:
        """
        Initializes a new LogTable.

        :param timestamp: The timestamp for the log entries in this table, in microseconds.
        :param prefix: The prefix for all keys in this table.
        """
        self._timestamp = timestamp
        self.prefix = prefix
        self.depth = 0
        self.data: dict[str, LogValue] = {}

    @staticmethod
    def clone(source: "LogTable"):
        """
        Creates a shallow copy of a LogTable.

        :param source: The LogTable to clone.
        :return: A new LogTable instance with the same data.
        """
        data: dict[str, LogValue] = {}
        for item, value in source.data.items():
            data[item] = value

        newTable = LogTable(source._timestamp, source.prefix)
        newTable.data = data
        return newTable

    def getTimestamp(self) -> int:
        """
        Returns the timestamp of the log table.

        :return: The timestamp in microseconds.
        """
        return self._timestamp

    def setTimestamp(self, timestamp: int) -> None:
        """
        Sets the timestamp of the log table.

        :param timestamp: The new timestamp in microseconds.
        """
        self._timestamp = timestamp

    def writeAllowed(
        self,
        key: str,
        logType: LogValue.LoggableType,
        customType: str,
    ) -> bool:
        """
        Checks if a write operation is allowed for a given key and type.
        Prevents changing the type of an existing log entry.

        :param key: The key of the log entry.
        :param logType: The `LoggableType` of the new value.
        :param customType: The custom type string of the new value.
        :return: True if writing is allowed, False otherwise.
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
        """
        Adds the schema for a nested WPILib struct to the log table.

        :param structname: The name of the struct.
        :param schema: The schema string of the struct.
        """
        typeString = structname
        key = "/.schema/" + typeString
        if key in self.data.keys():
            return

        self.data[key] = LogValue(schema.encode(), "structschema")

    def addStructSchema(self, struct: Any, seen: Set[str]):
        """
        Adds the schema for a WPILib struct and its nested structs to the log table.

        :param struct: The struct instance.
        :param seen: A set of already processed type strings to avoid recursion loops.
        """
        # Add struct schema definition to log for replay compatibility
        typeString = "struct:" + wpistruct.getTypeName(struct.__class__)
        key = "/.schema/" + typeString
        if key in self.data.keys():
            return
        seen.add(typeString)
        schema = wpistruct.getSchema(struct.__class__)
        self.data[key] = LogValue(schema.encode(), "structschema")

        # Recursively add schemas for nested struct types
        wpistruct.forEachNested(struct.__class__, self.addStructSchemaNest)
        seen.remove(typeString)

    def put(self, key: str, value: Any, typeStr: str = "", unit: Optional[str] = None):
        """
        Puts a value into the log table, automatically handling WPILib structs and arrays.
        The value is wrapped in a `LogValue` object.

        :param key: The key for the log entry.
        :param value: The value to be logged.
        :param typeStr: An optional custom type string.
        """
        if hasattr(value, "WPIStruct"):
            # Handle WPILib struct types - serialize and add schema
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
            # Handle arrays of struct types
            self.addStructSchema(value[0], set())
            log_value = LogValue(
                wpistruct.packArray(value),
                "struct:" + wpistruct.getTypeName(value[0].__class__) + "[]",
            )
        else:
            log_value = LogValue(value, typeStr, unit)
        self.putValue(key, log_value)

    def putValue(self, key: str, log_value: LogValue):
        """
        Puts a `LogValue` object into the log table.

        :param key: The key for the log entry.
        :param log_value: The `LogValue` object to be stored.
        """
        # Handle empty array edge case - match type to previous entry to avoid type mismatch
        if isinstance(log_value.value, list) and len(log_value.value) == 0:
            currentVal = self.data.get(self.prefix + key)
            if currentVal is not None:
                log_value.log_type = currentVal.log_type
                log_value.custom_type = currentVal.custom_type
                if currentVal.custom_type.startswith("struct"):
                    # Struct logging uses raw bytes, so empty array needs empty bytes
                    log_value.value = b""
            else:
                # Don't log if no previous entry to match type against
                return
        if self.writeAllowed(key, log_value.log_type, log_value.custom_type):
            self.data[self.prefix + key] = log_value
        else:
            print(f"Failed to insert {log_value.value}")

    def get(self, key: str, defaultValue: Any) -> Any:
        """
        Gets a value from the log table.

        :param key: The key of the value to retrieve.
        :param defaultValue: The value to return if the key is not found.
        :return: The retrieved value or the default value.
        """
        if (log_value := self.data.get(self.prefix + key)) is not None:
            return log_value.value
        return defaultValue

    def getRaw(self, key: str, defaultValue: bytes) -> bytes:
        """
        Gets a raw (bytes) value from the log table.

        :param key: The key of the value to retrieve.
        :param defaultValue: The value to return if the key is not found or the type is incorrect.
        :return: The retrieved value or the default value.
        """
        if (
            log_value := self.data.get(self.prefix + key)
        ) is not None and log_value.log_type == LogValue.LoggableType.Raw:
            return cast(bytes, log_value.value)
        return defaultValue

    def getBoolean(self, key: str, defaultValue: bool) -> bool:
        """
        Gets a boolean value from the log table.

        :param key: The key of the value to retrieve.
        :param defaultValue: The value to return if the key is not found or the type is incorrect.
        :return: The retrieved value or the default value.
        """
        if (
            log_value := self.data.get(self.prefix + key)
        ) is not None and log_value.log_type == LogValue.LoggableType.Boolean:
            return cast(bool, log_value.value)
        return defaultValue

    def getInteger(self, key: str, defaultValue: int) -> int:
        """
        Gets an integer value from the log table.

        :param key: The key of the value to retrieve.
        :param defaultValue: The value to return if the key is not found or the type is incorrect.
        :return: The retrieved value or the default value.
        """
        if (
            log_value := self.data.get(self.prefix + key)
        ) is not None and log_value.log_type == LogValue.LoggableType.Integer:
            return cast(int, log_value.value)
        return defaultValue

    def getFloat(self, key: str, defaultValue: float) -> float:
        """
        Gets a float value from the log table.

        :param key: The key of the value to retrieve.
        :param defaultValue: The value to return if the key is not found or the type is incorrect.
        :return: The retrieved value or the default value.
        """
        if (
            log_value := self.data.get(self.prefix + key)
        ) is not None and log_value.log_type == LogValue.LoggableType.Float:
            return cast(float, log_value.value)
        return defaultValue

    def getDouble(self, key: str, defaultValue: float) -> float:
        """
        Gets a double value from the log table.

        :param key: The key of the value to retrieve.
        :param defaultValue: The value to return if the key is not found or the type is incorrect.
        :return: The retrieved value or the default value.
        """
        if (
            log_value := self.data.get(self.prefix + key)
        ) is not None and log_value.log_type == LogValue.LoggableType.Double:
            return cast(float, log_value.value)
        return defaultValue

    def getString(self, key: str, defaultValue: str) -> str:
        """
        Gets a string value from the log table.

        :param key: The key of the value to retrieve.
        :param defaultValue: The value to return if the key is not found or the type is incorrect.
        :return: The retrieved value or the default value.
        """
        if (
            log_value := self.data.get(self.prefix + key)
        ) is not None and log_value.log_type == LogValue.LoggableType.String:
            return cast(str, log_value.value)
        return defaultValue

    def getBooleanArray(self, key: str, defaultValue: list[bool]) -> list[bool]:
        """
        Gets a boolean array value from the log table.

        :param key: The key of the value to retrieve.
        :param defaultValue: The value to return if the key is not found or the type is incorrect.
        :return: The retrieved value or the default value.
        """
        if (
            log_value := self.data.get(self.prefix + key)
        ) is not None and log_value.log_type == LogValue.LoggableType.BooleanArray:
            return cast(list[bool], log_value.value)
        return defaultValue

    def getIntegerArray(self, key: str, defaultValue: list[int]) -> list[int]:
        """
        Gets an integer array value from the log table.

        :param key: The key of the value to retrieve.
        :param defaultValue: The value to return if the key is not found or the type is incorrect.
        :return: The retrieved value or the default value.
        """
        if (
            log_value := self.data.get(self.prefix + key)
        ) is not None and log_value.log_type == LogValue.LoggableType.IntegerArray:
            return cast(list[int], log_value.value)
        return defaultValue

    def getFloatArray(self, key: str, defaultValue: list[float]) -> list[float]:
        """
        Gets a float array value from the log table.

        :param key: The key of the value to retrieve.
        :param defaultValue: The value to return if the key is not found or the type is incorrect.
        :return: The retrieved value or the default value.
        """
        if (
            log_value := self.data.get(self.prefix + key)
        ) is not None and log_value.log_type == LogValue.LoggableType.FloatArray:
            return cast(list[float], log_value.value)
        return defaultValue

    def getDoubleArray(self, key: str, defaultValue: list[float]) -> list[float]:
        """
        Gets a double array value from the log table.

        :param key: The key of the value to retrieve.
        :param defaultValue: The value to return if the key is not found or the type is incorrect.
        :return: The retrieved value or the default value.
        """
        if (
            log_value := self.data.get(self.prefix + key)
        ) is not None and log_value.log_type == LogValue.LoggableType.DoubleArray:
            return cast(list[float], log_value.value)
        return defaultValue

    def getStringArray(self, key: str, defaultValue: list[str]) -> list[str]:
        """
        Gets a string array value from the log table.

        :param key: The key of the value to retrieve.
        :param defaultValue: The value to return if the key is not found or the type is incorrect.
        :return: The retrieved value or the default value.
        """
        if (
            log_value := self.data.get(self.prefix + key)
        ) is not None and log_value.log_type == LogValue.LoggableType.StringArray:
            return cast(list[str], log_value.value)
        return defaultValue

    def getAll(self, subtableOnly: bool = False) -> dict[str, LogValue]:
        """
        Returns all log values in the table.

        :param subtableOnly: If True, returns only the entries within the current subtable's prefix.
        :return: A dictionary of all log entries.
        """
        if not subtableOnly:
            return self.data
        return {
            key: value
            for key, value in self.data.items()
            if key.startswith(self.prefix)
        }

    def getSubTable(self, subtablePrefix: str) -> "LogTable":
        """
        Returns a new `LogTable` instance representing a subtable of the current one.
        The new table shares the same underlying data but has an extended prefix.

        :param subtablePrefix: The prefix for the subtable.
        :return: A new `LogTable` for the specified subtable.
        """
        subtable = LogTable(self.getTimestamp(), self.prefix + subtablePrefix + "/")
        subtable.data = self.data
        subtable.depth = self.depth + 1
        return subtable
