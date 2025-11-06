from pykit.logtable import LogTable


class LogReplaySource:
    timestampKey: str = "/Timestamp"

    def start(self):
        raise NotImplementedError("must be implemented by a subclass")

    def end(self):
        pass

    def updateTable(self, _table: LogTable) -> bool:
        raise NotImplementedError("must be implemented by a subclass")
