from pykit.logtable import LogTable


class LogReplaySource:
    """An abstract base class for providing log data for replay."""

    timestampKey: str = "/Timestamp"

    def start(self):
        """
        Initializes the replay source.
        This method should be implemented by subclasses to prepare for data replay.
        """
        raise NotImplementedError("must be implemented by a subclass")

    def end(self):
        """
        Cleans up resources used by the replay source.
        This method can be overridden by subclasses for cleanup tasks.
        """

    def updateTable(self, _table: LogTable) -> bool:
        """
        Updates the provided `LogTable` with the next set of data from the replay source.

        :param _table: The `LogTable` to populate with new data.
        :return: True if the table was successfully updated, False if the end of the replay is reached.
        """
        raise NotImplementedError("must be implemented by a subclass")
