from typing import Any, Optional

from wpilib import RobotController
from pykit.autolog import AutoLogInputManager, AutoLogOutputManager
from pykit.inputs.loggableds import LoggedDriverStation
from pykit.inputs.loggablesystemstats import LoggedSystemStats
from pykit.logdatareciever import LogDataReciever
from pykit.logreplaysource import LogReplaySource
from pykit.logtable import LogTable
from pykit.networktables.loggednetworkinput import LoggedNetworkInput


class Logger:
    """Manages the logging and replay of data for the robot."""

    replaySource: Optional[LogReplaySource] = None
    running: bool = False
    cycleCount: int = 0
    entry: LogTable = LogTable(0)
    outputTable: LogTable = LogTable(0)
    metadata: dict[str, str] = {}
    checkConsole: bool = True

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
    def recordOutput(cls, key: str, value: Any):
        """
        Records an output value to the log table.
        This is only active when not in replay mode.

        :param key: The key under which to record the value.
        :param value: The value to record.
        """
        if cls.running:
            cls.outputTable.put(key, value)

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
            autoLogStart = RobotController.getFPGATime()
            # Publish all auto-logged outputs
            AutoLogOutputManager.publish_all(cls.outputTable)
            autoLogEnd = RobotController.getFPGATime()
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
                "Logger/AutoLogOutputMS", (autoLogEnd - autoLogStart) / 1000.0
            )
            cls.recordOutput("LoggedRobot/UserCodeMS", userCodeLength / 1000.0)
            periodicAfterLength = autoLogEnd - dsStart
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
