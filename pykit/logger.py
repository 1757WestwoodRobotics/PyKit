from typing import Optional

from wpilib import RobotController
from pykit.logreplaysource import LogReplaySource
from pykit.logtable import LogTable


class Logger:
    """Manages the logging and replay of data."""

    replaySource: Optional[LogReplaySource] = None
    running: bool = False
    cycleCount: int = 0
    entry: LogTable = LogTable(0)
    outputTable: LogTable = LogTable(0)
    metadata: dict[str, str] = {}
    checkConsole: bool = True

    @classmethod
    def setReplaySource(cls, replaySource: LogReplaySource):
        """Sets the replay source for the logger."""
        cls.replaySource = replaySource

    @classmethod
    def isReplay(cls) -> bool:
        """Returns True if the logger is in replay mode."""
        return cls.replaySource is not None

    @classmethod
    def recordOutput(cls, key: str, value: any):
        """
        Records an output value to the log table.
        This is only active when not in replay mode.
        """
        if not cls.isReplay():
            cls.log_table.put(key, value)

    @classmethod
    def recordMetadata(cls, key: str, value: str):
        """
        Records metadata information.
        This is only active when not in replay mode.
        """
        if not cls.isReplay():
            cls.metadata[key] = value

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

    @classmethod
    def start(cls):
        if !cls.running:
            cls.running = True
            cls.cycleCount = 0
            print("Logger started")

            if cls.isReplay():
                cls.replaySource.start()


            if not cls.isReplay():
                print("Logger in normal logging mode")
                cls.outputTable = cls.entry.getSubTable("RealOutputs")
            else:
                print("Logger in replay mode")
                cls.outputTable = cls.entry.getSubTable("ReplayOutputs")

            metadataTable = cls.entry.getSubTable("ReplayMetadata" if cls.isReplay() else "RealMetadata")

            for key, value in cls.metadata.items():
                metadataTable.put(key, value)

            RobotController.setTimeSource(cls.getTimestamp)
            cls.periodicBeforeUser()

    @classmethod
    def end(cls):
        if cls.running:
            cls.running = False
            print("Logger ended")

            if cls.isReplay():
                cls.replaySource.end()

            RobotController.setTimeSource(RobotController.getFPGATime)

    @classmethod
    def getTimestamp(cls) -> int:
        """Returns the current timestamp for logging."""
        if cls.isReplay():
            return cls.replaySource.getCurrentTimestamp()
        else:
            return RobotController.getFPGATime()

    @classmethod
    def periodicBeforeUser(cls):
        """Called periodically before user code to update the log table."""
        cls.cycleCount += 1
        if cls.running:
            entryUpdateStart = RobotController.getFPGATime()
            if !cls.isReplay():
                cls.entry.setTimestamp(RobotController.getFPGATime())
            else:
                if !cls.replaySource.updateTable(cls.entry):
                    print("End of replay reached")
                    cls.end()
                    exit()
                    return
