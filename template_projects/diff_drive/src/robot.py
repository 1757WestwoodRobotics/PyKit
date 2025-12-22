#!/usr/bin/env python3

import os
from typing import Optional
import constants
from pykit.wpilog.wpilogwriter import WPILOGWriter
from pykit.wpilog.wpilogreader import WPILOGReader
from pykit.networktables.nt4Publisher import NT4Publisher
from pykit.loggedrobot import LoggedRobot
from pykit.logger import Logger


from commands2 import CommandScheduler, Command
import wpilib

from robotcontainer import RobotContainer


class DiffDrive(LoggedRobot):

    autonomousCommand: Optional[Command] = None

    def __init__(self) -> None:
        super().__init__()
        Logger.recordMetadata("Robot", "DiffDrive")

        match constants.kRobotMode:
            case constants.RobotModes.REAL:
                deploy_config = wpilib.deployinfo.getDeployData()
                if deploy_config is not None:
                    Logger.recordMetadata(
                        "Deploy Host", deploy_config.get("deploy-host", "")
                    )
                    Logger.recordMetadata(
                        "Deploy User", deploy_config.get("deploy-user", "")
                    )
                    Logger.recordMetadata(
                        "Deploy Date", deploy_config.get("deploy-date", "")
                    )
                    Logger.recordMetadata(
                        "Code Path", deploy_config.get("code-path", "")
                    )
                    Logger.recordMetadata("Git Hash", deploy_config.get("git-hash", ""))
                    Logger.recordMetadata(
                        "Git Branch", deploy_config.get("git-branch", "")
                    )
                    Logger.recordMetadata(
                        "Git Description", deploy_config.get("git-desc", "")
                    )
                Logger.addDataReciever(NT4Publisher(True))
                Logger.addDataReciever(WPILOGWriter())
            case constants.RobotModes.SIMULATION:
                Logger.addDataReciever(NT4Publisher(True))
            case constants.RobotModes.REPLAY:
                self.useTiming = False  # run as fast as possible
                log_path = os.environ["LOG_PATH"]
                log_path = os.path.abspath(log_path)
                print(f"Starting log from {log_path}")
                Logger.setReplaySource(WPILOGReader(log_path))
                Logger.addDataReciever(WPILOGWriter(log_path[:-7] + "_sim.wpilog"))

        Logger.start()

        self.robotContainer = RobotContainer()

    def robotPeriodic(self) -> None:
        # Runs the Scheduler. This is responsible for polling buttons, adding
        # newly-scheduled commands, running already-scheduled commands, removing
        # finished or interrupted commands, and running subsystem periodic() methods.
        # This must be called from the robot's periodic block in order for anything in
        # the Command-based framework to work.
        CommandScheduler.getInstance().run()

    def disabledInit(self) -> None:
        pass

    def disabledPeriodic(self) -> None:
        pass

    def autonomousInit(self) -> None:
        self.autonomousCommand = self.robotContainer.getAutonomousCommand()

        if self.autonomousCommand is not None:
            CommandScheduler.getInstance().schedule(self.autonomousCommand)

    def autonomousPeriodic(self) -> None:
        pass

    def teleopInit(self) -> None:
        if self.autonomousCommand is not None:
            self.autonomousCommand.cancel()

    def teleopPeriodic(self) -> None:
        pass

    def testInit(self) -> None:
        CommandScheduler.getInstance().cancelAll()

    def testPeriodic(self) -> None:
        pass

    def simulationInit(self) -> None:
        pass

    def simulationPeriodic(self) -> None:
        pass


if __name__ == "__main__":
    wpilib.run(DiffDrive)
