import os
from typing import Optional
from commands2 import Command, cmd
from commands2.sysid import SysIdRoutine
from commands2.button import CommandXboxController
from pykit.networktables.loggeddashboardchooser import LoggedDashboardChooser
from pathplannerlib.auto import AutoBuilder
from wpilib import getDeployDirectory

from commands.drivecommands import DriveCommands
from subsystems.drive.drive import Drive
from subsystems.drive.driveio import DriveIO
from subsystems.drive.driveiosim import DriveIOSim
from subsystems.drive.driveiotalonfx import DriveIOTalonFX

from subsystems.drive.gyroio import GyroIO
from subsystems.drive.gyroiopigeon2 import GyroIOPigeon2

import constants


class RobotContainer:
    def __init__(self) -> None:
        match constants.kRobotMode:
            case constants.RobotModes.REAL:
                self.drive = Drive(DriveIOTalonFX(), GyroIOPigeon2())
            case constants.RobotModes.SIMULATION:
                self.drive = Drive(DriveIOSim(), GyroIO())
            case constants.RobotModes.REPLAY:
                self.drive = Drive(DriveIO(), GyroIO())

        auto_folder_path = os.path.join(getDeployDirectory(), "pathplanner", "autos")
        auto_list = os.listdir(auto_folder_path)

        self.autoChooser: LoggedDashboardChooser[Command] = LoggedDashboardChooser(
            "Auto Choices"
        )
        for auto in auto_list:
            auto = auto.removesuffix(".auto")
            self.autoChooser.addOption(
                auto,
                AutoBuilder.buildAuto(auto),
            )
        self.autoChooser.setDefaultOption("Do Nothing", cmd.none())

        self.autoChooser.addOption(
            "Drive Simple FF Charactarization",
            DriveCommands.feedForwardCharacterization(self.drive),
        )
        self.autoChooser.addOption(
            "Drive SysId (Quasistatic Forward)",
            self.drive.sysIdQuasistatic(SysIdRoutine.Direction.kForward),
        )
        self.autoChooser.addOption(
            "Drive SysId (Quasistatic Reverse)",
            self.drive.sysIdQuasistatic(SysIdRoutine.Direction.kReverse),
        )
        self.autoChooser.addOption(
            "Drive SysId (Dynamic Forward)",
            self.drive.sysIdDynamic(SysIdRoutine.Direction.kForward),
        )
        self.autoChooser.addOption(
            "Drive SysId (Dynamic Reverse)",
            self.drive.sysIdDynamic(SysIdRoutine.Direction.kReverse),
        )

        self.controller = CommandXboxController(0)
        self.configureButtonBindings()

    def configureButtonBindings(self) -> None:
        self.drive.setDefaultCommand(
            DriveCommands.arcadeDrive(
                self.drive,
                lambda: -self.controller.getLeftY(),
                lambda: -self.controller.getRightX(),
            )
        )

    def getAutonomousCommand(self) -> Optional[Command]:
        return self.autoChooser.getSelected()
