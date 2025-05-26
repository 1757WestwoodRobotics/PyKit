from enum import Enum, auto
import hal
from ntcore import NetworkTableInstance
from wpilib import (
    DSControlWord,
    DriverStation,
    IterativeRobotBase,
    LiveWindow,
    RobotController,
    Notifier,
    SmartDashboard,
    Watchdog,
)
from pykit.logger import Logger
from pykit.logtable import LogTable
from pykit.wpilog.wpilogwriter import WPILOGWriter
from pykit.wpilog.wpilogreader import WPILOGReader
from pykit.inputs.loggableds import DSIO
from pykit.autolog import autolog
import os
from dataclasses import dataclass


@autolog
@dataclass
class RobotIO:
    """A dataclass for holding robot I/O data."""

    voltage: float = 0.0


class LoggedRobot(IterativeRobotBase):
    """A robot base class that provides logging and replay functionality."""

    default_period = 0.02  # seconds

    class Mode(Enum):
        """Enum for the different robot modes."""

        none = auto()
        disabled = auto()
        autonomous = auto()
        teleop = auto()
        test = auto()

    def printOverrunMessage(self):
        """Prints a message when the main loop overruns."""
        print("Loop overrun detected!")

    def __init__(self):
        """
        Constructor for the LoggedRobot.
        Initializes the robot, sets up the logger, and creates I/O objects.
        """
        IterativeRobotBase.__init__(self, LoggedRobot.default_period)
        self.useTiming = True
        self._nextCycleUs = 0
        self._periodUs = int(self.getPeriod() * 1000000)

        self.notifier = hal.initializeNotifier()[0]
        self.watchdog = Watchdog(LoggedRobot.default_period, self.printOverrunMessage)
        self.last_mode = LoggedRobot.Mode.none
        self.word = DSControlWord()

        if not Logger.isReplay():
            self.writer = WPILOGWriter()

        self.io = RobotIO()
        self.ds_io = DSIO()

    def endCompetition(self) -> None:
        """Called at the end of the competition to clean up resources."""
        if not Logger.isReplay() and hasattr(self, "writer"):
            self.writer.finish()
        hal.stopNotifier(self.notifier)
        hal.cleanNotifier(self.notifier)

    def startCompetition(self) -> None:
        """
        The main loop of the robot.
        Handles timing, logging, and calling the periodic functions.
        """
        self.robotInit()
        hal.observeUserProgramStarting()

        if self.isSimulation():
            self._simulationInit()

        self.initEnd = RobotController.getFPGATime()

        print("Robot startup complete!")

        while not self.isExited():
            if self.useTiming:
                currentTime = RobotController.getFPGATime()  # microseconds
                if self._nextCycleUs < currentTime:
                    # loop overrun, immediate next cycle
                    self._nextCycleUs = currentTime
                else:
                    hal.updateNotifierAlarm(self.notifier, int(self._nextCycleUs))
                    if hal.waitForNotifierAlarm(self.notifier) == 0:
                        break
                self._nextCycleUs += self._periodUs

            timestamp = RobotController.getFPGATime()
            log_table = LogTable(timestamp)
            Logger.init(log_table)

            if Logger.isReplay():
                Logger.replaySource.updateTable(log_table)

            Logger.processInputs("/IO", self.io)
            Logger.processInputs("/DS", self.ds_io)

            self._loopFunc()

            if not Logger.isReplay():
                self.writer.write(log_table)

    def robotPeriodic(self):
        """
        Called periodically during all modes.
        This is where the user can interact with the I/O objects.
        """
        # This is where the user would use the IO object
        if not Logger.isReplay():
            self.io.voltage = RobotController.getBatteryVoltage()
            self.ds_io.update()

        Logger.recordOutput("voltage", self.io.voltage)
