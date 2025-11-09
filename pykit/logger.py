from typing import Any, Optional

from wpilib import RobotController
from pykit.autolog import AutoLogInputManager, AutoLogOutputManager
from pykit.inputs.loggableds import LoggedDriverStation
from pykit.logdatareciever import LogDataReciever
from pykit.logreplaysource import LogReplaySource
from pykit.logtable import LogTable
from pykit.networktables.loggednetworkinput import LoggedNetworkInput


class Logger:
    """Manages the logging and replay of data."""

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
        """Sets the replay source for the logger."""
        cls.replaySource = replaySource

    @classmethod
    def isReplay(cls) -> bool:
        """Returns True if the logger is in replay mode."""
        return cls.replaySource is not None

    @classmethod
    def recordOutput(cls, key: str, value: Any):
        """
        Records an output value to the log table.
        This is only active when not in replay mode.
        """
        if cls.running:
            cls.outputTable.put(key, value)

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
        if cls.running:
            if cls.isReplay():
                inputs.fromLog(cls.entry, prefix)
            else:
                inputs.toLog(cls.entry, prefix)

    @classmethod
    def addDataReciever(cls, reciever: LogDataReciever):
        cls.dataRecievers.append(reciever)

    @classmethod
    def registerDashboardInput(cls, dashboardInput: LoggedNetworkInput):
        cls.dashboardInputs.append(dashboardInput)

    @classmethod
    def start(cls):
        if not cls.running:
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

            metadataTable = cls.entry.getSubTable(
                "ReplayMetadata" if cls.isReplay() else "RealMetadata"
            )

            for key, value in cls.metadata.items():
                metadataTable.put(key, value)

            RobotController.setTimeSource(cls.getTimestamp)
            cls.periodicBeforeUser()

    @classmethod
    def startReciever(cls):
        for reciever in cls.dataRecievers:
            reciever.start()

    @classmethod
    def end(cls):
        if cls.running:
            cls.running = False
            print("Logger ended")

            if cls.isReplay():
                cls.replaySource.end()

            RobotController.setTimeSource(RobotController.getFPGATime)
            for reciever in cls.dataRecievers:
                reciever.end()

    @classmethod
    def getTimestamp(cls) -> int:
        """Returns the current timestamp for logging."""
        if cls.isReplay():
            return cls.entry.getTimestamp()
        return RobotController.getFPGATime()

    @classmethod
    def periodicBeforeUser(cls):
        """Called periodically before user code to update the log table."""
        cls.cycleCount += 1
        if cls.running:
            entryUpdateStart = RobotController.getFPGATime()
            if not cls.isReplay():
                cls.entry.setTimestamp(RobotController.getFPGATime())
            else:
                if not cls.replaySource.updateTable(cls.entry):
                    print("End of replay reached")
                    cls.end()
                    raise SystemExit(0)

            dsStart = RobotController.getFPGATime()
            if cls.isReplay():
                LoggedDriverStation.loadFromTable(
                    cls.entry.getSubTable("DriverStation")
                )
            dashboardInputStart = RobotController.getFPGATime()

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
        """Called periodically after user code to finalize the log table."""
        if cls.running:
            dsStart = RobotController.getFPGATime()
            if not cls.isReplay():
                LoggedDriverStation.saveToTable(cls.entry.getSubTable("DriverStation"))
            autoLogStart = RobotController.getFPGATime()
            # TODO: AutoLogOutput periodic check and update
            AutoLogOutputManager.publish_all(cls.outputTable)
            radioLogStart = RobotController.getFPGATime()
            # TODO: RadioLogger
            radioLogEnd = RobotController.getFPGATime()
            if not cls.isReplay():
                cls.recordOutput(
                    "Logger/DriverStationMS", (autoLogStart - dsStart) / 1000.0
                )
                for logged_input in AutoLogInputManager.getInputs():
                    logged_input.toLog(
                        cls.entry.getSubTable("/"),
                        "/" + logged_input.__class__.__name__,
                    )

            cls.recordOutput(
                "Logger/AutoLogOutputMS", (radioLogStart - autoLogStart) / 1000.0
            )
            cls.recordOutput(
                "Logger/RadioLoggerMS", (radioLogEnd - radioLogStart) / 1000.0
            )
            cls.recordOutput("LoggedRobot/UserCodeMS", userCodeLength / 1000.0)
            periodicAfterLength = radioLogEnd - dsStart
            cls.recordOutput(
                "LoggedRobot/LogPeriodicMS",
                (periodicBeforeLength + periodicAfterLength) / 1000.0,
            )
            cls.recordOutput(
                "LoggedRobot/FullCycleMS",
                (periodicBeforeLength + userCodeLength + periodicAfterLength) / 1000.0,
            )

            for reciever in cls.dataRecievers:
                reciever.putTable(LogTable.clone(cls.entry))
