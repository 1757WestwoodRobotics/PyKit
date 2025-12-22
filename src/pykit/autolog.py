import typing
import inspect
import gc
import dataclasses

from wpiutil import wpistruct

from pykit.logtable import LogTable
from pykit.logvalue import LogValue


class _HasAutoLogInfo(typing.Protocol):
    _autolog_output_info: typing.Dict[str, typing.Any]


class AutoLogInputManager:
    """A manager class for handling automatic input loading of dataclass fields."""

    logged_classes: typing.List[typing.Any] = []

    @classmethod
    def register_class(cls, class_to_register: typing.Any):
        """
        Registers a class for automatic input loading.

        :param class_to_register: The class type to register.
        """
        cls.logged_classes.append(class_to_register)

    @classmethod
    def getInputs(cls) -> typing.List[typing.Any]:
        """
        Returns the list of registered classes for input loading.

        :return: A list of registered classes.
        """
        return cls.logged_classes


class AutoLogOutputManager:
    """A manager class for handling automatic logging of output members (fields/methods)."""

    # Stores a dictionary where keys are class types and values are lists of
    # dictionaries, each representing a decorated member.
    # Each member dictionary contains:
    #   'name': str (name of the field or method)
    #   'is_method': bool (True if it's a method, False if it's a field)
    #   'log_type': LogValue.LoggableType (the type to log as)
    #   'custom_type': str (optional custom type string)
    #   'unit': str (optional unit string)
    logged_members: typing.Dict[
        typing.Type, typing.List[typing.Dict[str, typing.Any]]
    ] = {}

    root_cache: typing.List[typing.Any] = []

    @classmethod
    def publish_all(cls, table: LogTable, root_instance=None):
        """
        Publishes all registered members of all registered class instances.

        This method scans for all instances of classes registered with `autologgable_output`
        and publishes their decorated members to the provided LogTable. It also handles
        caching of root instances to avoid redundant garbage collection scans.

        :param table: The LogTable to publish data to.
        :param root_instance: An optional list of root instances to start publishing from.
                              If None, it scans for all instances of registered classes.
        """
        # Build root instance list from cache or by scanning for registered class instances
        if root_instance is None:
            if cls.root_cache:
                root_instance = cls.root_cache
            else:
                root_instance = []
                for clS in cls.logged_members:
                    # At runtime, find all instances that exist of registered classes
                    for instance in gc.get_referrers(clS):
                        if instance.__class__ == clS:
                            root_instance.append(instance)
                cls.root_cache = root_instance

        # Publish each instance and recurse into nested autologged objects
        for instance in root_instance:
            cls.publish(instance, table)
            if (
                hasattr(instance, "_do_autolog")
                and getattr(instance, "_do_autolog")
                and hasattr(instance, "__dict__")
                and not isinstance(instance, staticmethod)
            ):
                # Recursively publish sub-members for classes marked for autolog
                cls.publish_all(table, instance.__dict__.values())

    @classmethod
    def register_member(
        cls,
        class_type: typing.Type,
        member_name: str,
        is_method: bool,
        log_type: typing.Optional[LogValue.LoggableType],
        key: str = "",
        custom_type: str = "",
        unit: typing.Optional[str] = None,
    ):
        """
        Registers a member (field or method) of a class for automatic output logging.

        :param class_type: The class to which the member belongs.
        :param member_name: The name of the member (field or method).
        :param is_method: True if the member is a method, False otherwise.
        :param log_type: The `LogValue.LoggableType` to log the member as.
        :param key: The key to use for logging. Defaults to the member name.
        :param custom_type: A custom type string for the log entry.
        :param unit: The unit string for the log entry.
        """
        if class_type not in cls.logged_members:
            cls.logged_members[class_type] = []
        cls.logged_members[class_type].append(
            {
                "name": member_name,
                "is_method": is_method,
                "log_type": log_type,
                "key": key,
                "custom_type": custom_type,
                "unit": unit,
            }
        )

    @classmethod
    def publish(cls, instance: typing.Any, table: LogTable):
        """
        Publishes the values of all registered members of an instance to a LogTable.

        :param instance: The instance whose members are to be published.
        :param table: The LogTable to publish data to.
        """
        class_type = type(instance)
        if class_type in cls.logged_members:
            for member_info in cls.logged_members[class_type]:
                member_name = member_info["name"]
                is_method = member_info["is_method"]
                log_type = member_info["log_type"]
                custom_type = member_info["custom_type"]
                unit = member_info["unit"]

                key = member_info["key"] or member_name

                # Get the value from the instance (call if method, access if field)
                value = None
                if is_method:
                    value = getattr(instance, member_name)()
                else:
                    value = getattr(instance, member_name)

                # Handle WPILib struct types specially
                if hasattr(value, "WPIStruct") or (
                    hasattr(value, "__iter__")
                    and len(value) > 0
                    and hasattr(value[0], "WPIStruct")
                ):
                    table.put(key, value)
                else:
                    # Wrap value in LogValue and override type if specified
                    log_value = LogValue(value, custom_type, unit)
                    if log_type is not None:
                        log_value.log_type = log_type
                    table.putValue(key, log_value)


