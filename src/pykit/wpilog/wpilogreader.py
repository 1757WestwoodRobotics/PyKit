from typing import Iterator, TypeVar

from wpiutil.log import DataLogReader, DataLogRecord

from pykit.logreplaysource import LogReplaySource
from pykit.logtable import LogTable
from pykit.logvalue import LogValue

T = TypeVar("T")


def safeNext(val: Iterator[T]) -> None | T:
    """
    Safely gets the next item from an iterator, returning None if the iterator is exhausted.

    :param val: The iterator.
    :return: The next item or None.
    """
    try:
        return next(val)
    except StopIteration:
        return None


class WPILOGReader(LogReplaySource):
    """
    Reads a `.wpilog` file and provides the data as a replay source for the logger.
    """

    timestamp: int | None

    def __init__(self, filename: str) -> None:
        """
        Initializes the WPILOGReader.

        :param filename: The path to the `.wpilog` file.
        """
        self.filename = filename
        # Predeclare records to satisfy typing before start() initializes it
        self.records: Iterator[DataLogRecord] = iter(())

    def start(self) -> None:
        """
        Initializes the reader by opening the log file and preparing to read records.
        """
        self.reader = DataLogReader(self.filename)
        self.isValid = (
            self.reader.isValid()
            # and self.reader.getExtraHeader() == wpilogconstants.extraHeader
        )
        print(self.reader.isValid())
        print(self.reader.getExtraHeader())
        self.records = iter(())

        if self.isValid:
            # Create a new iterator for the initial entry scan
            self.records = iter(self.reader)
            self.entryIds: dict[int, str] = {}
            self.entryTypes: dict[int, LogValue.LoggableType] = {}
            self.timestamp = None
            self.entryCustomTypes: dict[int, str] = {}

        else:
            print("[WPILogReader] not valid")

    def updateTable(self, table: LogTable) -> bool:
        """
        Updates a LogTable with the next record from the log file.

        This method iterates through the log records, populating the provided
        `LogTable` with data corresponding to a single timestamp.

        :param table: The `LogTable` to update.
        :return: True if the table was updated and there may be more data,
                 False if the end of the log was reached.
        """
        if not self.isValid:
            return False

        if self.timestamp is not None:
            table.setTimestamp(self.timestamp)

        keepLogging = False
        while (record := safeNext(self.records)) is not None:
            if record.isControl():
                if record.isStart():
                    startData = record.getStartData()
                    self.entryIds[startData.entry] = startData.name
                    typeStr = startData.type
                    self.entryTypes[startData.entry] = (
                        LogValue.LoggableType.fromWPILOGType(typeStr)
                    )
                    if typeStr.startswith("struct:") or typeStr == "structschema":
                        self.entryCustomTypes[startData.entry] = typeStr
            else:
                entry = self.entryIds.get(record.getEntry())
                if entry is not None:
                    if entry == self.timestampKey:
                        firsttimestamp = self.timestamp is None
                        self.timestamp = record.getInteger()
                        if firsttimestamp:
                            assert self.timestamp is not None
                            table.setTimestamp(self.timestamp)
                        else:
                            keepLogging = True  # we still have a timestamp, just need to wait until next iter
                            break
                    elif (
                        self.timestamp is not None
                        and record.getTimestamp() == self.timestamp
                    ):
                        entry = entry[1:]
                        if entry.startswith("ReplayOutputs"):
                            continue
                        customType = self.entryCustomTypes.get(record.getEntry())
                        entryType = self.entryTypes.get(record.getEntry())
                        if customType is None:
                            customType = ""
                        match entryType:
                            case LogValue.LoggableType.Raw:
                                table.putValue(
                                    entry,
                                    LogValue.withType(
                                        entryType, record.getRaw(), customType
                                    ),
                                )
                            case LogValue.LoggableType.Boolean:
                                table.putValue(
                                    entry,
                                    LogValue.withType(
                                        entryType, record.getBoolean(), customType
                                    ),
                                )
                            case LogValue.LoggableType.Integer:
                                table.putValue(
                                    entry,
                                    LogValue.withType(
                                        entryType, record.getInteger(), customType
                                    ),
                                )
                            case LogValue.LoggableType.Float:
                                table.putValue(
                                    entry,
                                    LogValue.withType(
                                        entryType, record.getFloat(), customType
                                    ),
                                )
                            case LogValue.LoggableType.Double:
                                table.putValue(
                                    entry,
                                    LogValue.withType(
                                        entryType, record.getDouble(), customType
                                    ),
                                )
                            case LogValue.LoggableType.String:
                                table.putValue(
                                    entry,
                                    LogValue.withType(
                                        entryType, record.getString(), customType
                                    ),
                                )
                            case LogValue.LoggableType.BooleanArray:
                                table.putValue(
                                    entry,
                                    LogValue.withType(
                                        entryType, record.getBooleanArray(), customType
                                    ),
                                )
                            case LogValue.LoggableType.IntegerArray:
                                table.putValue(
                                    entry,
                                    LogValue.withType(
                                        entryType, record.getIntegerArray(), customType
                                    ),
                                )
                            case LogValue.LoggableType.FloatArray:
                                table.putValue(
                                    entry,
                                    LogValue.withType(
                                        entryType, record.getFloatArray(), customType
                                    ),
                                )
                            case LogValue.LoggableType.DoubleArray:
                                table.putValue(
                                    entry,
                                    LogValue.withType(
                                        entryType, record.getDoubleArray(), customType
                                    ),
                                )
                            case LogValue.LoggableType.StringArray:
                                table.putValue(
                                    entry,
                                    LogValue.withType(
                                        entryType, record.getStringArray(), customType
                                    ),
                                )

        return keepLogging
