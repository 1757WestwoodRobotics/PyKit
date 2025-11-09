import hal
from wpilib import (
    DSControlWord,
    IterativeRobotBase,
    RobotController,
    Watchdog,
)

from pykit.logger import Logger


class LoggedRobot(IterativeRobotBase):
    """A robot base class that provides logging and replay functionality."""

    default_period = 0.02  # seconds

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
        self.word = DSControlWord()

    def endCompetition(self) -> None:
        """Called at the end of the competition to clean up resources."""
        hal.stopNotifier(self.notifier)
        hal.cleanNotifier(self.notifier)

    def startCompetition(self) -> None:
        """
        The main loop of the robot.
        Handles timing, logging, and calling the periodic functions.
        """
        self.robotInit()

        # TODO: handle autolog outputs

        if self.isSimulation():
            self._simulationInit()

        self.initEnd = RobotController.getFPGATime()
        Logger.periodicAfterUser(self.initEnd, 0)
        print("Robot startup complete!")
        hal.observeUserProgramStarting()

        Logger.startReciever()

        while True:
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

            periodicBeforeStart = RobotController.getFPGATime()
            Logger.periodicBeforeUser()

            userCodeStart = RobotController.getFPGATime()
            self._loopFunc()
            userCodeEnd = RobotController.getFPGATime()

            Logger.periodicAfterUser(
                userCodeEnd - userCodeStart, userCodeStart - periodicBeforeStart
            )
