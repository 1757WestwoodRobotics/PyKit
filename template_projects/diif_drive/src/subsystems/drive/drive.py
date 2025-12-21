from typing import Optional
from commands2 import Subsystem
from pathplannerlib.commands import (
    DriveFeedforwards,
    PPLTVController,
    PathPlannerLogging,
)
from pykit.autolog import autolog_output, autologgable_output
from pykit.logger import Logger
from wpilib import DriverStation
from commands2.sysid import SysIdRoutine
from wpimath.geometry import Pose2d, Rotation2d
from wpimath.kinematics import (
    ChassisSpeeds,
    DifferentialDriveKinematics,
    DifferentialDriveWheelSpeeds,
)
from wpimath.estimator import DifferentialDrivePoseEstimator

from pathplannerlib.auto import AutoBuilder

from subsystems.drive.driveio import DriveIO
from subsystems.drive.gyroio import GyroIO
from subsystems.drive import driveconstants

import constants
from util.helpfulmath import sign
from util.sysidlog import sysIdStateToStr


@autologgable_output
class Drive(Subsystem):
    def __init__(self, io: DriveIO, gyroIO: GyroIO) -> None:
        self.io = io
        self.gyroIO = gyroIO

        self.inputs = DriveIO.DriveIOInputs()
        self.gyroInputs = GyroIO.GyroIOInputs()

        self.kinematics = DifferentialDriveKinematics(driveconstants.kTrackWidth)

        self.kS = (
            driveconstants.kSimKs
            if constants.kRobotMode == constants.RobotModes.SIMULATION
            else driveconstants.kRealKs
        )
        self.kV = (
            driveconstants.kSimKv
            if constants.kRobotMode == constants.RobotModes.SIMULATION
            else driveconstants.kRealKv
        )

        self.poseEstimator = DifferentialDrivePoseEstimator(
            self.kinematics, Rotation2d(), 0.0, 0.0, Pose2d()
        )
        self.rawGyroRotation = Rotation2d()
        self.lastLeftPosition = 0.0
        self.lastRightPosition = 0.0

        AutoBuilder.configure(
            self.getPose,
            self.setPose,
            self.getChassisSpeeds,
            self.runClosedLoop,
            PPLTVController(
                constants.kRobotPeriod, driveconstants.kMaxSpeedMetersPerSecond
            ),
            driveconstants.kPPConfig,
            (lambda: DriverStation.getAlliance() == DriverStation.Alliance.kRed),
            self,
        )

        PathPlannerLogging.setLogActivePathCallback(
            lambda activePath: Logger.recordOutput("Odometry/Trajectory", activePath)
        )
        PathPlannerLogging.setLogTargetPoseCallback(
            lambda targetPose: Logger.recordOutput(
                "Odometry/TrajectorySetpoint", targetPose
            )
        )

        self.sysid = SysIdRoutine(
            SysIdRoutine.Config(
                1,
                7,
                10,
                lambda state: Logger.recordOutput(
                    "Drive/SysIdState", sysIdStateToStr(state)
                ),
            ),
            SysIdRoutine.Mechanism(
                (lambda volts: self.runOpenLoop(volts, volts)), (lambda: None), self
            ),
        )

    def periodic(self) -> None:
        self.io.updateInputs(self.inputs)
        self.gyroIO.updateInputs(self.gyroInputs)
        Logger.processInputs("Drive", self.inputs)
        Logger.processInputs("Drive/Gyro", self.gyroInputs)

        if self.gyroInputs.connected:
            self.rawGyroRotation = self.gyroInputs.yawPosition
        else:
            twist = self.kinematics.toTwist2d(
                self.getLeftPosition() - self.lastLeftPosition,
                self.getRightPosition() - self.lastRightPosition,
            )
            self.rawGyroRotation = self.rawGyroRotation + Rotation2d(twist.dtheta)

        self.lastLeftPosition = self.getLeftPosition()
        self.lastRightPosition = self.getRightPosition()

        self.poseEstimator.update(
            self.rawGyroRotation, self.getLeftPosition(), self.getRightPosition()
        )

    def runClosedLoop(
        self, speeds: ChassisSpeeds, _feedForwards: Optional[DriveFeedforwards] = None
    ):
        wheelSpeeds = self.kinematics.toWheelSpeeds(speeds)
        self.runClosedLoopParameters(wheelSpeeds.left, wheelSpeeds.right)

    def runClosedLoopParameters(self, leftSpeed: float, rightSpeed: float):
        leftRadPerS = leftSpeed / driveconstants.kWheelRadius
        rightRadPerS = rightSpeed / driveconstants.kWheelRadius

        Logger.recordOutput("Drive/LeftSetpoint", leftRadPerS)
        Logger.recordOutput("Drive/RightSetpoint", rightRadPerS)

        leftFF = self.kS * sign(leftRadPerS) + self.kV * leftRadPerS
        rightFF = self.kS * sign(rightRadPerS) + self.kV * rightRadPerS

        self.io.setVelocity(leftRadPerS, rightRadPerS, leftFF, rightFF)

    def runOpenLoop(self, leftV: float, rightV: float) -> None:
        self.io.setVoltage(leftV, rightV)

    def stop(self):
        self.runOpenLoop(0, 0)

    def sysIdQuasistatic(self, direction: SysIdRoutine.Direction):
        return self.sysid.quasistatic(direction)

    def sysIdDynamic(self, direction: SysIdRoutine.Direction):
        return self.sysid.dynamic(direction)

    @autolog_output(key="Odometry/Robot")
    def getPose(self) -> Pose2d:
        return self.poseEstimator.getEstimatedPosition()

    def getRotation(self) -> Rotation2d:
        return self.getPose().rotation()

    def setPose(self, pose: Pose2d) -> None:
        self.poseEstimator.resetPosition(
            self.rawGyroRotation, self.getLeftPosition(), self.getRightPosition(), pose
        )

    def addVisionMeasurement(self, visionPose: Pose2d, timestamp: float):
        self.poseEstimator.addVisionMeasurement(visionPose, timestamp)

    @autolog_output(key="Drive/LeftPosition")
    def getLeftPosition(self) -> float:
        return self.inputs.leftPositionRad * driveconstants.kWheelRadius

    @autolog_output(key="Drive/RightPosition")
    def getRightPosition(self) -> float:
        return self.inputs.rightPositionRad * driveconstants.kWheelRadius

    @autolog_output(key="Drive/LeftVelocity")
    def getLeftVelocity(self) -> float:
        return self.inputs.leftVelocityRadPerSec * driveconstants.kWheelRadius

    @autolog_output(key="Drive/RightVelocity")
    def getRightVelocity(self) -> float:
        return self.inputs.rightVelocityRadPerSec * driveconstants.kWheelRadius

    def getCharacterizationVelocity(self) -> float:
        return (
            self.inputs.leftVelocityRadPerSec + self.inputs.rightVelocityRadPerSec
        ) / 2.0

    def getChassisSpeeds(self) -> ChassisSpeeds:
        return self.kinematics.toChassisSpeeds(
            DifferentialDriveWheelSpeeds(
                driveconstants.kWheelRadius * self.getLeftVelocity(),
                driveconstants.kWheelRadius * self.getRightVelocity(),
            )
        )
