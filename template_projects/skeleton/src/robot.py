#!/usr/bin/env python3

import os
import constants
from pykit.wpilog.wpilogwriter import WPILOGWriter
from pykit.wpilog.wpilogreader import WPILOGReader
from pykit.networktables.nt4Publisher import NT4Publisher
from pykit.loggedrobot import LoggedRobot
from pykit.logger import Logger

import wpilib


class Robot(LoggedRobot):
    def __init__(self) -> None:
        super().__init__()
        Logger.recordMetadata("Robot", __class__.__name__)

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

    def robotPeriodic(self) -> None:
        pass

    def disabledInit(self) -> None:
        pass

    def disabledPeriodic(self) -> None:
        pass

    def autonomousInit(self) -> None:
        pass

    def autonomousPeriodic(self) -> None:
        pass

    def teleopInit(self) -> None:
        pass

    def teleopPeriodic(self) -> None:
        pass

    def testInit(self) -> None:
        pass

    def testPeriodic(self) -> None:
        pass

    def simulationInit(self) -> None:
        pass

    def simulationPeriodic(self) -> None:
        pass


if __name__ == "__main__":
    wpilib.run(Robot)
