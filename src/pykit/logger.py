from typing import Any, Optional
import sys
import threading

from wpilib import RobotController
from pykit.alertlogger import AlertLogger
from pykit.autolog import AutoLogInputManager, AutoLogOutputManager
from pykit.inputs.loggableds import LoggedDriverStation
from pykit.inputs.loggablepowerdistribution import LoggedPowerDistribution
from pykit.inputs.loggablesystemstats import LoggedSystemStats
from pykit.logdatareciever import LogDataReciever
from pykit.logreplaysource import LogReplaySource
from pykit.logtable import LogTable
from pykit.networktables.loggednetworkinput import LoggedNetworkInput


class _ConsoleRecorder:
    def __init__(self, orig):
        self.orig = orig
        self.lock = threading.Lock()
        self.buffer = ""

    def write(self, s):
        try:
            with self.lock:
                # always write through to original stream
                self.orig.write(s)
                try:
                    self.orig.flush()
                except (OSError, ValueError):
                    # I/O errors or writing to a closed stream
                    pass
                # buffer until newline then record each line
                self.buffer += s
                while "\n" in self.buffer:
                    line, self.buffer = self.buffer.split("\n", 1)
                    try:
                        # Logger may not yet be initialized when class is defined; reference at runtime
                        Logger.recordOutput("Console", line)
                    except (AttributeError, RuntimeError, ValueError):
                        # Logger may not be ready or the logging backend raised an error
                        pass
        except (OSError, ValueError, RuntimeError):
            # Locking errors, I/O errors, or value errors from stream operations
            pass

    def flush(self):
        if self.buffer:
            Logger.recordOutput("Console", self.buffer)
            self.buffer = ""
        try:
            self.orig.flush()
        except (OSError, ValueError):
            # I/O errors or writing to a closed stream
            pass


