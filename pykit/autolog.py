import typing
import inspect
import dataclasses
from pykit.logtable import LogTable
from pykit.logvalue import LogValue

class AutoLogClassOutputManager:
    """
    A manager class for handling automatic logging of dataclass fields.
    """
    logged_classes = []

    @classmethod
    def register_class(cls, class_to_register: typing.Any):
        """
        Registers a class for automatic logging.

        :param class_type: The class type to register.
        """
        cls.logged_classes.append(class_to_register)


class AutoLogInputManager:
    """
    A manager class for handling automatic input loading of dataclass fields.
    """
    logged_classes = []

    @classmethod
    def register_class(cls, class_to_register: typing.Any):
        """
        Registers a class for automatic input loading.

        :param class_type: The class type to register.
        """
        cls.logged_classes.append(class_to_register)


class AutoLogInputManager:
    """
    A manager class for handling automatic input loading of dataclass fields.
    """
    logged_classes = []

    @classmethod
    def register_class(cls, class_to_register: typing.Any):
        """
        Registers a class for automatic input loading.

        :param class_type: The class type to register.
        """
        cls.logged_classes.append(class_to_register)


class AutoLogOutputManager:
    """
    A manager class for handling automatic logging of output members (fields/methods).
    """
    # Stores a dictionary where keys are class types and values are lists of
    # dictionaries, each representing a decorated member.
    # Each member dictionary contains:
    #   'name': str (name of the field or method)
    #   'is_method': bool (True if it's a method, False if it's a field)
    #   'log_type': LogValue.LoggableType (the type to log as)
    #   'custom_type': str (optional custom type string)
    logged_members: typing.Dict[typing.Type, typing.List[typing.Dict[str, typing.Any]]] = {}

    @classmethod
    def register_member(
        cls,
        class_type: typing.Type,
        member_name: str,
        is_method: bool,
        log_type: LogValue.LoggableType,
        custom_type: str = "",
    ):
        """
        Registers a member (field or method) of a class for automatic output logging.
        """
        if class_type not in cls.logged_members:
            cls.logged_members[class_type] = []
        cls.logged_members[class_type].append(
            {
                "name": member_name,
                "is_method": is_method,
                "log_type": log_type,
                "custom_type": custom_type,
            }
        )

    @classmethod
    def publish(cls, instance: typing.Any, table: LogTable, prefix: str):
        """
        Publishes the values of all registered members of an instance to a LogTable.
        """
        class_type = type(instance)
        if class_type in cls.logged_members:
            for member_info in cls.logged_members[class_type]:
                member_name = member_info["name"]
                is_method = member_info["is_method"]
                log_type = member_info["log_type"]
                custom_type = member_info["custom_type"]

                value = None
                if is_method:
                    # Assume methods are getters and take no arguments
                    value = getattr(instance, member_name)()
                else:
                    value = getattr(instance, member_name)
                
                # Construct the full key for the log table
                full_key = f"{prefix}/{member_name}" if prefix else member_name

                # Put the value into the log table with the specified type
                log_value = LogValue(value, custom_type)
                # Override the inferred log_type if explicitly provided in the decorator
                log_value.log_type = log_type
                
                if table.writeAllowed(full_key, log_value.log_type, log_value.custom_type):
                    table.data[full_key] = log_value


def autolog_output(log_type: LogValue.LoggableType, custom_type: str = ""):
    """
    A decorator for methods or fields in a class to automatically log their output.
    """

    def decorator(member):
        # This part is tricky because Python decorators for methods/fields
        # don't directly give you the class at definition time.
        # We'll store a temporary attribute and process it in a class decorator.
        if inspect.isfunction(member):
            # It's a method
            member._autolog_output_info = {
                "is_method": True,
                "log_type": log_type,
                "custom_type": custom_type,
            }
        else:
            # It's a field (this case is harder to handle directly with a decorator
            # on the field itself, usually done via a class decorator or metaclass)
            # For now, we'll assume it's a method or a property-like descriptor.
            # If it's a simple field, the class decorator approach is more robust.
            # Let's assume for now that direct field decoration will be handled
            # by a class decorator that scans for these attributes.
            # For direct field decoration, we might need a descriptor.
            # For simplicity, let's focus on methods first, or assume a class
            # decorator will pick up field annotations.
            # For now, let's make it work for methods and properties.
            member._autolog_output_info = {
                "is_method": False, # This will be true for properties too
                "log_type": log_type,
                "custom_type": custom_type,
            }
        return member

    return decorator


def autologgable_output(cls):
    """
    A class decorator that scans for methods/fields decorated with @autolog_output
    and registers them with AutoLogOutputManager.
    """
    for name in dir(cls):
        member = getattr(cls, name)
        if hasattr(member, "_autolog_output_info"):
            info = member._autolog_output_info
            AutoLogOutputManager.register_member(
                cls,
                name,
                info["is_method"],
                info["log_type"],
                info["custom_type"],
            )
    return cls


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
        AutoLogInputManager.register_class(clS)
        return clS

    if cls is None:
        return wrap

    return wrap(cls)
