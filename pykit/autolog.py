import typing
import inspect
import dataclasses
from pykit.logtable import LogTable


def autolog(cls=None, /):
    """
    A class decorator that adds 'toLog' and 'fromLog' methods to a dataclass for automatic logging.

    The 'toLog' method serializes the dataclass fields to a LogTable.
    The 'fromLog' method deserializes the data from a LogTable into the dataclass fields.

    This decorator is designed to be used with dataclasses and supports nested dataclasses
    decorated with @autolog.
    """

    def wrap(clS):
        resolved_hints = typing.get_type_hints(clS)
        field_names = [field.name for field in dataclasses.fields(clS)]

        def toLog(self, table: LogTable, prefix: str):
            """
            Recursively logs the fields of the dataclass to a LogTable.

            :param table: The LogTable instance to write to.
            :param prefix: The prefix for the log entries.
            """
            for name in field_names:
                value = getattr(self, name)
                field_prefix = f"{prefix}/{name}"
                if hasattr(value, "toLog"):
                    value.toLog(table, field_prefix)
                else:
                    table.put(field_prefix, value)

        def fromLog(self, table: LogTable, prefix: str):
            """
            Recursively reads the fields of the dataclass from a LogTable.

            :param table: The LogTable instance to read from.
            :param prefix: The prefix for the log entries.
            """
            for name in field_names:
                field_prefix = f"{prefix}/{name}"

                value = getattr(self, name)
                if hasattr(value, "fromLog"):
                    value.fromLog(table, field_prefix)
                else:
                    field_type = resolved_hints[name]
                    new_value = None

                    origin = typing.get_origin(field_type)
                    if origin is list:
                        list_type = typing.get_args(field_type)[0]
                        if list_type is bool:
                            new_value = table.getBooleanArray(field_prefix, value)
                        elif list_type is int:
                            new_value = table.getIntegerArray(field_prefix, value)
                        elif list_type is float:
                            new_value = table.getDoubleArray(field_prefix, value)
                        elif list_type is str:
                            new_value = table.getStringArray(field_prefix, value)
                    else:
                        if field_type is bool:
                            new_value = table.getBoolean(field_prefix, value)
                        elif field_type is int:
                            new_value = table.getInteger(field_prefix, value)
                        elif field_type is float:
                            new_value = table.getDouble(field_prefix, value)
                        elif field_type is str:
                            new_value = table.getString(field_prefix, value)

                    if new_value is not None:
                        setattr(self, name, new_value)

        setattr(clS, "toLog", toLog)
        setattr(clS, "fromLog", fromLog)
        return clS

    if cls is None:
        return wrap

    return wrap(cls)
