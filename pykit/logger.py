from pykit.logreplaysource import LogReplaySource
from pykit.logtable import LogTable


class Logger:
    """Manages the logging and replay of data."""

    replaySource: LogReplaySource = None
    log_table: LogTable = None

    @classmethod
    def setReplaySource(cls, replaySource: LogReplaySource):
        """Sets the replay source for the logger."""
        cls.replaySource = replaySource

    @classmethod
    def isReplay(cls) -> bool:
        """Returns True if the logger is in replay mode."""
        return cls.replaySource is not None

    @classmethod
    def init(cls, log_table: LogTable):
        """Initializes the logger with a LogTable for the current cycle."""
        cls.log_table = log_table

    @classmethod
    def recordOutput(cls, key: str, value: any):
        """
        Records an output value to the log table.
        This is only active when not in replay mode.
        """
        if not cls.isReplay():
            cls.log_table.put(key, value)

    @classmethod
    def processInputs(cls, prefix: str, inputs):
        """
        Processes an I/O object, either by logging its state or by updating it from the log.

        In normal mode, it calls 'toLog' on the inputs object to record its state.
        In replay mode, it calls 'fromLog' on the inputs object to update its state from the log.
        """
        if cls.isReplay():
            inputs.fromLog(cls.log_table, prefix)
        else:
            inputs.toLog(cls.log_table, prefix)