class Logger:
    """Manages the logging and replay of data for the robot."""

    replaySource: Optional[LogReplaySource] = None
    running: bool = False
    cycleCount: int = 0
    entry: LogTable = LogTable(0)
    outputTable: LogTable = LogTable(0)
    metadata: dict[str, str] = {}
    checkConsole: bool = True

    # Internal fields for console capturing
    _orig_stdout: Optional[Any] = None
    _orig_stderr: Optional[Any] = None
    _console_wrapped: bool = False
    _console_recorder_stdout: Optional[Any] = None
    _console_recorder_stderr: Optional[Any] = None

    dataRecievers: list[LogDataReciever] = []
    dashboardInputs: list[LoggedNetworkInput] = []

    @classmethod
    def setReplaySource(cls, replaySource: LogReplaySource):
        """
        Sets the replay source for the logger.

        :param replaySource: The `LogReplaySource` to use for replaying data.
        """
        cls.replaySource = replaySource

    @classmethod
    def isReplay(cls) -> bool:
        """
        Checks if the logger is currently in replay mode.

        :return: True if in replay mode, False otherwise.
        """
        return cls.replaySource is not None

    @classmethod
    def recordOutput(cls, key: str, value: Any, unit: Optional[str] = None):
        """
        Records an output value to the log table.
        This is only active when not in replay mode.

        :param key: The key under which to record the value.
        :param value: The value to record.
        """
        if cls.running:
            cls.outputTable.put(key, value, unit=unit)

    @classmethod
    def recordMetadata(cls, key: str, value: str):
        """
        Records metadata information.
        This is only active when not in replay mode.

        :param key: The key for the metadata.
        :param value: The metadata value.
        """
        if not cls.isReplay():
            cls.metadata[key] = value

    @classmethod
    def processInputs(cls, prefix: str, inputs):
        """
        Processes an I/O object, either by logging its state or by updating it from the log.

        In normal mode, it calls 'toLog' on the inputs object to record its state.
        In replay mode, it calls 'fromLog' on the inputs object to update its state from the log.

        :param prefix: The prefix for the log entries.
        :param inputs: The I/O object to process.
        """
        if cls.running:
            if cls.isReplay():
                inputs.fromLog(cls.entry, prefix)
            else:
                inputs.toLog(cls.entry, prefix)

    @classmethod
    def addDataReciever(cls, reciever: LogDataReciever):
        """
        Adds a data receiver to the logger.

        :param reciever: The `LogDataReciever` to add.
        """
        cls.dataRecievers.append(reciever)

    @classmethod
    def registerDashboardInput(cls, dashboardInput: LoggedNetworkInput):
        """
        Registers a dashboard input for periodic updates.

        :param dashboardInput: The `LoggedNetworkInput` to register.
        """
        cls.dashboardInputs.append(dashboardInput)

    @classmethod
    def start(cls):
        """
        Starts the logger. This initializes logging or replay and sets up the necessary tables.
        """
        if not cls.running:
            cls.running = True
            cls.cycleCount = 0
            print("Logger started")

            if cls.isReplay():
                rs = cls.replaySource
                if rs is not None:
                    rs.start()

            if not cls.isReplay():
                print("Logger in normal logging mode")
                cls.outputTable = cls.entry.getSubTable("RealOutputs")
            else:
                print("Logger in replay mode")
                cls.outputTable = cls.entry.getSubTable("ReplayOutputs")

            metadataTable = cls.entry.getSubTable(
                "ReplayMetadata" if cls.isReplay() else "RealMetadata"
            )

            for key, value in cls.metadata.items():
                metadataTable.put(key, value)

            # Setup console capture to record prints under "Console"
            if cls.checkConsole and not cls._console_wrapped:
                try:
                    cls._orig_stdout = sys.stdout
                    cls._orig_stderr = sys.stderr
                    cls._console_recorder_stdout = _ConsoleRecorder(cls._orig_stdout)
                    cls._console_recorder_stderr = _ConsoleRecorder(cls._orig_stderr)
                    sys.stdout = cls._console_recorder_stdout
                    sys.stderr = cls._console_recorder_stderr
                    cls._console_wrapped = True
                except (AttributeError, RuntimeError, TypeError):
                    # If sys streams are missing or recorder construction failed
                    pass

            RobotController.setTimeSource(cls.getTimestamp)
            cls.periodicBeforeUser()

    @classmethod
    def startReciever(cls):
        """Starts all registered data receivers."""
        for reciever in cls.dataRecievers:
            reciever.start()

    @classmethod
    def end(cls):
        """Stops the logger and all data receivers, and performs necessary cleanup."""
        if cls.running:
            cls.running = False
            print("Logger ended")

            # Restore console if we wrapped it
            if cls._console_wrapped:
                try:
                    if cls._orig_stdout is not None:
                        sys.stdout = cls._orig_stdout
                    if cls._orig_stderr is not None:
                        sys.stderr = cls._orig_stderr
                except (AttributeError, RuntimeError):
                    # Restoring original streams failed
                    pass
                cls._console_wrapped = False
                cls._console_recorder_stdout = None
                cls._console_recorder_stderr = None
                cls._orig_stdout = None
                cls._orig_stderr = None

            if cls.isReplay():
                rs = cls.replaySource
                if rs is not None:
                    rs.end()

            RobotController.setTimeSource(RobotController.getFPGATime)
            for reciever in cls.dataRecievers:
                reciever.end()

    @classmethod
    def getTimestamp(cls) -> int:
        """
        Returns the current timestamp for logging.
        In replay mode, it gets the timestamp from the log entry.
        In normal mode, it gets the current FPGA timestamp.

        :return: The current timestamp in microseconds.
        """
        if cls.isReplay():
            return cls.entry.getTimestamp()
        # RobotController.getFPGATime may be untyped; ensure int
        return int(RobotController.getFPGATime())

    @classmethod
    def periodicBeforeUser(cls):
        """
        Called periodically before the user's robot code.
        This method updates the log table with new data, either from the replay source
        or from the live robot hardware.
        """
        cls.cycleCount += 1
        if cls.running:
            entryUpdateStart = RobotController.getFPGATime()
            if not cls.isReplay():
                # Normal mode: set current timestamp
                cls.entry.setTimestamp(RobotController.getFPGATime())
            else:
                # Replay mode: load next timestamped data from log
                rs = cls.replaySource
                if rs is None or not rs.updateTable(cls.entry):
                    print("End of replay reached")
                    cls.end()
                    raise SystemExit(0)

            dsStart = RobotController.getFPGATime()
            # In replay mode, simulate driver station inputs from log
            if cls.isReplay():
                LoggedDriverStation.loadFromTable(
                    cls.entry.getSubTable("DriverStation")
                )
            dashboardInputStart = RobotController.getFPGATime()

            # Update dashboard inputs (choosers, etc.)
            for dashInput in cls.dashboardInputs:
                dashInput.periodic()

            dashboardInputEnd = RobotController.getFPGATime()

            cls.recordOutput(
                "Logger/EntryUpdateMS", (dsStart - entryUpdateStart) / 1000.0
            )
            if cls.isReplay():
                cls.recordOutput(
                    "Logger/DriverStationMS", (dashboardInputStart - dsStart) / 1000.0
                )
            cls.recordOutput(
                "Logger/DashboardInputsMS",
                (dashboardInputEnd - dashboardInputStart) / 1000.0,
            )

    @classmethod
    def periodicAfterUser(cls, userCodeLength: int, periodicBeforeLength: int):
        """
        Called periodically after the user's robot code.
        This method finalizes the log entry for the current cycle by recording outputs,
        performance data, and then sends the log table to all registered receivers.

        :param userCodeLength: The execution time of the user's code in microseconds.
        :param periodicBeforeLength: The execution time of the `periodicBeforeUser` method in microseconds.
        """
        if cls.running:
            dsStart = RobotController.getFPGATime()
            # In normal mode, save driver station state to log
            if not cls.isReplay():
                LoggedDriverStation.saveToTable(cls.entry.getSubTable("DriverStation"))
            systemStart = RobotController.getFPGATime()
            if not cls.isReplay():
                LoggedSystemStats.saveToTable(cls.entry.getSubTable("SystemStats"))
                LoggedPowerDistribution.getInstance().saveToTable(
                    cls.entry.getSubTable("PowerDistribution")
                )
            autoLogStart = RobotController.getFPGATime()
            # Publish all auto-logged outputs
            AutoLogOutputManager.publish_all(cls.outputTable)
            alertLogStart = RobotController.getFPGATime()
            AlertLogger.periodic(cls.outputTable)
            alertLogEnd = RobotController.getFPGATime()
            if not cls.isReplay():
                cls.recordOutput(
                    "Logger/DriverStationMS", (systemStart - dsStart) / 1000.0
                )
                cls.recordOutput(
                    "Logger/SystemStatsMS", (autoLogStart - systemStart) / 1000.0
                )
                # Log all auto-logged inputs
                for logged_input in AutoLogInputManager.getInputs():
                    logged_input.toLog(
                        cls.entry.getSubTable("/"),
                        "/" + logged_input.__class__.__name__,
                    )

            cls.recordOutput(
                "Logger/AutoLogOutputMS", (alertLogStart - autoLogStart) / 1000.0
            )
            cls.recordOutput(
                "Logger/AlertLoggerMS", (alertLogEnd - alertLogStart) / 1000.0
            )
            cls.recordOutput("LoggedRobot/UserCodeMS", userCodeLength / 1000.0)
            periodicAfterLength = alertLogEnd - dsStart
            cls.recordOutput(
                "LoggedRobot/LogPeriodicMS",
                (periodicBeforeLength + periodicAfterLength) / 1000.0,
            )
            cls.recordOutput(
                "LoggedRobot/FullCycleMS",
                (periodicBeforeLength + userCodeLength + periodicAfterLength) / 1000.0,
            )

            # Send log table to all receivers (file writer, NetworkTables, etc.)
            for reciever in cls.dataRecievers:
                reciever.putTable(LogTable.clone(cls.entry))
