from wpilib import DriverStation
from wpiutil.log import DataLogReader, DataLogRecord
from pykit.logreplaysource import LogReplaySource
from pykit.wpilog import wpilogconstants
from pykit.logtable import LogTable
from pykit.logvalue import LogValue


class WPILOGReader(LogReplaySource):
    """Reads a .wpilog file and provides the data as a replay source."""

    def __init__(self, filename: str) -> None:
        """
        Constructor for WPILOGReader.

        :param filename: The path to the .wpilog file.
        """
        self.filename = filename

    def start(self):
        self.reader = DataLogReader(self.filename)
        self.isValid = (
            self.reader.isValid()
            and self.reader.getExtraHeader() == wpilogconstants.extraHeader
        )
        self.records = iter([])

        if self.isValid:
            # Create a new iterator for the initial entry scan
            self.records = iter(self.reader)
            self.entryIds = {}
            self.entryTypes = {}
            self.timestamp = None

        else:
            print("[WPILogReader] not valid")

    def updateTable(self, table: LogTable) -> bool:
        """
        Updates a LogTable with the next record from the log file.

        :param table: The LogTable to update.
        :return: True if the table was updated, False if the end of the log was reached.
        """
        if not self.isValid:
            return False

        if self.timestamp is not None:
            table.setTimestamp(self.timestamp)

        for record in self.records:
            if record.isControl():
                if record.isStart():
                    startData = record.getStartData()
                    self.entryIds[startData.entry] = startData.name
                    self.entryTypes[startData.entry] = (
                        LogValue.LoggableType.fromWPILOGType(startData.type),
                    )
                    pass
            else:
                entry = self.entryIds.get(record.getEntry())
                if entry is not None:
                    if entry == self.timestampKey:
                        firsttimestamp = self.timestamp is None
                        self.timestamp = record.getInteger()
                        if firsttimestamp:
                            table.setTimestamp(self.timestamp)

        return True
