from wpiutil.log import DataLogReader
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
        self.reader = DataLogReader(self.filename)
        self.isValid = (
            self.reader.isValid()
            and self.reader.getExtraHeader() == wpilogconstants.extraHeader
        )
        self.entries = {}
        self.record_iterator = iter(self.reader.getRecords())

        if self.isValid:
            # Create a new iterator for the initial entry scan
            entry_scan_iterator = iter(self.reader.getRecords())
            for record in entry_scan_iterator:
                if record.isStart():
                    data = record.getStartData()
                    self.entries[data.entry] = data

    def updateTable(self, table: LogTable) -> bool:
        """
        Updates a LogTable with the next record from the log file.

        :param table: The LogTable to update.
        :return: True if the table was updated, False if the end of the log was reached.
        """
        if not self.isValid:
            return False

        try:
            record = next(self.record_iterator)
            table._timestamp = record.getTimestamp()

            if not record.isControl():
                entry_id = record.getEntry()
                if entry_id in self.entries:
                    entry = self.entries[entry_id]
                    value = None
                    if entry.type == "boolean":
                        value = record.getBoolean()
                    elif entry.type == "double":
                        value = record.getDouble()
                    elif entry.type == "string" or entry.type == "json":
                        value = record.getString()
                    elif entry.type == "int" or entry.type == "int64":
                        value = record.getInteger()
                    elif entry.type == "float":
                        value = record.getFloat()
                    else:  # raw and others
                        value = record.getData()

                    if value is not None:
                        table.put(entry.name, value)

            return True
        except StopIteration:
            self.isValid = False
            return False
