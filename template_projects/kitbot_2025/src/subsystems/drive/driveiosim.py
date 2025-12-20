from wpilib.simulation import DifferentialDrivetrainSim
from wpimath.controller import PIDController
from subsystems.drive.driveio import DriveIO

from util.helpfulmath import clamp
from constants import kRobotPeriod

import driveconstants


class DriveIOSim(DriveIO):
    def __init__(self) -> None:
        self.sim = DifferentialDrivetrainSim.createKitbotSim(
            driveconstants.kGearbox,
            driveconstants.kMotorReduction,
            driveconstants.kWheelRadius,
        )

        self.leftAppliedVolts = 0.0
        self.rightAppliedVolts = 0.0
        self.closedLoop = False

        self.leftPID = PIDController(driveconstants.kSimKp, 0.0, driveconstants.kSimKd)
        self.rightPID = PIDController(driveconstants.kSimKp, 0.0, driveconstants.kSimKd)

        self.leftFFVolts = 0.0
        self.rightFFVolts = 0.0

    def updateInputs(self, inputs: DriveIO.DriveIOInputs) -> None:
        if self.closedLoop:
            self.leftAppliedVolts = (
                self.leftPID.calculate(
                    self.sim.getLeftVelocity() / driveconstants.kWheelRadius,
                )
                + self.leftFFVolts
            )
            self.rightAppliedVolts = (
                self.rightPID.calculate(
                    self.sim.getRightVelocity() / driveconstants.kWheelRadius,
                )
                + self.rightFFVolts
            )

        self.sim.setInputs(
            clamp(self.leftAppliedVolts, -12.0, 12.0),
            clamp(self.rightAppliedVolts, -12.0, 12.0),
        )
        self.sim.update(kRobotPeriod)

        inputs.leftPositionRad = (
            self.sim.getLeftPosition() / driveconstants.kWheelRadius
        )
        inputs.leftVelocityRadPerSec = (
            self.sim.getLeftVelocity() / driveconstants.kWheelRadius
        )
        inputs.leftAppliedVolts = self.leftAppliedVolts
        inputs.leftCurrentAmps = [self.sim.getLeftCurrentDraw()]

        inputs.rightPositionRad = (
            self.sim.getRightPosition() / driveconstants.kWheelRadius
        )
        inputs.rightVelocityRadPerSec = (
            self.sim.getRightVelocity() / driveconstants.kWheelRadius
        )
        inputs.rightAppliedVolts = self.rightAppliedVolts
        inputs.rightCurrentAmps = [self.sim.getRightCurrentDraw()]

    def setVoltage(self, leftVolts: float, rightVolts: float) -> None:
        self.closedLoop = False
        self.leftAppliedVolts = leftVolts
        self.rightAppliedVolts = rightVolts

    def setVelocity(
        self,
        leftRadPerSec: float,
        rightRadPerSec: float,
        leftFFVolts: float,
        rightFFVolts: float,
    ) -> None:
        self.closedLoop = True
        self.leftFFVolts = leftFFVolts
        self.rightFFVolts = rightFFVolts
        self.leftPID.setSetpoint(leftRadPerSec)
        self.rightPID.setSetpoint(rightRadPerSec)
