from ntcore import (
    GenericPublisher,
    IntegerPublisher,
    NetworkTable,
    NetworkTableInstance,
    PubSubOptions,
)

from pykit.logdatareciever import LogDataReciever
from pykit.logtable import LogTable
from pykit.logvalue import LogValue


class NT4Publisher(LogDataReciever):
    """
    A data receiver that publishes log data to NetworkTables.

    This class listens for log table updates and publishes the data
    to a specified NetworkTable, allowing for real-time monitoring.
    """

    pykitTable: NetworkTable
    lastTable: LogTable = LogTable(0)

    timestampPublisher: IntegerPublisher
    publishers: dict[str, GenericPublisher] = {}
    units: dict[str, str] = {}

    def __init__(self, actLikeAKit: bool = False):
        """
        Initializes the NT4Publisher.

        :param actLikeAKit: If True, publishes to the "/AdvantageKit" table.
                            Otherwise, publishes to the "/PyKit" table.
        """
        self.pykitTable = NetworkTableInstance.getDefault().getTable(
            "/AdvantageKit" if actLikeAKit else "/PyKit"
        )
        options = PubSubOptions()
        options.sendAll = True
        self.timestampPublisher = self.pykitTable.getIntegerTopic(
            self.timestampKey[1:]
        ).publish(options)

    def putTable(self, table: LogTable):
        """
        Publishes the contents of a LogTable to NetworkTables.

        This method compares the new table with the last one received and only
        publishes the values that have changed.

        :param table: The LogTable to publish.
        """
        self.timestampPublisher.set(table.getTimestamp(), table.getTimestamp())

        # Compare with previous table to only publish changes
        newMap = table.getAll(False)
        oldMap = self.lastTable.getAll(False)

        for key, newValue in newMap.items():
            if newValue == oldMap.get(key):
                continue
            key = key[1:]
            unit = newValue.unit
            # Create publisher for new topics
            publisher = self.publishers.get(key)
            if publisher is None:
                publisher = self.pykitTable.getTopic(key).genericPublish(
                    newValue.getNT4Type()
                )
                self.publishers[key] = publisher
                if unit is not None:
                    self.pykitTable.getTopic(key).setProperty("unit", unit)
                    self.units[key] = unit

            # Update unit if it has changed
            if unit is not None and self.units.get(key) != unit:
                self.pykitTable.getTopic(key).setProperty("unit", unit)
                self.units[key] = unit

            if unit is not None:
                print(self.pykitTable.getTopic(key).getProperties())
            match newValue.log_type:
                case LogValue.LoggableType.Raw:
                    publisher.setRaw(newValue.value, table.getTimestamp())

                case LogValue.LoggableType.Boolean:
                    publisher.setBoolean(newValue.value, table.getTimestamp())
                case LogValue.LoggableType.Integer:
                    publisher.setInteger(newValue.value, table.getTimestamp())
                case LogValue.LoggableType.Float:
                    publisher.setFloat(newValue.value, table.getTimestamp())
                case LogValue.LoggableType.Double:
                    publisher.setDouble(newValue.value, table.getTimestamp())
                case LogValue.LoggableType.String:
                    publisher.setString(newValue.value, table.getTimestamp())
                case LogValue.LoggableType.BooleanArray:
                    publisher.setBooleanArray(newValue.value, table.getTimestamp())
                case LogValue.LoggableType.IntegerArray:
                    publisher.setIntegerArray(newValue.value, table.getTimestamp())
                case LogValue.LoggableType.FloatArray:
                    publisher.setFloatArray(newValue.value, table.getTimestamp())
                case LogValue.LoggableType.DoubleArray:
                    publisher.setDoubleArray(newValue.value, table.getTimestamp())
                case LogValue.LoggableType.StringArray:
                    publisher.setStringArray(newValue.value, table.getTimestamp())
