import wpiutil.log
from pykit.logtable import LogTable
from pykit.logvalue import LogValue


class WPILOGWriter:
    """Writes a LogTable to a .wpilog file."""

    def __init__(self, filename: str | None = None, extra_header: str = ""):
        """
        Constructor for WPILOGWriter.

        :param filename: The path to the .wpilog file.
        :param extra_header: An extra header to write to the log file.
        """
        if filename is None:
            filename = "robotlog.wpilog"
        self.log = wpiutil.log.DataLog(dir=filename, extra_header=extra_header)
        self.entries = {}

    def write(self, table: LogTable):
        """
        Writes the contents of a LogTable to the log file.

        :param table: The LogTable to write.
        """
        for key, log_value in table.data.items():
            if key not in self.entries:
                entry_type = log_value.log_type.getWPILOGType()
                if log_value.custom_type:
                    entry_type += ":" + log_value.custom_type
                self.entries[key] = wpiutil.log.DataLogEntry(self.log, key, entry_type)

            entry = self.entries[key]
            value = log_value.value
            timestamp = table._timestamp

            if log_value.log_type == LogValue.LoggableType.Boolean:
                self.log.appendBoolean(entry, value, timestamp)
            elif log_value.log_type == LogValue.LoggableType.Integer:
                self.log.appendInteger(entry, value, timestamp)
            elif log_value.log_type == LogValue.LoggableType.Float:
                self.log.appendFloat(entry, value, timestamp)
            elif log_value.log_type == LogValue.LoggableType.Double:
                self.log.appendDouble(entry, value, timestamp)
            elif log_value.log_type == LogValue.LoggableType.String:
                self.log.appendString(entry, value, timestamp)
            elif log_value.log_type == LogValue.LoggableType.BooleanArray:
                self.log.appendBooleanArray(entry, value, timestamp)
            elif log_value.log_type == LogValue.LoggableType.IntegerArray:
                self.log.appendIntegerArray(entry, value, timestamp)
            elif log_value.log_type == LogValue.LoggableType.FloatArray:
                self.log.appendFloatArray(entry, value, timestamp)
            elif log_value.log_type == LogValue.LoggableType.DoubleArray:
                self.log.appendDoubleArray(entry, value, timestamp)
            elif log_value.log_type == LogValue.LoggableType.StringArray:
                self.log.appendStringArray(entry, value, timestamp)
            elif log_value.log_type == LogValue.LoggableType.Raw:
                self.log.appendRaw(entry, value, timestamp)

    def finish(self):
        """Finishes writing to the log file."""
        self.log.finish()
