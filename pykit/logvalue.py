from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


@dataclass
class LogValue:
    """Represents a value in the log table, with its type and custom type string."""

    log_type: "LogValue.LoggableType"
    custom_type: str
    value: Any

    def __init__(self, value: Any, typeStr: str = "") -> None:
        """
        Constructor for LogValue.
        Infers the loggable type from the value.
        """
        self.value = value
        self.custom_type = typeStr
        if isinstance(value, bool):
            self.log_type = LogValue.LoggableType.Boolean
        elif isinstance(value, int):
            self.log_type = LogValue.LoggableType.Integer
        elif isinstance(value, float):
            self.log_type = LogValue.LoggableType.Double
        elif isinstance(value, str):
            self.log_type = LogValue.LoggableType.String
        elif isinstance(value, bytes):
            self.log_type = LogValue.LoggableType.Raw
        elif isinstance(value, list):
            if len(value) == 0:
                self.log_type = LogValue.LoggableType.IntegerArray
            elif all(isinstance(x, bool) for x in value):
                self.log_type = LogValue.LoggableType.BooleanArray
            elif all(isinstance(x, int) for x in value):
                self.log_type = LogValue.LoggableType.IntegerArray
            elif all(isinstance(x, float) for x in value):
                self.log_type = LogValue.LoggableType.DoubleArray
            elif all(isinstance(x, str) for x in value):
                self.log_type = LogValue.LoggableType.StringArray
            else:
                raise TypeError("Unsupported list type for LogValue")
        else:
            raise TypeError(f"Unsupported type for LogValue: {type(value)}")

    @staticmethod
    def withType(log_type: "LogValue.LoggableType", data: Any) -> "LogValue":
        val = LogValue(1)
        val.log_type = log_type
        val.value = data
        return val

    class LoggableType(Enum):
        """Enum for the different types of loggable values."""

        Raw = auto()
        Boolean = auto()
        Integer = auto()
        Float = auto()
        Double = auto()
        String = auto()
        BooleanArray = auto()
        IntegerArray = auto()
        FloatArray = auto()
        DoubleArray = auto()
        StringArray = auto()

        wpilogTypes = [
            "raw",
            "boolean",
            "int64",
            "float",
            "double",
            "string",
            "boolean[]",
            "int64[]",
            "float[]",
            "double[]",
            "string[]",
        ]

        nt4Types = [
            "raw",
            "boolean",
            "int",
            "float",
            "double",
            "string",
            "boolean[]",
            "int[]",
            "float[]",
            "double[]",
            "string[]",
        ]

        def getWPILOGType(self) -> str:
            """Returns the WPILOG type string for this type."""
            return LogValue.LoggableType.wpilogTypes.value[self.value - 1]

        def getNT4Type(self) -> str:
            """Returns the NT4 type string for this type."""
            return LogValue.LoggableType.nt4Types.value[self.value - 1]

        @staticmethod
        def fromWPILOGType(typeStr: str) -> "LogValue.LoggableType":
            """Returns a LoggableType from a WPILOG type string."""
            if typeStr in LogValue.LoggableType.wpilogTypes:
                return LogValue.LoggableType(
                    LogValue.LoggableType.wpilogTypes.index(typeStr) + 1
                )

        @staticmethod
        def fromNT4Type(typeStr: str) -> "LogValue.LoggableType":
            """Returns a LoggableType from an NT4 type string."""
            if typeStr in LogValue.LoggableType.nt4Types:
                return LogValue.LoggableType(
                    LogValue.LoggableType.nt4Types.index(typeStr) + 1
                )
