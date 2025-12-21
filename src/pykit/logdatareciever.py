from pykit.logtable import LogTable


class LogDataReciever:
    """An abstract base class for classes that receive and process log data."""

    timestampKey: str = "/Timestamp"

    def start(self):
        """Called when the logging process starts. Can be used for initialization."""

    def end(self):
        """Called when the logging process ends. Can be used for cleanup."""

    def putTable(self, table: LogTable):
        """
        Processes a `LogTable` instance. This method is called for each log entry.

        :param table: The `LogTable` containing the log data for a specific timestamp.
        """
