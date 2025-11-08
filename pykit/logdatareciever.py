from pykit.logtable import LogTable


class LogDataReciever:
    timestampKey: str = "/Timestamp"

    def start(self):
        pass

    def end(self):
        pass

    def putTable(self, table: LogTable):
        pass