def autolog_output(
    key: str,
    log_type: typing.Optional[LogValue.LoggableType] = None,
    custom_type: str = "",
    unit: typing.Optional[str] = None,
):
    """
    A decorator for methods or fields in a class to automatically log their output.

    Usage:
        @autologgable_output
        class MyComponent:
            my_value = 5

            @autolog_output("MyValue")
            def get_my_value(self):
                return self.my_value

    :param key: The key to use for logging the member's value.
    :param log_type: The `LogValue.LoggableType` to log the value as. If None, it's inferred.
    :param custom_type: A custom type string for the log entry.
    :param unit: The unit string for the log entry.
    :return: A decorator function.
    """

    def decorator(member: typing.Any):
        # This part is tricky because Python decorators for methods/fields
        # don't directly give you the class at definition time.
        # We'll store a temporary attribute and process it in a class decorator.
        if inspect.isfunction(member):
            # It's a method
            print(f"[AugoLogOutput] DEBUG: Setting up log for {key}")
            typing.cast(_HasAutoLogInfo, member)._autolog_output_info = {
                "is_method": True,
                "log_type": log_type,
                "custom_type": custom_type,
                "key": key,
                "unit": unit,
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
            typing.cast(_HasAutoLogInfo, member)._autolog_output_info = {
                "is_method": False,  # This will be true for properties too
                "log_type": log_type,
                "custom_type": custom_type,
                "key": key,
                "unit": unit,
            }
        return member

    return decorator


def autologgable_output(cls):
    """
    A class decorator that scans for methods/fields decorated with @autolog_output
    and registers them with AutoLogOutputManager.

    :param cls: The class to decorate.
    :return: The decorated class.
    """
    for name in dir(cls):
        member = getattr(cls, name)
        info = getattr(member, "_autolog_output_info", None)
        if isinstance(info, dict):
            AutoLogOutputManager.register_member(
                cls,
                name,
                bool(info.get("is_method", False)),
                typing.cast(
                    typing.Optional[LogValue.LoggableType], info.get("log_type")
                ),
                typing.cast(str, info.get("key", name)),
                typing.cast(str, info.get("custom_type", "")),
                typing.cast(str, info.get("unit", "")),
            )

    setattr(cls, "_do_autolog", True)
    return cls


def autolog(cls=None, /):
    """
    A class decorator that adds 'toLog' and 'fromLog' methods to a dataclass for automatic logging.

    The 'toLog' method serializes the dataclass fields to a LogTable.
    The 'fromLog' method deserializes the data from a LogTable into the dataclass fields.

    This decorator is designed to be used with dataclasses and supports nested dataclasses
    decorated with @autolog.

    :param cls: The class to decorate.
    :return: The decorated class or a wrapper function.
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
                # Recursively load nested autolog dataclasses
                if hasattr(value, "fromLog"):
                    value.fromLog(table, field_prefix)
                else:
                    # Load primitive types and arrays from log table
                    field_type = resolved_hints[name]
                    new_value: typing.Any = None

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
                        elif hasattr(list_type, "WPIStruct"):
                            # Unpack WPILib struct array
                            new_value = wpistruct.unpackArray(
                                list_type, table.getRaw(field_prefix, b"")
                            )
                        else:
                            print(
                                f"[AutoLog] Failed to read of type {field_type} with value {list_type}"
                            )
                    else:
                        if field_type is bool:
                            new_value = table.getBoolean(field_prefix, value)
                        elif field_type is int:
                            new_value = table.getInteger(field_prefix, value)
                        elif field_type is float:
                            new_value = table.getDouble(field_prefix, value)
                        elif field_type is str:
                            new_value = table.getString(field_prefix, value)
                        elif hasattr(field_type, "WPIStruct"):
                            # Unpack WPILib struct
                            new_value = wpistruct.unpack(
                                field_type, table.getRaw(field_prefix, b"")
                            )
                        else:
                            print(f"[AutoLog] Failed to read of type {field_type}")

                    if new_value is not None:
                        setattr(self, name, new_value)

        def registerAutologged(self) -> None:
            """Registers the class instance with the AutoLogInputManager after initialization."""
            print(f"[AutoLog] registering {self.name}")
            AutoLogInputManager.register_class(self)

        setattr(clS, "toLog", toLog)
        setattr(clS, "fromLog", fromLog)
        # https://docs.python.org/3/library/dataclasses.html#dataclasses.__post_init__
        # https://docs.python.org/3/reference/expressions.html#private-name-mangling
        setattr(cls, f"_{clS.__class__.__name__}__post_init__", registerAutologged)

        return clS

    if cls is None:
        return wrap

    return wrap(cls)
