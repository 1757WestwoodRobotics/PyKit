import hal
from wpilib import (
    DSControlWord,
    IterativeRobotBase,
    RobotController,
    Watchdog,
)

from pykit.logger import Logger


class LoggedRobot(IterativeRobotBase):
    """
    A robot base class that provides logging and replay functionality.
    This class extends `IterativeRobotBase` and integrates with the `Logger`
    to automatically handle the logging of robot data and periodic loops.
    """

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

        self._periodUs = int(self.getPeriod() * 1000000)

        # Because in "robotpy test" this code starts at time 0
        # and hal.waitForNotifierAlarm returns (current_time_or_stopped, status)
        # with current_time_or_stopped assigned to 0 when hal.stopNotifier is called
        # or when the the current time is 0, and hal.stopNotifier is signal to
        # exit the infinite loop, the stop is prematurely detected at time 0.
        # Force the program to wait until self._periodUs for the first periodic loop
        # so that current_time_or_stopped will contain a non-zero current time and the
        # infinite loop does not end prematurely.
        self._nextCycleUs = 0 + self._periodUs

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
        This method replaces the standard `IterativeRobotBase.startCompetition`
        to inject logging and precise timing control.
        """
        self.robotInit()

        if self.isSimulation():
            self._simulationInit()

        self.initEnd = RobotController.getFPGATime()
        Logger.periodicAfterUser(self.initEnd, 0)
        print("Robot startup complete!")
        hal.observeUserProgramStarting()

        Logger.startReciever()

        while True:
            # Wait for next cycle using HAL notifier for precise timing
            if self.useTiming:
                currentTime = RobotController.getFPGATime()
                if self._nextCycleUs < currentTime:
                    # Loop overrun detected - skip waiting and run immediately
                    self._nextCycleUs = currentTime
                else:
                    hal.updateNotifierAlarm(self.notifier, int(self._nextCycleUs))

                    currentTimeOrStopped, status = hal.waitForNotifierAlarm(
                        self.notifier
                    )
                    if status != 0:
                        raise RuntimeError(
                            f"Error waiting for notifier alarm: status {status}"
                        )
                    if currentTimeOrStopped == 0:
                        break
                self._nextCycleUs += self._periodUs

            # Run logger pre-user code (load inputs from log or sensors)
            periodicBeforeStart = RobotController.getFPGATime()
            Logger.periodicBeforeUser()

            # Execute user periodic code and measure timing
            userCodeStart = RobotController.getFPGATime()
            self._loopFunc()
            userCodeEnd = RobotController.getFPGATime()

            # Run logger post-user code (save outputs to log)
            Logger.periodicAfterUser(
                userCodeEnd - userCodeStart, userCodeStart - periodicBeforeStart
            )
