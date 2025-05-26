from pykit.logtable import LogTable


class LogReplaySource:
    def start(self):
        raise NotImplementedError("must be implemented by a subclass")

    def end(self):
        raise NotImplementedError("must be implemented by a subclass")

    def updateTable(self, _table: LogTable) -> bool:
        raise NotImplementedError("must be implemented by a subclass")
