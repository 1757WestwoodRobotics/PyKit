from ntcore import (
    GenericPublisher,
    IntegerPublisher,
    NetworkTable,
    NetworkTableInstance,
)

from pykit.logdatareciever import LogDataReciever
from pykit.logtable import LogTable
from pykit.logvalue import LogValue


class NT4Publisher(LogDataReciever):
    pykitTable: NetworkTable
    lastTable: LogTable = LogTable(0)

    timestampPublisher: IntegerPublisher
    publishers: dict[str, GenericPublisher] = {}

    def __init__(self, actLikeAKit: bool = False):
        self.pykitTable = NetworkTableInstance.getDefault().getTable(
            "/AdvantageKit" if actLikeAKit else "/PyKit"
        )
        self.timestampPublisher = self.pykitTable.getIntegerTopic(
            self.timestampKey[1:]
        ).publish()

    def putTable(self, table: LogTable):
        self.timestampPublisher.set(table.getTimestamp(), table.getTimestamp())

        newMap = table.getAll(False)
        oldMap = self.lastTable.getAll(False)

        for key, newValue in newMap.items():
            if newValue == oldMap.get(key):
                continue
            key = key[1:]
            publisher = self.publishers.get(key)
            if publisher is None:
                publisher = self.pykitTable.getTopic(key).genericPublish(
                    newValue.getNT4Type()
                )
                self.publishers[key] = publisher

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
